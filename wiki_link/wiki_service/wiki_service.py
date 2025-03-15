from functools import partial
from logging import getLogger
from typing import Callable

from wiki_service.config import WikiServiceConfig
from wiki_service.database import Database
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
        wikidata_query_service_factory: Callable[
            [], WikiDataQueryService
        ] = lambda: WikiDataQueryService(WikiServiceConfig()),
        config_factory: Callable[[], WikiServiceConfig] = lambda: WikiServiceConfig(),
        database_factory: Callable[[], Database] = Database.factory,
    ):
        self._database = database_factory()
        self._wikidata_query_service = wikidata_query_service_factory()
        self._config = config_factory()

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

    def build_entity(self):
        """
        Get a QID to be processed, resolve its properties from WikiData,
        and publish an event.
        """
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
            if item.entity_type == "PERSON":
                event = self._build_person(item=item, entity=entity)
            else:
                report_errors(f"Unknown entity type field: {item.entity_type}")
                raise WikiServiceError(f"Unknown entity type: `{item.entity_type}`")
        except WikiDataQueryServiceError as e:
            report_errors(f"WikiData query had an error: {e}")
            return
        except Exception as e:
            report_errors(f"Unknown error occurred: {e}")
            return
