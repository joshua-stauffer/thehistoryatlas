from logging import getLogger
from datetime import datetime, timezone

from wiki_service.config import WikiServiceConfig
from wiki_service.database import Database, Item
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

    def search_for_works_of_art(self, num_works: int | None = None):
        """
        Query WikiData for all instances of works of art, and add each entry
        to the WikiQueue, if it doesn't yet exist in the system.

        Args:
            num_works: Optional number of works to search for. If None, uses config limit.
        """
        offset = self._database.get_last_works_of_art_offset()
        limit = (
            min(num_works, self._config.WIKIDATA_SEARCH_LIMIT)
            if num_works
            else self._config.WIKIDATA_SEARCH_LIMIT
        )
        try:
            works = self._query.find_works_of_art(limit=limit, offset=offset)
            log.info(f"Found works: {works}")
            if not works:
                log.info("No works of art found")
                return 0
        except WikiDataQueryServiceError as e:
            log.warning(f"WikiData Query Service encountered error and failed: {e}")
            return 0

        # Convert set to list for filtering
        works_list = list(works)
        log.info(f"Works list: {works_list}")
        filtered_works = [
            work
            for work in works_list
            if not self._database.is_wiki_id_in_queue(wiki_id=work.qid)
            and not self._database.wiki_id_exists(wiki_id=work.qid)
        ]
        log.info(f"Filtered works: {filtered_works}")

        if filtered_works:
            self._database.add_items_to_queue(entity_type="WORK_OF_ART", items=filtered_works)
            self._database.save_last_works_of_art_offset(offset=limit + offset)
            return len(filtered_works)
        
        log.info("No new works of art to add to queue")
        return 0

    def run(self, num_people: int | None = None, num_works: int | None = None) -> None:
        """
        Run the WikiService pipeline to search for people and works of art, and build events.

        Args:
            num_people: Optional number of people to process. If None, processes all available.
            num_works: Optional number of works of art to process. If None, processes none.
        """
        # First search for people
        people_added = self.search_for_people(num_people=num_people)
        if people_added == 0:
            log.info("No new people found to process")

        # Then search for works of art if requested
        works_added = 0
        if num_works is not None:
            works_added = self.search_for_works_of_art(num_works=num_works)
            if works_added == 0:
                log.info("No new works of art found to process")

        if people_added == 0 and works_added == 0:
            return

        # Process events until queue is empty or we've hit our limit
        processed = 0
        while True:
            if num_people and processed >= num_people + works_added:
                log.info(f"Reached processing limit of {num_people + works_added} items")
                break

            item = self._database.get_oldest_item_from_queue()
            if item is None:
                log.info("Queue is empty, processing complete")
                break

            try:
                self.build_events(item=item)
                self._database.remove_item_from_queue(wiki_id=item.wiki_id)
                processed += 1
            except Exception as e:
                log.error(f"Error processing item: {e}")
                continue

        log.info(f"Processed {processed} items successfully")

    def build_events(self, item: Item) -> None:
        log.info(f"Processing entity: {item}")
        try:
            if item.entity_type not in ["PERSON", "WORK_OF_ART"]:
                self._database.report_queue_error(
                    wiki_id=item.wiki_id,
                    error_time=get_current_time(),
                    errors=f"Unknown entity type field: {item.entity_type}",
                )
                return

            entity = self._query.get_entity(id=item.wiki_id)
            event_factories = get_event_factories(entity=entity, query=self._query, entity_type=item.entity_type)
            english_label = entity.labels.get("en")
            if english_label:
                label = english_label.value
            else:
                label = f"Unknown label ({entity.title})"

            try:
                for event_factory in event_factories:
                    self._create_wiki_event(event_factory, item.wiki_id, label)
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
            log.info(f"{event_factory.label} has no event for wiki_id: {wiki_id}")
            return
        elif self._database.event_exists(
            wiki_id=wiki_id,
            factory_label=event_factory.label,
            factory_version=event_factory.version,
        ):
            log.info(
                f"{event_factory.label} event already processed for wiki_id: {wiki_id}"
            )
            return

        try:
            events = event_factory.create_wiki_event()

            # Create a citation that will be used for all events
            citation = {
                "access_date": datetime.now(timezone.utc).isoformat(),
                "wikidata_item_url": f"https://www.wikidata.org/wiki/{wiki_id}",
                "wikidata_item_title": entity_title,
                "wikidata_item_id": wiki_id,
            }

            # Process each event
            for event in events:
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
                        if person_tag.wiki_id:
                            description = self._query.get_description(
                                id=person_tag.wiki_id, language="en"
                            )
                        else:
                            description = None
                        result = self._rest_client.create_person(
                            name=person_tag.name,
                            wikidata_id=person_tag.wiki_id,
                            wikidata_url=f"https://www.wikidata.org/wiki/{person_tag.wiki_id}",
                            description=description,
                        )
                        id_map[person_tag.wiki_id] = result["id"]

                if not id_map.get(event.place_tag.wiki_id):
                    coords = event.place_tag.location.coordinates
                    if coords:
                        if event.place_tag.wiki_id:
                            description = self._query.get_description(
                                id=event.place_tag.wiki_id, language="en"
                            )
                        else:
                            description = None
                        result = self._rest_client.create_place(
                            name=event.place_tag.name,
                            wikidata_id=event.place_tag.wiki_id,
                            wikidata_url=f"https://www.wikidata.org/wiki/{event.place_tag.wiki_id}",
                            latitude=coords.latitude,
                            longitude=coords.longitude,
                            description=description,
                        )
                        id_map[event.place_tag.wiki_id] = result["id"]
                    # todo: handle case of geoshape, no coords

                # Create time tag
                if event.time_tag.wiki_id:
                    if not id_map.get(event.time_tag.wiki_id):
                        description = self._query.get_description(
                            id=event.time_tag.wiki_id, language="en"
                        )
                        result = self._rest_client.create_time(
                            name=event.time_tag.name,
                            wikidata_id=event.time_tag.wiki_id,
                            wikidata_url=f"https://www.wikidata.org/wiki/{event.time_tag.wiki_id}",
                            date=event.time_tag.time_definition.time,
                            calendar_model=event.time_tag.time_definition.calendarmodel,
                            precision=event.time_tag.time_definition.precision,
                            description=description,
                        )
                        time_id = result["id"]
                    else:
                        time_id = id_map[event.time_tag.wiki_id]
                else:
                    # Check if the time already exists
                    time_exists = self._rest_client.check_time_exists(
                        datetime=event.time_tag.time_definition.time,
                        calendar_model=event.time_tag.time_definition.calendarmodel,
                        precision=event.time_tag.time_definition.precision,
                    )
                    if time_exists:
                        time_id = str(time_exists)
                    else:
                        # Create time tag without WikiData ID
                        result = self._rest_client.create_time(
                            name=event.time_tag.name,
                            wikidata_id=None,
                            wikidata_url=None,
                            date=event.time_tag.time_definition.time,
                            calendar_model=event.time_tag.time_definition.calendarmodel,
                            precision=event.time_tag.time_definition.precision,
                            description=None,
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
                self._rest_client.create_event(
                    summary=event.summary,
                    tags=tags,
                    citation=citation,
                )

            # Record successful event creation after all events are created
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
