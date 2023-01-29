import asyncio
from collections import deque
import logging
from typing import Callable, Dict
from uuid import uuid4

from abstract_domain_model.transform import from_dict, to_dict
from abstract_domain_model.types import Command
from pybroker import BrokerBase

log = logging.getLogger(__name__)
log.setLevel("DEBUG")


class Broker(BrokerBase):
    def __init__(
        self,
        config,
        event_handler: Callable[[Dict], None],
    ) -> None:
        super().__init__(
            broker_username=config.BROKER_USERNAME,
            broker_password=config.BROKER_PASS,
            network_host_name=config.NETWORK_HOST_NAME,
            exchange_name=config.EXCHANGE_NAME,
            queue_name=config.QUEUE_NAME,
        )

        # save main application callbacks
        self._event_handler = event_handler

    async def start(self):
        """Start the broker. Will request and process a event replay when
        after initialized unless flag is_initialized is True."""

        await self.connect()

        await self.add_message_handler(
            routing_key="event.persisted", callback=self._handle_persisted_event
        )

        # get publish methods
        self._publish_command = self.get_publisher(routing_key="command.emitted")

    # on message callbacks

    async def _handle_persisted_event(self, message):
        """wrapper for handling persisted events"""
        body = self.decode_message(message)
        self._event_handler(body)

    async def publish_command(self, command: Dict) -> None:
        """Publish a command."""
        msg = self.create_message(correlation_id=str(uuid4()), body=command)
        await self._publish_command(msg)
