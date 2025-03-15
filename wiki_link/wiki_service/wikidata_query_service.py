from datetime import datetime
from re import search
from typing import List, Dict, Optional, Set
from urllib.error import HTTPError

import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from pydantic import BaseModel

from wiki_service.config import WikiServiceConfig
from wiki_service.types import WikiDataItem


class WikiDataQueryServiceError(Exception): ...


class Entity(BaseModel):
    """Expected fields on a wikidata entity"""

    id: str
    pageid: int
    ns: int
    title: str
    lastrevid: int
    modified: str
    type: str
    labels: Dict[str, "Property"]
    descriptions: Dict[str, "Property"]
    aliases: Dict[str, List["Property"]]
    claims: Dict[str, List[Dict]]
    sitelinks: Dict[str, Dict]


class CoordinateLocation(BaseModel):
    id: str
    rank: str
    type: str
    snaktype: str
    property: str
    hash: str
    latitude: float
    longitude: float
    altitude: Optional[int]
    precision: Optional[float]
    globe: str


class GeoshapeLocation(BaseModel):
    id: str
    rank: str
    type: str
    snaktype: str
    property: str
    hash: str
    url: str
    zoom: int
    latitude: float
    longitude: float
    data: Dict


class GeoLocation(BaseModel):
    coordinates: CoordinateLocation | None
    geoshape: GeoshapeLocation | None


class TimeDefinition(BaseModel):
    id: str
    rank: str
    type: str
    snaktype: str
    property: str
    hash: str
    time: str
    timezone: int
    before: int
    after: int
    precision: int
    calendarmodel: str


def build_time_definition_from_claim(time_claim: Dict) -> TimeDefinition:
    return TimeDefinition(
        id=time_claim["id"],
        type=time_claim["type"],
        rank=time_claim["rank"],
        hash=time_claim["mainsnak"]["hash"],
        snaktype=time_claim["mainsnak"]["snaktype"],
        property=time_claim["mainsnak"]["property"],
        time=time_claim["mainsnak"]["datavalue"]["value"]["time"],
        timezone=time_claim["mainsnak"]["datavalue"]["value"]["timezone"],
        before=time_claim["mainsnak"]["datavalue"]["value"]["before"],
        after=time_claim["mainsnak"]["datavalue"]["value"]["after"],
        precision=time_claim["mainsnak"]["datavalue"]["value"]["precision"],
        calendarmodel=time_claim["mainsnak"]["datavalue"]["value"]["calendarmodel"],
    )


def build_coordinate_location(geoclaim: Dict) -> CoordinateLocation:
    """build CoordinateLocation from a P625 claim"""
    return CoordinateLocation(
        id=geoclaim["id"],
        type=geoclaim["type"],
        rank=geoclaim["rank"],
        hash=geoclaim["mainsnak"]["hash"],
        snaktype=geoclaim["mainsnak"]["snaktype"],
        property=geoclaim["mainsnak"]["property"],
        latitude=geoclaim["mainsnak"]["datavalue"]["value"]["latitude"],
        longitude=geoclaim["mainsnak"]["datavalue"]["value"]["longitude"],
        altitude=geoclaim["mainsnak"]["datavalue"]["value"]["altitude"],
        precision=geoclaim["mainsnak"]["datavalue"]["value"]["precision"],
        globe=geoclaim["mainsnak"]["datavalue"]["value"]["globe"],
    )


def build_geoshape_location(
    geoclaim: Dict, geoshape: Dict, geoshape_url: str
) -> GeoshapeLocation:
    return GeoshapeLocation(
        id=geoclaim["id"],
        type=geoclaim["type"],
        rank=geoclaim["rank"],
        hash=geoclaim["mainsnak"]["hash"],
        snaktype=geoclaim["mainsnak"]["snaktype"],
        property=geoclaim["mainsnak"]["property"],
        longitude=geoshape["longitude"],
        latitude=geoshape["latitude"],
        data=geoshape["data"],
        zoom=geoshape["zoom"],
        url=geoshape_url,
    )


