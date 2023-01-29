from dataclasses import dataclass
from re import search
from typing import List, Dict, Optional, Set
from urllib.error import HTTPError

import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from wiki_service.config import WikiServiceConfig
from wiki_service.types import WikiDataItem


class WikiDataQueryServiceError(Exception):
    ...


@dataclass(frozen=True)
class Entity:
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


@dataclass(frozen=True)
class CoordinateLocation:
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


@dataclass(frozen=True)
class GeoshapeLocation:
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


@dataclass(frozen=True)
class TimeDefinition:
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


@dataclass(frozen=True)
class Property:
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
        return res.get["bindings"][0]["value"]

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
