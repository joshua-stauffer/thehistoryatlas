import logging
from typing import Union

from the_history_atlas.apps.accounts.accounts import Accounts
from the_history_atlas.apps.database.database_app import DatabaseClient
from the_history_atlas.apps.domain.models import PublishCitationPayload, PublishCitation
from the_history_atlas.apps.domain.models.accounts import GetUser, GetUserPayload
from the_history_atlas.apps.domain.models.commands import (
    CommandSuccess,
    CommandFailed,
    CommandFailedPayload,
)
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.domain.types import Event
from the_history_atlas.apps.eventstore import EventStore
from the_history_atlas.apps.writemodel.state_manager.command_handler import (
    CommandHandler,
)
from the_history_atlas.apps.writemodel.state_manager.database import Database
from the_history_atlas.apps.writemodel.state_manager.event_handler import EventHandler
from the_history_atlas.apps.writemodel.state_manager.handler_errors import (
    CitationExistsError,
    CitationMissingFieldsError,
    MissingResourceError,
)
from the_history_atlas.apps.writemodel.state_manager.text_processor import TextHasher

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class WriteModelApp:
    """Business logic for creating new Events."""

    def __init__(
        self,
        config: Config,
        database_client: DatabaseClient,
        events_app: EventStore,
        accounts_app: Accounts,
    ):
        self._config_app = config
        self._events_app = events_app
        self._accounts_app = accounts_app

        database = Database(database_client=database_client)
        hasher = TextHasher()
        self._event_handler = EventHandler(
            database_instance=database, hash_text=hasher.get_hash
        )
        self._command_handler = CommandHandler(
            database_instance=database, hash_text=hasher.get_hash
        )

        # subscribe to Event stream
        self._events_app.subscribe(callback=self.handle_event)

    def publish_citation(
        self, payload: PublishCitationPayload
    ) -> Union[CommandSuccess, CommandFailed]:
        """Wrapper for handling commands"""

        user = self._accounts_app.get_user(data=GetUserPayload(token=payload.token))
        command = PublishCitation(
            user_id=user.user_details.username,  # todo: pass through ID here
            app_version=self._config_app.get_app_version(),
            timestamp=self._config_app.get_timestamp(),
            payload=payload,
        )

        try:
            events = self._command_handler.publish_citation(command)
            log.debug(f"WriteModel is publishing to emitted.event: {events}")
            self._events_app.publish_events(events=events)
            return CommandSuccess(token=user.token)
        except CitationExistsError as e:
            return CommandFailed(
                payload=CommandFailedPayload(
                    reason=f"Citation with ID `{e.GUID}`already exists in database.",
                ),
                token=user.token,
            )
        except CitationMissingFieldsError as e:
            return CommandFailed(
                payload=CommandFailedPayload(
                    reason="Citation was missing fields.",
                ),
                token=user.token,
            )
        except MissingResourceError as e:
            return CommandFailed(
                payload=CommandFailedPayload(
                    reason="A resource referenced by ID in this query was not found.",
                ),
                token=user.token,
            )

    def handle_event(self, event: Event) -> None:
        self._event_handler.handle_event(event=event)
