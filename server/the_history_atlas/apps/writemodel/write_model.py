import asyncio
import logging
from typing import Union, Dict

from the_history_atlas.apps.domain.models.accounts import GetUser, GetUserPayload
from the_history_atlas.apps.domain.models.accounts.get_user import GetUserResponse
from the_history_atlas.apps.domain.models.commands import (
    CommandSuccess,
    CommandFailed,
    CommandFailedPayload,
)
from the_history_atlas.apps.domain.transform import to_dict, from_dict
from the_history_atlas.apps.domain.models.commands import Command
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.writemodel.api.api import GQLApi
from the_history_atlas.apps.writemodel.state_manager.handler_errors import (
    CitationExistsError,
    CitationMissingFieldsError,
)
from the_history_atlas.apps.writemodel.state_manager.manager import Manager

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class WriteModelApp:
    def __init__(self):
        self.config = Config()
        self.manager = Manager(self.config)
        self.api = GQLApi(
            command_handler=self.handle_command,
            auth_handler=self.get_authorization,
        )

    async def handle_command(
        self, message: Command
    ) -> Union[CommandSuccess, CommandFailed]:
        """Wrapper for handling commands"""

        try:
            events = self.manager.command_handler.handle_command(message)
            msg = self.broker.create_message([to_dict(e) for e in events])
            log.debug(f"WriteModel is publishing to emitted.event: {events}")
            await self.broker._publish_emitted_event(msg)
            return CommandSuccess()
        except CitationExistsError as e:
            log.info(
                f"Broker caught error from a duplicate event. "
                + "If sender included a reply_to value they will receive a "
                + "message now."
            )
            return CommandFailed(
                payload=CommandFailedPayload(
                    reason=f"Citation with ID `{e.GUID}`already exists in database.",
                ),
            )
        except CitationMissingFieldsError as e:
            log.info(
                f"Broker caught an error from a citation missing fields. "
                + "If sender included a reply_to value they will receive a "
                + "message now."
            )
            log.info(e)
            return CommandFailed(
                payload=CommandFailedPayload(
                    reason="Citation was missing fields.",
                ),
            )

    def handle_event(self, event: dict) -> None:
        event = from_dict(event)
        self.manager.event_handler.handle_event(event=event)

    async def get_authorization(self, token: str) -> str:
        """
        Query the Accounts service to verify token.
        """
        auth_request = GetUser(type="GET_USER", payload=GetUserPayload(token=token))
        response = None  # todo
        get_user_response: GetUserResponse = from_dict(response.message)
        return get_user_response.payload.token