def wikidata_time_to_text(time_def: TimeDefinition) -> str:
    """
    Convert a Wikidata time definition to a human-readable date string.

    Precision mapping:
      - 11: full date (day precision) → "December 31, 1980"
      - 10: month precision → "December 1980"
      - 9: year precision → "1980"
      - 8: decade precision → "1980s"
      - 7: century precision → "20th century"
    """
    # Remove leading '+' and any trailing parts (like the 'Z') not needed for parsing.
    raw_time = time_def.time
    if raw_time.startswith("+"):
        raw_time = raw_time[1:]

    # Parse only the date and time part (first 19 characters: "YYYY-MM-DDTHH:MM:SS")
    dt = datetime.strptime(raw_time[:19], "%Y-%m-%dT%H:%M:%S")

    if time_def.precision == 11:
        # Full date: e.g. "December 31, 1980"
        return dt.strftime("%B %d, %Y")
    elif time_def.precision == 10:
        # Month precision: e.g. "December 1980"
        return dt.strftime("%B %Y")
    elif time_def.precision == 9:
        # Year precision: e.g. "1980"
        return dt.strftime("%Y")
    elif time_def.precision == 8:
        # Decade precision: e.g. "1980s"
        decade = (dt.year // 10) * 10
        return f"{decade}s"
    elif time_def.precision == 7:
        # Century precision: e.g. "20th century"
        century = (dt.year - 1) // 100 + 1
        # Determine the ordinal suffix (handles 11-13 as well)
        if 10 <= century % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(century % 10, "th")
        return f"{century}{suffix} century"
    else:
        # Fallback: return ISO formatted date
        return dt.isoformat()


class Property(BaseModel):
    language: str
    value: str


class WikiDataQueryService:
    def __init__(self, config: WikiServiceConfig):
        self._config = config

    def find_people(self, limit: int, offset: int) -> Set[WikiDataItem]:

        query = f"""
        SELECT DISTINCT ?item
        WHERE 
        {{
          ?item wdt:P31 wd:Q5 .
        }}
        LIMIT {limit} OFFSET {offset}
        """
        res = self.make_sparql_query(query=query, url=self._config.WIKIDATA_SPARQL_URL)
        items = res.get("bindings", [])
        items = {
            WikiDataItem(
                url=item["item"]["value"],
                qid=self.get_qid_from_uri(item["item"]["value"]),
            )
            for item in items
        }
        return items

    def get_wikidata_people_count(self) -> int:

        query = """
        SELECT (COUNT(*) AS ?count)
        WHERE {
          ?item wdt:P31 wd:Q5 .
        }
        """
        res = self.make_sparql_query(query=query, url=self._config.WIKIDATA_SPARQL_URL)
        return int(res["bindings"][0]["count"]["value"])

    def make_sparql_query(self, query: str, url: str) -> Dict:
        sparql = SPARQLWrapper(url)
        sparql.setQuery(query=query)
        sparql.setReturnFormat(JSON)

        # Run the query
        try:
            result = sparql.query()
        except HTTPError as e:
            raise WikiDataQueryServiceError(e)
        converted_result = result.convert()

        results = converted_result["results"]
        return results

    def get_entity(self, id: str) -> Entity:
        """
        Query the WikiData REST API to retrieve an item by ID.
        """
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={id}&format=json"
        result = requests.get(url)
        json_result = result.json()
        error = json_result.get("error", None)
        if error is not None:
            raise WikiDataQueryServiceError(error)
        entity_dict = json_result["entities"][id]
        return self.build_entity(entity_dict)

    def get_label(self, id: str, language: str) -> str:
        url = f"https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/{id}/labels/{language}"
        result = requests.get(url)
        if not result.ok:
            raise WikiDataQueryServiceError(
                f"Query label request failed with {result.status_code}: {result.json()}"
            )
        return result.text.strip('"')

    def get_geo_location(self, id: str) -> GeoLocation:
        entity = self.get_entity(id)
        coordinate = self.get_coordinate_location(entity)
        geoshape = self.get_geoshape_location(entity)
        return GeoLocation(coordinates=coordinate, geoshape=geoshape)

    def get_coordinate_location(self, entity: Entity) -> Optional[CoordinateLocation]:
        """
        Get an entity's location properties or None.
        """
        geo_claim = entity.claims.get("P625", None)
        if geo_claim is None:
            return None
        coordinate_location = self.build_coordinate_location(geo_claim[0])
        return coordinate_location

    def get_geoshape_location(self, entity: Entity) -> Optional[GeoshapeLocation]:
        """
        Get an Entity's geoshape property or None.
        """
        claims = entity.claims.get("P3896", None)
        if claims is None:
            return None
        geoclaim = claims[0]
        geo_param = geoclaim["mainsnak"]["datavalue"]["value"]
        geoshape_url = f"http://commons.wikimedia.org/data/main/{geo_param}?origin=*"
        result = requests.get(geoshape_url)
        geoshape = result.json()
        return self.build_geoshape_location(
            geoclaim=geoclaim, geoshape=geoshape, geoshape_url=geoshape_url
        )

    def get_time(self, entity: Entity) -> Optional[TimeDefinition]:
        """
        Get an Entity's point in time property or None.
        """
        point_in_time_claim = "P585"
        claims = entity.claims.get(point_in_time_claim)
        if len(claims) == 0:
            return None
        time_claim = claims[0]
        return self.build_time_definition(time_claim=time_claim)

    @staticmethod
    def build_entity(entity_dict: Dict) -> Entity:
        return Entity(
            id=entity_dict["id"],
            pageid=entity_dict["pageid"],
            ns=entity_dict["ns"],
            title=entity_dict["title"],
            lastrevid=entity_dict["lastrevid"],
            modified=entity_dict["modified"],
            type=entity_dict["type"],
            labels={
                lang: Property(**prop) for lang, prop in entity_dict["labels"].items()
            },
            descriptions={
                lang: Property(**prop)
                for lang, prop in entity_dict["descriptions"].items()
            },
            aliases={
                key: [Property(**prop) for prop in val]
                for key, val in entity_dict["aliases"].items()
            },
            claims=entity_dict["claims"],
            sitelinks=entity_dict["sitelinks"],
        )

    @staticmethod
    def build_coordinate_location(geoclaim: Dict) -> CoordinateLocation:
        return CoordinateLocation(
            id=geoclaim["id"],
            type=geoclaim["type"],
            rank=geoclaim["rank"],
            hash=geoclaim["mainsnak"]["hash"],
            snaktype=geoclaim["mainsnak"]["snaktype"],
            property=geoclaim["mainsnak"]["property"],
            latitude=geoclaim["mainsnak"]["datavalue"]["value"]["latitude"],
            longitude=geoclaim["mainsnak"]["datavalue"]["value"]["longitude"],
            altitude=geoclaim["mainsnak"]["datavalue"]["value"]["altitude"],
            precision=geoclaim["mainsnak"]["datavalue"]["value"]["precision"],
            globe=geoclaim["mainsnak"]["datavalue"]["value"]["globe"],
        )

    @staticmethod
    def build_geoshape_location(
        geoclaim: Dict, geoshape: Dict, geoshape_url: str
    ) -> GeoshapeLocation:
        return GeoshapeLocation(
            id=geoclaim["id"],
            type=geoclaim["type"],
            rank=geoclaim["rank"],
            hash=geoclaim["mainsnak"]["hash"],
            snaktype=geoclaim["mainsnak"]["snaktype"],
            property=geoclaim["mainsnak"]["property"],
            longitude=geoshape["longitude"],
            latitude=geoshape["latitude"],
            data=geoshape["data"],
            zoom=geoshape["zoom"],
            url=geoshape_url,
        )

    @staticmethod
    def build_time_definition(time_claim: Dict) -> TimeDefinition:
        return TimeDefinition(
            id=time_claim["id"],
            type=time_claim["type"],
            rank=time_claim["rank"],
            hash=time_claim["mainsnak"]["hash"],
            snaktype=time_claim["mainsnak"]["snaktype"],
            property=time_claim["mainsnak"]["property"],
            time=time_claim["mainsnak"]["datavalue"]["value"]["time"],
            timezone=time_claim["mainsnak"]["datavalue"]["value"]["timezone"],
            before=time_claim["mainsnak"]["datavalue"]["value"]["before"],
            after=time_claim["mainsnak"]["datavalue"]["value"]["after"],
            precision=time_claim["mainsnak"]["datavalue"]["value"]["precision"],
            calendarmodel=time_claim["mainsnak"]["datavalue"]["value"]["calendarmodel"],
        )

    @staticmethod
    def get_qid_from_uri(uri: str) -> Optional[str]:
        # 'http://www.wikidata.org/entity/Q23'
        pattern = "(Q[1-9]+)"
        res = search(pattern=pattern, string=uri)
        if res is None:
            return None
        return res.group()
