"""Broker implementation for the User Service. Built on top of PyBroker.

October 16th, 2021"""


import logging
from uuid import uuid4
from pybroker import BrokerBase


log = logging.getLogger(__name__)
log.setLevel("DEBUG")


class Broker(BrokerBase):
    def __init__(self, config, query_handler) -> None:
        super().__init__(
            broker_username=config.BROKER_USERNAME,
            broker_password=config.BROKER_PASS,
            network_host_name=config.NETWORK_HOST_NAME,
            exchange_name=config.EXCHANGE_NAME,
            queue_name=config.QUEUE_NAME,
        )

        self._query_handler = query_handler

    async def start(self):
        """Start the broker. Will request and process a event replay when
        after initialized unless flag is_initialized is True."""

        await self.connect()

        # register handlers
        await self.add_message_handler(
            routing_key="query.accounts", callback=self._handle_query
        )

    async def _handle_query(self, message):
        """Primary handler for making Users service available to the
        rest of the application."""
        # Errors thrown above this layer in application code will be
        # caught in the context manager which invoked this method, and
        # the faulty message will be nacked.
        body = self.decode_message(message)
        response = self._query_handler(body)
        msg = self.create_message(body=response, correlation_id=message.correlation_id)
        await self.publish_one(message=msg, routing_key=message.reply_to)
