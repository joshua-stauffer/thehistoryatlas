from logging import getLogger
from typing import Callable, Optional, List

from abstract_domain_model.models.commands.add_person import AddPerson, AddPersonPayload
from abstract_domain_model.models.commands.description import AddDescription
from abstract_domain_model.models.commands.name import AddName
from wiki_service.config import WikiServiceConfig
from wiki_service.database import Database, Item
from wiki_service.utils import get_current_time
from wiki_service.wikidata_query_service import (
    WikiDataQueryService,
    WikiDataQueryServiceError,
    Entity,
)
from writemodel.utils import get_app_version

log = getLogger(__name__)


class WikiServiceError(Exception):
    ...


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
            items = self._wikidata_query_service.find_people(limit=limit, offset=offset)
        except WikiDataQueryServiceError as e:
            log.warning(f"WikiData Query Service encountered error and failed: {e}")
            return
        items = [
            item
            for item in items
            if self._database.is_wiki_id_in_queue(wiki_id=item.qid) is False
            and self._database.wiki_id_exists(wiki_id=item.qid) is False
        ]
        self._database.add_items_to_queue(
            entity_type="PERSON", wiki_type="WIKIDATA", items=items
        )
        self._database.save_last_person_offset(offset=limit + offset)

    def build_entity(self):
        """
        Get a QID to be processed, resolve its properties from WikiData,
        and publish an event.
        """

        item = self._database.get_oldest_item_from_queue()
        entity = self._wikidata_query_service.get_entity(id=item.wiki_id)
        if item.entity_type == "PERSON":
            event = self._build_person(item=item, entity=entity)
        else:
            raise WikiServiceError(f"Unknown entity type: `{item.entity_type}`")

    def _build_person(self, item: Item, entity: Entity) -> Optional[AddPerson]:
        names = self._build_names_from_entity(entity)
        desc = self._build_descriptions_from_entity(entity)
        return AddPerson(
            user_id=self._config.USER_ID,
            timestamp=get_current_time(),
            app_version=get_app_version(),
            type="ADD_PERSON",
            payload=AddPersonPayload(
                names=names,
                desc=desc,
                wiki_data_id=item.wiki_id,
                wiki_link=item.wiki_link,
            ),
        )

    @staticmethod
    def _build_names_from_entity(entity: Entity) -> List[AddName]:
        return [
            *[
                AddName(name=prop.value, lang=prop.language, is_default=True)
                for prop in entity.labels.values()
            ],
            *[
                AddName(name=prop.value, lang=prop.language, is_default=False)
                for alias in entity.aliases.values()
                for prop in alias
            ],
        ]

    @staticmethod
    def _build_descriptions_from_entity(entity: Entity) -> List[AddDescription]:
        return [
            AddDescription(
                text=prop.value, lang=prop.language, source_updated_at=entity.modified
            )
            for prop in entity.descriptions.values()
        ]
