from functools import partial
from logging import getLogger
from typing import Callable, Optional, List, Dict

from abstract_domain_model.models.commands.add_person import AddPerson, AddPersonPayload
from abstract_domain_model.models.commands.description import AddDescription
from abstract_domain_model.models.commands.name import AddName
from abstract_domain_model.transform import from_dict, to_dict
from rpc_manager import RPCManager, RPCSuccess, RPCFailure
from wiki_service.broker import Broker
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


def broker_factory(
    config_factory: Callable[[], WikiServiceConfig],
    event_handler: Callable[[Dict], None],
) -> Broker:
    return Broker(config=config_factory(), event_handler=event_handler)


class WikiService:
    def __init__(
        self,
        broker_factory: broker_factory = broker_factory,
        wikidata_query_service_factory: Callable[
            [], WikiDataQueryService
        ] = lambda: WikiDataQueryService(WikiServiceConfig()),
        config_factory: Callable[[], WikiServiceConfig] = lambda: WikiServiceConfig(),
        database_factory: Callable[[], Database] = Database.factory,
        command_publisher: Callable[[int, Callable], RPCManager] = RPCManager,
    ):
        self._database = database_factory()
        self._wikidata_query_service = wikidata_query_service_factory()
        self._config = config_factory()
        self._broker: Broker = broker_factory(
            config_factory=config_factory, event_handler=self.handle_event
        )
        self._command_publisher = command_publisher(
            timeout=5, pub_function=self._broker.publish_command
        )

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

    async def build_entity(self):
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

        response = await self._command_publisher.make_call(to_dict(event))
        if isinstance(response, RPCSuccess):
            self._database.remove_item_from_queue(wiki_id=item.wiki_id)
            log.info(f"Successfully published command to add new entity.")
        elif isinstance(response, RPCFailure) and response.errors is not None:
            report_errors(f"Failed to publish command with errors: {response.errors}")
        else:
            report_errors("Timed out while waiting for WriteModel response.")

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

    def handle_event(self, message: Dict) -> None:
        ...

    async def init_services(self):
        """
        Start up any asynchronous services required by the application.
        """
        await self._broker.start()
