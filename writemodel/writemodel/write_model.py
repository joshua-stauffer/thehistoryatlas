"""Entry point for the WriteModel component.

Receives config variables from the environment via the Config module.
Integrates handler modules (command_handler and event_handler) and database
access via the Manager module.
Communicates with the rest of the History Atlas through the Broker module.
"""

import asyncio
import os
import json
import logging
import signal
from tha_config import Config
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
        self.handle_command = self.manager.command_handler.handle_command
        self.handle_event = self.manager.event_handler.handle_event
        self.broker = None  # created asynchronously in WriteModel.start_broker()

    async def handle_command(self, message):
        """Wrapper for handling commands"""
        body = self.broker.decode_message(message)
        # Now pass message body to main application for processing.
        # if the processing fails this line with raise an exception
        # and the context manager which called this method will
        # nack the message
        try:
            event = self.manager.event_handler.handle_event(body)
            msg = self.broker.create_message(event, headers=message.headers)
            log.debug(f"WriteModel is publishing to emitted.event: {event}")
            await self.broker._publish_emitted_event(msg)
            # check if the publisher wants to hear a reply
            if message.reply_to:
                body = self.broker.create_message(
                    {"type": "COMMAND_SUCCESS"},
                    correlation_id=message.correlation_id,
                    headers=message.headers,
                )
                await self.broker.publish_one(body, message.reply_to)
        except CitationExistsError as e:
            log.info(
                f"Broker caught error from a duplicate event. "
                + "If sender included a reply_to value they will receive a "
                + "message now."
            )
            if message.reply_to:
                body = self.broker.create_message(
                    {
                        "type": "COMMAND_FAILED",
                        "payload": {
                            "reason": "Citation already exists in database.",
                            "existing_event_guid": e.GUID,
                        },
                    },
                    correlation_id=message.correlation_id,
                    headers=message.headers,
                )
                await self.broker.publish_one(body, message.reply_to)
        except CitationMissingFieldsError as e:
            log.info(
                f"Broker caught an error from a citation missing fields. "
                + "If sender included a reply_to value they will receive a "
                + "message now."
            )
            log.info(e)
            if message.reply_to:
                body = self.broker.create_message(
                    {
                        "type": "COMMAND_FAILED",
                        "payload": {
                            "reason": "Citation was missing fields (text, GUID, tags, or meta)."
                        },
                    },
                    correlation_id=message.correlation_id,
                    headers=message.headers,
                )
                await self.broker.publish_one(body, message.reply_to)

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


if __name__ == "__main__":
    wm = WriteModel()
    log.info("WriteModel initialized")
    loop = asyncio.get_event_loop()
    loop.create_task(wm.start_broker())
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(wm.shutdown(s)))
    try:
        log.info("Asyncio loop now running")
        loop.run_forever()
    finally:
        loop.close()
        log.info("WriteModel shut down successfully.")
