import logging
from datetime import datetime, timezone
from re import search
from urllib.error import HTTPError
import time
from functools import lru_cache

import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from wiki_service.config import WikiServiceConfig
from wiki_service.types import (
    CoordinateLocation,
    Entity,
    GeoLocation,
    GeoshapeLocation,
    Property,
    TimeDefinition,
    WikiDataItem,
    LocationResult,
)
from wiki_service.utils import get_version
from wiki_service.event_factories.q_numbers import (
    COORDINATE_LOCATION,
    LOCATION,
    COUNTRY,
    BOOK,
    POINT_IN_TIME,
)
from wiki_service.tracing import trace_time


MAX_RETRIES = 5

logger = logging.getLogger(__name__)


class WikiDataQueryServiceError(Exception): ...


def build_coordinate_location(geoclaim: dict) -> CoordinateLocation:
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
    geoclaim: dict, geoshape: dict, geoshape_url: str
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
        # Initialize cache functions with configured sizes
        self._get_entity_cached = lru_cache(maxsize=self._config.ENTITY_CACHE_SIZE)(
            self._get_entity_impl
        )
        self._get_label_cached = lru_cache(maxsize=self._config.LABEL_CACHE_SIZE)(
            self._get_label_impl
        )
        self._get_description_cached = lru_cache(
            maxsize=self._config.DESCRIPTION_CACHE_SIZE
        )(self._get_description_impl)

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

    @trace_time()
    def find_people(self, limit: int = 100, offset: int = 0) -> set[WikiDataItem]:
        """Find people from WikiData."""
        query = f"""
        SELECT DISTINCT ?item
        WHERE 
        {{
          ?item wdt:P31 wd:Q5 .
        }}
        LIMIT {limit} OFFSET {offset}
        """
        return self._sparql_query(query)

    @trace_time()
    def find_works_of_art(self, limit: int, offset: int) -> set[WikiDataItem]:
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

    @trace_time()
    def find_books(self, limit: int, offset: int) -> set[WikiDataItem]:
        INSTANCE_OF = "P31"
        query = f"""
        SELECT DISTINCT ?item WHERE {{
          {{
            SELECT DISTINCT ?item WHERE {{
              ?item p:{INSTANCE_OF} ?statement0.
              ?statement0 (ps:P31) wd:{BOOK}.
            }}
            LIMIT {limit} OFFSET {offset}
          }}
        }}
        """
        return self._sparql_query(query)

    @trace_time()
    def find_orations(self, limit: int = 100, offset: int = 0) -> set[WikiDataItem]:
        """Find orations from WikiData."""
        query = f"""
        SELECT DISTINCT ?item WHERE {{
          {{
            SELECT DISTINCT ?item WHERE {{
              ?item p:P31 ?statement0.
              ?statement0 (ps:P31) wd:Q861911.
            }}
            LIMIT {limit} OFFSET {offset}
          }}
        }}
        """
        return self._sparql_query(query)

    @trace_time()
    def _sparql_query(self, query: str) -> set[WikiDataItem]:
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

    @trace_time()
    def get_wikidata_people_count(self) -> int:

        query = """
        SELECT (COUNT(*) AS ?count)
        WHERE {
          ?item wdt:P31 wd:Q5 .
        }
        """
        res = self.make_sparql_query(query=query, url=self._config.WIKIDATA_SPARQL_URL)
        return int(res["results"]["bindings"][0]["count"]["value"])

    @trace_time()
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

    @trace_time()
    def get_wikidata_books_count(self) -> int:
        query = """
            SELECT ?count WHERE {
              {
             SELECT (COUNT(*) AS ?count)
             WHERE {
                  ?item p:P31 ?statement0.
                  ?statement0 (ps:P31) wd:Q7725634.
                }
              }
            }
        """
        res = self.make_sparql_query(query=query, url=self._config.WIKIDATA_SPARQL_URL)
        return int(res["results"]["bindings"][0]["count"]["value"])

    @trace_time()
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
        Uses caching to avoid repeated API calls for the same ID.
        """
        return self._get_entity_cached(id)

    @trace_time()
    def _get_entity_impl(self, id: str) -> Entity:
        """Implementation of get_entity without caching"""
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
        """
        Get an entity's label in the specified language.
        Uses caching to avoid repeated API calls for the same ID/language pair.
        """
        return self._get_label_cached(id, language)

    @trace_time()
    def _get_label_impl(self, id: str, language: str) -> str:
        """Implementation of get_label without caching"""
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

    def get_description(self, id: str, language: str) -> str | None:
        """
        Get an entity's description in the specified language.
        Uses caching to avoid repeated API calls for the same ID/language pair.

        Args:
            id: The Wikidata entity ID (e.g. Q1339)
            language: The language code (e.g. 'en')

        Returns:
            The description text if found, None if not found or on error
        """
        return self._get_description_cached(id, language)

    @trace_time()
    def _get_description_impl(self, id: str, language: str) -> str | None:
        """Implementation of get_description without caching"""
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

    @trace_time()
    def get_geo_location(self, id: str) -> GeoLocation:
        entity = self.get_entity(id)
        return self.get_hierarchical_location(entity=entity)

    @trace_time()
    def get_hierarchical_location(
        self, entity: Entity, properties: list[str] | None = None
    ) -> GeoLocation:
        """
        Get an entity's location by trying different location properties in order. By default:
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
        if not properties:
            properties = [LOCATION, COUNTRY]
        # Try coordinate location first
        coordinate = self.get_coordinate_location(entity)
        if coordinate is not None:
            return GeoLocation(coordinates=coordinate, geoshape=None)

        for prop in properties:
            prop_claim = entity.claims.get(prop, [])
            if prop_claim:
                location_id = prop_claim[0]["mainsnak"]["datavalue"]["value"]["id"]
                try:
                    prop_entity = self.get_entity(location_id)
                    location = self.get_hierarchical_location(
                        prop_entity, properties=[]
                    )
                    if location is not None:
                        return location
                except Exception as exc:
                    logger.info(f"Failed to get location from {location_id}: {exc}")
                    pass  # Continue to next method if location lookup fails

        return GeoLocation(coordinates=None, geoshape=None)

    @trace_time()
    def get_location_from_entity(
        self, entity: Entity, claim_props: list[str]
    ) -> LocationResult | None:
        # Try coordinate location first
        coordinate = self.get_coordinate_location(entity)
        if coordinate is not None:
            location_name = self.get_label(id=entity.id, language="en")
            return LocationResult(
                id=entity.id,
                name=location_name,
                geo_location=GeoLocation(coordinates=coordinate, geoshape=None),
            )

        for prop in claim_props:
            prop_claim = entity.claims.get(prop, [])
            if prop_claim:
                location_id = prop_claim[0]["mainsnak"]["datavalue"]["value"]["id"]
                try:
                    prop_entity = self.get_entity(location_id)
                    location = self.get_location_from_entity(
                        prop_entity, claim_props=claim_props
                    )
                    if location is not None:
                        return location
                except Exception as exc:
                    logger.info(f"Failed to get location from {location_id}: {exc}")
                    pass

        return None

    @trace_time()
    def get_location_from_claim(
        self, claim: dict, location_props: list[str]
    ) -> LocationResult | None:
        if "qualifiers" in claim:
            for prop in location_props:
                if prop in claim["qualifiers"]:
                    try:
                        # Special handling for coordinate location which has a different structure
                        if prop == COORDINATE_LOCATION:
                            coords = claim["qualifiers"][prop][0]["datavalue"]["value"]

                            # Get the event entity to use as location name
                            event_id = claim["mainsnak"]["datavalue"]["value"]["id"]
                            location_name = self.get_label(id=event_id, language="en")

                            geo_location = GeoLocation(
                                coordinates=CoordinateLocation(**coords),
                                geoshape=None,
                            )
                            return LocationResult(
                                name=location_name,
                                id=event_id,
                                geo_location=geo_location,
                            )
                        else:
                            location_id = claim["qualifiers"][prop][0]["datavalue"][
                                "value"
                            ]["id"]
                            geo_location = self._query.get_geo_location(id=location_id)
                            location_name = self._query.get_label(
                                id=location_id, language="en"
                            )
                            return LocationResult(
                                name=location_name,
                                id=event_id,
                                geo_location=geo_location,
                            )
                    except Exception as e:
                        logger.warning(
                            f"Could not get location for qualifier {prop}: {e}"
                        )
        return None

    @trace_time()
    def get_time_definition_from_entity(
        self, entity: Entity, claim: str, time_props: list[str]
    ) -> TimeDefinition | None:
        """
        Get a time definition by searching through a hierarchy of time properties within a claim.

        Args:
            entity: The entity to search within
            claim: The claim ID to search within (e.g. "P1344")
            time_props: List of time property IDs to search for in priority order (e.g. ["P585", "P580"])

        Returns:
            TimeDefinition if any time property is found, None otherwise
        """
        claim_values = entity.claims.get(claim, [])
        if not claim_values:
            return None
        for claim_value in claim_values:
            if time_definition := self.get_time_definition_from_claim(
                claim_value, time_props
            ):
                return time_definition
        return None

    @trace_time()
    def get_time_definition_from_claim(
        self, claim: dict, time_props: list[str]
    ) -> TimeDefinition | None:
        try:
            return self.build_time_definition(claim)
        except KeyError as exc:
            pass

        qualifiers = claim.get("qualifiers", {})
        for time_prop in time_props:
            if time_prop in qualifiers:
                time_qualifier = qualifiers[time_prop][0]  # Take first qualifier
                return self.build_time_definition(time_qualifier)

        # If no time found in qualifiers, try to get time from referenced entity
        mainsnak = claim.get("mainsnak", {})
        referenced_id = "MISSING"  # provide a clearer error message
        if mainsnak.get("datatype") == "wikibase-item":
            try:
                referenced_id = mainsnak["datavalue"]["value"]["id"]
                referenced_entity = self.get_entity(referenced_id)
                # Search for time properties in the referenced entity
                for time_prop in time_props:
                    if time_prop in referenced_entity.claims:
                        time_claim = referenced_entity.claims[time_prop][0]
                        return self.build_time_definition(time_claim)
            except Exception as exc:
                logger.info(f"Failed to get time from {referenced_id}: {exc}")
                return None

    @trace_time()
    def get_coordinate_location(self, entity: Entity) -> CoordinateLocation | None:
        """
        Get an entity's location properties or None.
        """
        geo_claim = entity.claims.get(COORDINATE_LOCATION, None)
        if geo_claim is None:
            return None
        coordinate_location = self.build_coordinate_location(geo_claim[0])
        return coordinate_location

    @trace_time()
    def get_geoshape_location(self, entity: Entity) -> GeoshapeLocation | None:
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

    @trace_time()
    def get_time(
        self, entity: Entity, time_prop: str = POINT_IN_TIME
    ) -> TimeDefinition | None:
        """
        Get an Entity's point in time property or None.
        """
        claims = entity.claims.get(time_prop)
        if len(claims) == 0:
            return None
        time_claim = claims[0]
        return self.build_time_definition(time_claim=time_claim)

    @staticmethod
    def build_entity(entity_dict: dict) -> Entity:
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
    def build_coordinate_location(geoclaim: dict) -> CoordinateLocation:
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
        geoclaim: dict, geoshape: dict, geoshape_url: str
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
    def build_time_definition(time_claim: dict) -> TimeDefinition:
        """Build a TimeDefinition from either a full claim or a qualifier."""
        # Check if this is a qualifier (has datavalue directly)
        if "datavalue" in time_claim:
            return TimeDefinition(
                id=time_claim.get("hash", ""),  # Use hash as ID for qualifiers
                type="statement",
                rank="normal",
                hash=time_claim["hash"],
                snaktype=time_claim["snaktype"],
                property=time_claim["property"],
                time=time_claim["datavalue"]["value"]["time"],
                timezone=time_claim["datavalue"]["value"]["timezone"],
                before=time_claim["datavalue"]["value"]["before"],
                after=time_claim["datavalue"]["value"]["after"],
                precision=time_claim["datavalue"]["value"]["precision"],
                calendarmodel=time_claim["datavalue"]["value"]["calendarmodel"],
            )
        # Otherwise it's a full claim
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
    def get_qid_from_uri(uri: str) -> str | None:
        # 'http://www.wikidata.org/entity/Q23'
        pattern = r"(Q\d+)"
        res = search(pattern=pattern, string=uri)
        if res is None:
            return None
        return res.group()
