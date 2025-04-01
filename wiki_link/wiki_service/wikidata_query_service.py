import logging
from datetime import datetime, timezone
from re import search
from typing import Dict, Optional, Set
from urllib.error import HTTPError
import time

import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from wiki_service.config import WikiServiceConfig
from wiki_service.types import (
    CoordinateLocation,
    Entity,
    GeoLocation,
    GeoshapeLocation,
    Property,
    Query,
    TimeDefinition,
    WikiDataItem,
)
from wiki_service.utils import get_version
from wiki_service.event_factories.q_numbers import (
    COORDINATE_LOCATION,
    LOCATION,
    COUNTRY,
)


MAX_RETRIES = 5


class WikiDataQueryServiceError(Exception): ...


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


log = logging.getLogger(__name__)


class WikiDataQueryService:
    def __init__(self, config: WikiServiceConfig):
        self._config = config

    def _agent_identifier(self) -> str:
        return f"TheHistoryAtlas WikiLink/{get_version()} ({self._config.contact})"

    @staticmethod
    def _get_current_time():
        """Get current time in UTC. Separate method to make testing easier."""
        return datetime.now(timezone.utc)

    def _parse_retry_after(self, retry_after: str) -> float:
        """
        Parse the retry-after header which can be either:
        1. A number of seconds
        2. A HTTP date format (e.g. 'Wed, 21 Oct 2015 07:28:00 GMT')

        Returns the number of seconds to wait.
        """
        try:
            # First try parsing as a number of seconds
            return float(retry_after)
        except ValueError:
            try:
                # Try parsing as HTTP date format
                retry_date = datetime.strptime(
                    retry_after, "%a, %d %b %Y %H:%M:%S GMT"
                ).replace(tzinfo=timezone.utc)
                now = self._get_current_time()
                wait_seconds = (retry_date - now).total_seconds()
                return max(0, wait_seconds)  # Don't return negative values
            except ValueError:
                raise WikiDataQueryServiceError(
                    f"Invalid retry-after format: {retry_after}"
                )

    def _handle_rate_limit(self, response, retries: int = 0) -> bool:
        """Handle rate limiting by checking retry-after header and waiting if needed."""
        if response.status_code == 429:
            log.info("Rate limit reached. Retrying.")
            retry_after = response.headers.get("retry-after")
            if not retry_after:
                raise WikiDataQueryServiceError(
                    "Rate limit exceeded with no retry-after header"
                )
            if retries >= MAX_RETRIES:
                raise WikiDataQueryServiceError(
                    "Maximum retries exceeded for rate limited request"
                )

            wait_seconds = self._parse_retry_after(retry_after)
            time.sleep(wait_seconds)
            return True
        return False

    def find_people(self, limit: int, offset: int) -> Set[WikiDataItem]:

        query = f"""
        SELECT DISTINCT ?item
        WHERE 
        {{
          ?item wdt:P31 wd:Q5 .
        }}
        LIMIT {limit} OFFSET {offset}
        """
        return self._sparql_query(query)

    def find_works_of_art(self, limit: int, offset: int) -> Set[WikiDataItem]:
        INSTANCE_OF = "P31"
        WORK_OF_ART = "Q838948"
        query = f"""
        SELECT DISTINCT ?item WHERE {{
          {{
            SELECT DISTINCT ?item WHERE {{
              ?item p:{INSTANCE_OF} ?statement0.
              ?statement0 (ps:P31) wd:{WORK_OF_ART}.
            }}
            LIMIT {limit} OFFSET {offset}
          }}
        }}
        """
        return self._sparql_query(query)

    def _sparql_query(self, query: str) -> Set[WikiDataItem]:
        res = self.make_sparql_query(query=query, url=self._config.WIKIDATA_SPARQL_URL)
        items = res.get("results", {}).get("bindings", [])
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
        return int(res["results"]["bindings"][0]["count"]["value"])

    def get_wikidata_works_of_art_count(self) -> int:
        query = """
            SELECT ?count WHERE {
              {
             SELECT (COUNT(*) AS ?count)
             WHERE {
                  ?item p:P31 ?statement0.
                  ?statement0 (ps:P31) wd:Q838948.
                }
              }
            }
        """
        res = self.make_sparql_query(query=query, url=self._config.WIKIDATA_SPARQL_URL)
        return int(res["results"]["bindings"][0]["count"]["value"])

    def make_sparql_query(self, query: str, url: str) -> dict:
        """
        Make a SPARQL query to the specified URL.

        Args:
            query: The SPARQL query to execute
            url: The URL to query

        Returns:
            The query results as a dictionary
        """
        sparql = SPARQLWrapper(url, agent=self._agent_identifier())
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        retries = 0
        while True:
            try:
                result = sparql.query()
                return result.convert()
            except HTTPError as e:
                if hasattr(e, "response") and e.response.status_code == 429:
                    if self._handle_rate_limit(e.response, retries):
                        retries += 1
                        continue
                raise WikiDataQueryServiceError(f"SPARQL query failed: {e}")
            except Exception as e:
                raise WikiDataQueryServiceError(f"SPARQL query failed: {e}")

    def get_entity(self, id: str) -> Entity:
        """
        Query the WikiData REST API to retrieve an item by ID.
        """
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={id}&format=json"
        retries = 0
        while True:
            result = requests.get(url, headers={"User-Agent": self._agent_identifier()})
            if self._handle_rate_limit(result, retries):
                retries += 1
                continue

            json_result = result.json()
            error = json_result.get("error", None)
            if error is not None:
                raise WikiDataQueryServiceError(error)
            entity_dict = json_result["entities"][id]
            return self.build_entity(entity_dict)

    def get_label(self, id: str, language: str) -> str:
        url = f"https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/{id}/labels/{language}"
        retries = 0
        while True:
            result = requests.get(url, headers={"User-Agent": self._agent_identifier()})
            if self._handle_rate_limit(result, retries):
                retries += 1
                continue

            if not result.ok:
                raise WikiDataQueryServiceError(
                    f"Query label request failed with {result.status_code}: {result.json()}"
                )
            return result.text.strip('"').encode("utf-8").decode("unicode_escape")

    def get_description(self, id: str, language: str) -> Optional[str]:
        """Get an entity's description in the specified language.

        Args:
            id: The Wikidata entity ID (e.g. Q1339)
            language: The language code (e.g. 'en')

        Returns:
            The description text if found, None if not found or on error
        """
        url = f"https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/{id}/descriptions/{language}"
        retries = 0
        while True:
            result = requests.get(url, headers={"User-Agent": self._agent_identifier()})
            if self._handle_rate_limit(result, retries):
                retries += 1
                continue

            if not result.ok:
                if result.status_code == 404:
                    return None
                raise WikiDataQueryServiceError(
                    f"Query description request failed with {result.status_code}: {result.json()}"
                )
            return result.text.strip('"').encode("utf-8").decode("unicode_escape")

    def get_geo_location(self, id: str) -> GeoLocation:
        entity = self.get_entity(id)
        return self.get_hierarchical_location(entity=entity)

    def get_hierarchical_location(self, entity: Entity) -> Optional[GeoLocation]:
        """
        Get an entity's location by trying different location properties in order:
        1. Coordinate location (P625)
        2. Location (P276)
        3. Country (P17)

        For location and country properties, it will attempt to get the coordinates
        of the referenced entity.

        Args:
            entity: The entity to get location for

        Returns:
            GeoLocation if any location is found, None otherwise
        """
        # Try coordinate location first
        coordinate = self.get_coordinate_location(entity)
        if coordinate is not None:
            return GeoLocation(coordinates=coordinate, geoshape=None)

        # Try location property
        location_claims = entity.claims.get(LOCATION, [])
        if location_claims:
            location_id = location_claims[0]["mainsnak"]["datavalue"]["value"]["id"]
            try:
                location_entity = self.get_entity(location_id)
                location = self.get_hierarchical_location(location_entity)
                if location is not None:
                    return location
            except Exception:
                pass  # Continue to next method if location lookup fails

        # Try country property
        country_claims = entity.claims.get(COUNTRY, [])
        if country_claims:
            country_id = country_claims[0]["mainsnak"]["datavalue"]["value"]["id"]
            try:
                country_entity = self.get_entity(country_id)
                country = self.get_hierarchical_location(country_entity)
                if country is not None:
                    return country
            except Exception:
                pass  # Continue if country lookup fails

        return GeoLocation(coordinates=None, geoshape=None)

    def get_coordinate_location(self, entity: Entity) -> Optional[CoordinateLocation]:
        """
        Get an entity's location properties or None.
        """
        geo_claim = entity.claims.get(COORDINATE_LOCATION, None)
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
        pattern = r"(Q\d+)"
        res = search(pattern=pattern, string=uri)
        if res is None:
            return None
        return res.group()
