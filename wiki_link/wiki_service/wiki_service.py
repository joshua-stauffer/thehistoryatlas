from functools import partial
from logging import getLogger
from typing import Callable
from datetime import datetime, timezone

from wiki_service.config import WikiServiceConfig
from wiki_service.database import Database
from wiki_service.event_factories.event_factory import get_event_factories, EventFactory
from wiki_service.rest_client import RestClient, RestClientError
from wiki_service.utils import get_current_time
from wiki_service.wikidata_query_service import (
    WikiDataQueryService,
    WikiDataQueryServiceError,
    Entity,
)

log = getLogger(__name__)


class WikiServiceError(Exception): ...


class WikiService:
    def __init__(
        self,
        wikidata_query_service_factory: Callable[
            [], WikiDataQueryService
        ] = lambda: WikiDataQueryService(WikiServiceConfig()),
        config_factory: Callable[[], WikiServiceConfig] = lambda: WikiServiceConfig(),
        database_factory: Callable[[], Database] = Database.factory,
    ):
        self._config = config_factory()
        self._database = database_factory()
        self._wikidata_query_service = wikidata_query_service_factory()
        self._rest_client = RestClient(config=self._config)

    def search_for_people(self):
        """
        Query WikiData for all instances of Homo Sapien, and add each entry
        to the WikiQueue, if it doesn't yet exist in the system.
        """
        offset = self._database.get_last_person_offset()
        limit = self._config.WIKIDATA_SEARCH_LIMIT
        try:
            people = self._wikidata_query_service.find_people(
                limit=limit, offset=offset
            )
        except WikiDataQueryServiceError as e:
            log.warning(f"WikiData Query Service encountered error and failed: {e}")
            return
        people = [
            person
            for person in people
            if self._database.is_wiki_id_in_queue(wiki_id=person.qid) is False
            and self._database.wiki_id_exists(wiki_id=person.qid) is False
        ]
        self._database.add_items_to_queue(
            entity_type="PERSON", wiki_type="WIKIDATA", items=people
        )
        self._database.save_last_person_offset(offset=limit + offset)

    def build_events_from_person(self):
        item = self._database.get_oldest_item_from_queue()
        if item is None:
            log.info("WikiQueue is empty.")
            return
        log.info(f"Processing entity: {item}")
        report_errors = partial(
            self._database.report_queue_error,
            wiki_id=item.wiki_id,
            error_time=get_current_time(),
        )
        try:
            entity = self._wikidata_query_service.get_entity(id=item.wiki_id)
            if item.entity_type != "PERSON":
                report_errors(f"Unknown entity type field: {item.entity_type}")
                raise WikiServiceError(f"Unknown entity type: `{item.entity_type}`")
            event_factories = get_event_factories(
                entity=entity, query=self._wikidata_query_service
            )
            for event_factory in event_factories:
                self._create_wiki_event(event_factory)
            # Remove from queue after successful processing
            self._database.remove_item_from_queue(wiki_id=item.wiki_id)
        except WikiDataQueryServiceError as e:
            report_errors(f"WikiData query had an error: {e}")
            return
        except Exception as e:
            report_errors(f"Unknown error occurred: {e}")
            return

    def _create_wiki_event(self, event_factory: EventFactory) -> None:
        if not event_factory.entity_has_event():
            return

        try:
            event = event_factory.create_wiki_event()

            # Collect all WikiData IDs to check
            wikidata_ids = []
            for person_tag in event.people_tags:
                wikidata_ids.append(person_tag.wiki_id)
            wikidata_ids.append(event.place_tag.wiki_id)
            if event.time_tag.wiki_id:
                wikidata_ids.append(event.time_tag.wiki_id)

            # Check which tags already exist
            existing_tags = self._rest_client.get_tags(wikidata_ids=wikidata_ids)
            id_map = {
                tag["wikidata_id"]: tag["id"] for tag in existing_tags["wikidata_ids"]
            }

            # Create missing tags
            for person_tag in event.people_tags:
                if not id_map.get(person_tag.wiki_id):
                    result = self._rest_client.create_person(
                        name=person_tag.name,
                        wikidata_id=person_tag.wiki_id,
                        wikidata_url=f"https://www.wikidata.org/wiki/{person_tag.wiki_id}",
                    )
                    id_map[person_tag.wiki_id] = result["id"]

            if not id_map.get(event.place_tag.wiki_id):
                coords = event.place_tag.location.coordinates
                if coords:
                    result = self._rest_client.create_place(
                        name=event.place_tag.name,
                        wikidata_id=event.place_tag.wiki_id,
                        wikidata_url=f"https://www.wikidata.org/wiki/{event.place_tag.wiki_id}",
                        latitude=coords.latitude,
                        longitude=coords.longitude,
                    )
                    id_map[event.place_tag.wiki_id] = result["id"]

            if event.time_tag.wiki_id and not id_map.get(event.time_tag.wiki_id):
                result = self._rest_client.create_time(
                    name=event.time_tag.name,
                    wikidata_id=event.time_tag.wiki_id,
                    wikidata_url=f"https://www.wikidata.org/wiki/{event.time_tag.wiki_id}",
                    date=event.time_tag.time_definition.datetime,
                    calendar_model=event.time_tag.time_definition.calendar_model,
                    precision=event.time_tag.time_definition.precision,
                )
                id_map[event.time_tag.wiki_id] = result["id"]

            # Create event tags
            tags = []
            for person_tag in event.people_tags:
                tags.append(
                    {
                        "id": id_map[person_tag.wiki_id],
                        "name": person_tag.name,
                        "start_char": person_tag.start_char,
                        "stop_char": person_tag.stop_char,
                    }
                )

            tags.append(
                {
                    "id": id_map[event.place_tag.wiki_id],
                    "name": event.place_tag.name,
                    "start_char": event.place_tag.start_char,
                    "stop_char": event.place_tag.stop_char,
                }
            )

            if event.time_tag.wiki_id:
                time_id = id_map[event.time_tag.wiki_id]
            else:
                # Create time tag without WikiData ID
                result = self._rest_client.create_time(
                    name=event.time_tag.name,
                    wikidata_id=None,
                    wikidata_url=None,
                    date=event.time_tag.time_definition.datetime,
                    calendar_model=event.time_tag.time_definition.calendar_model,
                    precision=event.time_tag.time_definition.precision,
                )
                time_id = result["id"]

            tags.append(
                {
                    "id": time_id,
                    "name": event.time_tag.name,
                    "start_char": event.time_tag.start_char,
                    "stop_char": event.time_tag.stop_char,
                }
            )

            # Create the event
            citation = {
                "access_date": datetime.now(timezone.utc).isoformat(),
                "wikidata_item_id": event.people_tags[
                    0
                ].wiki_id,  # Use first person as main subject
                "wikidata_item_title": event.people_tags[0].name,
                "wikidata_item_url": f"https://www.wikidata.org/wiki/{event.people_tags[0].wiki_id}",
            }

            self._rest_client.create_event(
                summary=event.summary, tags=tags, citation=citation
            )

            # Record successful creation
            self._database.upsert_created_event(
                wiki_id=event.people_tags[0].wiki_id,
                factory_label=event_factory.label,
                factory_version=event_factory.version,
            )

        except (RestClientError, Exception) as e:
            # Record error
            self._database.upsert_created_event(
                wiki_id=event.people_tags[0].wiki_id,
                factory_label=event_factory.label,
                factory_version=event_factory.version,
                errors={"error": str(e)},
            )
