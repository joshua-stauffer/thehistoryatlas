"""Entry point for the WriteModel component.

Receives config variables from the environment via the Config module.
Integrates handler modules (command_handler and event_handler) and database
access via the Manager module.
Communicates with the rest of the History Atlas through the Broker module.
"""

import asyncio
import logging
from typing import Union


from abstract_domain_model.models.commands import (
    CommandSuccess,
    CommandFailed,
    CommandFailedPayload,
)
from abstract_domain_model.transform import to_dict, from_dict
from abstract_domain_model.types import Command
from tha_config import Config
from writemodel.api.api import GQLApi
from writemodel.broker import Broker
from writemodel.state_manager.handler_errors import (
    CitationExistsError,
    CitationMissingFieldsError,
)
from writemodel.state_manager.manager import Manager

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class WriteModel:
    """Primary class to serve the WriteModel. Starts database connection on
    instantiation, and is available to broker after calling
    WriteModel.start_broker()"""

    def __init__(self):
        self.config = Config()
        self.manager = Manager(self.config)
        self.broker = None  # created asynchronously in WriteModel.start_broker()
        self.api = GQLApi(
            command_handler=self.handle_command,
            auth_handler=lambda token: token,
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

    async def start_broker(self):
        """Initializes the message broker and starts listening for requests."""
        log.info("WriteModel: starting broker")
        self.broker = Broker(
            config=self.config,
            command_handler=self.handle_command,
            event_handler=self.handle_event,
            get_latest_event_id=self.manager.db.check_database_init,
        )
        last_event_id = self.manager.db.check_database_init()
        log.info(f"Last event id was {last_event_id}")

        try:
            await self.broker.start(is_initialized=False, replay_from=last_event_id)
        except Exception as e:
            log.critical(
                f"WriteModel caught unknown exception {e} and is "
                + "shutting down without restart."
            )
            await self.shutdown()

    async def shutdown(self, signal=None):
        """Gracefully close all open connections and cancel tasks"""
        if signal:
            log.info(f"Received shutdown signal: {signal}")
        await self.broker.cancel()
        loop = asyncio.get_event_loop()
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()
        log.info("Asyncio loop has been stopped")


# if __name__ == "__main__":
#     wm = WriteModel()
#     log.info("WriteModel initialized")
#     loop = asyncio.get_event_loop()
#     loop.create_task(wm.start_broker())
#     signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
#     for s in signals:
#         loop.add_signal_handler(s, lambda s=s: asyncio.create_task(wm.shutdown(s)))
#     try:
#         log.info("Asyncio loop now running")
#         loop.run_forever()
#     finally:
#         loop.close()
#         log.info("WriteModel shut down successfully.")
