from logging import getLogger
from datetime import datetime, timezone

from wiki_service.config import WikiServiceConfig
from wiki_service.database import Database
from wiki_service.event_factories.event_factory import get_event_factories, EventFactory
from wiki_service.rest_client import RestClient, RestClientError
from wiki_service.utils import get_current_time
from wiki_service.wikidata_query_service import (
    WikiDataQueryService,
    WikiDataQueryServiceError,
)

log = getLogger(__name__)


class WikiServiceError(Exception): ...


class WikiService:
    def __init__(
        self,
        wikidata_query_service: WikiDataQueryService,
        database: Database,
        config: WikiServiceConfig,
        rest_client: RestClient | None = None,
    ):
        self._config = config
        self._database = database
        self._query = wikidata_query_service
        self._rest_client = rest_client or RestClient(config)

    def search_for_people(self, num_people: int | None = None):
        """
        Query WikiData for all instances of Homo Sapien, and add each entry
        to the WikiQueue, if it doesn't yet exist in the system.

        Args:
            num_people: Optional number of people to search for. If None, uses config limit.
        """
        offset = self._database.get_last_person_offset()
        limit = (
            min(num_people, self._config.WIKIDATA_SEARCH_LIMIT)
            if num_people
            else self._config.WIKIDATA_SEARCH_LIMIT
        )
        try:
            people = self._query.find_people(limit=limit, offset=offset)
        except WikiDataQueryServiceError as e:
            log.warning(f"WikiData Query Service encountered error and failed: {e}")
            return 0
        people = [
            person
            for person in people
            if self._database.is_wiki_id_in_queue(wiki_id=person.qid) is False
            and self._database.wiki_id_exists(wiki_id=person.qid) is False
        ]
        self._database.add_items_to_queue(entity_type="PERSON", items=people)
        self._database.save_last_person_offset(offset=limit + offset)
        return len(people)

    def run(self, num_people: int | None = None) -> None:
        """
        Run the WikiService pipeline to search for people and build events.

        Args:
            num_people: Optional number of people to process. If None, processes all available.
        """
        # First search for people
        people_added = self.search_for_people(num_people=num_people)
        if people_added == 0:
            log.info("No new people found to process")
            return

        # Process events until queue is empty or we've hit our limit
        processed = 0
        while True:
            if num_people and processed >= num_people:
                log.info(f"Reached processing limit of {num_people} people")
                break

            item = self._database.get_oldest_item_from_queue()
            if item is None:
                log.info("Queue is empty, processing complete")
                break

            try:
                self.build_events_from_person()
                self._database.remove_item_from_queue(wiki_id=item.wiki_id)
                processed += 1
            except Exception as e:
                log.error(f"Error processing person: {e}")
                continue

        log.info(f"Processed {processed} people successfully")

    def build_events_from_person(self):
        item = self._database.get_oldest_item_from_queue()
        if item is None:
            log.info("WikiQueue is empty.")
            return
        log.info(f"Processing entity: {item}")
        try:
            entity = self._query.get_entity(id=item.wiki_id)
            if item.entity_type != "PERSON":
                self._database.report_queue_error(
                    wiki_id=item.wiki_id,
                    error_time=get_current_time(),
                    errors=f"Unknown entity type field: {item.entity_type}",
                )
                return
            event_factories = get_event_factories(entity=entity, query=self._query)
            try:
                for event_factory in event_factories:
                    self._create_wiki_event(event_factory, item.wiki_id, entity.title)
                # Remove from queue only after all events are successfully created
                self._database.remove_item_from_queue(wiki_id=item.wiki_id)
            except RestClientError as e:
                self._database.report_queue_error(
                    wiki_id=item.wiki_id,
                    error_time=get_current_time(),
                    errors=f"REST client error: {e}",
                )
                return
        except WikiDataQueryServiceError as e:
            self._database.report_queue_error(
                wiki_id=item.wiki_id,
                error_time=get_current_time(),
                errors=f"WikiData query had an error: {e}",
            )
            return
        except Exception as e:
            self._database.report_queue_error(
                wiki_id=item.wiki_id,
                error_time=get_current_time(),
                errors=f"Unknown error occurred: {e}",
            )
            return

    def _create_wiki_event(
        self, event_factory: EventFactory, wiki_id: str, entity_title: str
    ) -> None:
        if not event_factory.entity_has_event():
            log.info(f"no event found for wiki_id: {wiki_id}")
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
                tag["wikidata_id"]: tag["id"]
                for tag in existing_tags.get("wikidata_ids", [])
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
                # todo: handle case of geoshape, no coords

            # Create time tag
            if event.time_tag.wiki_id:
                if not id_map.get(event.time_tag.wiki_id):
                    result = self._rest_client.create_time(
                        name=event.time_tag.name,
                        wikidata_id=event.time_tag.wiki_id,
                        wikidata_url=f"https://www.wikidata.org/wiki/{event.time_tag.wiki_id}",
                        date=event.time_tag.time_definition.time,
                        calendar_model=event.time_tag.time_definition.calendarmodel,
                        precision=event.time_tag.time_definition.precision,
                    )
                    time_id = result["id"]
                else:
                    time_id = id_map[event.time_tag.wiki_id]
            else:
                # Create time tag without WikiData ID
                result = self._rest_client.create_time(
                    name=event.time_tag.name,
                    wikidata_id=None,
                    wikidata_url=None,
                    date=event.time_tag.time_definition.time,
                    calendar_model=event.time_tag.time_definition.calendarmodel,
                    precision=event.time_tag.time_definition.precision,
                )
                time_id = result["id"]

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
                "wikidata_item_url": f"https://www.wikidata.org/wiki/{wiki_id}",
                "wikidata_item_title": entity_title,
                "wikidata_item_id": wiki_id,
            }

            self._rest_client.create_event(
                summary=event.summary,
                tags=tags,
                citation=citation,
            )

            # Record successful event creation
            self._database.upsert_created_event(
                wiki_id=wiki_id,
                factory_label=event_factory.label,
                factory_version=event_factory.version,
                errors=None,
            )

        except (RestClientError, Exception) as e:
            # Record error
            self._database.upsert_created_event(
                wiki_id=wiki_id,
                factory_label=event_factory.label,
                factory_version=event_factory.version,
                errors={"error": str(e)},
            )
            raise  # Re-raise the error to be handled by the caller
