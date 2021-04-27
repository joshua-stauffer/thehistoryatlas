"""Broker implementation for the EventStore. Built on top of PyBroker.

April 27th, 2021"""

import logging
from pybroker import BrokerBase


log = logging.getLogger(__name__)
log.setLevel('DEBUG')

class Broker(BrokerBase):

    def __init__(self, config, event_handler) -> None:
        super().__init__(
            broker_username   = config.BROKER_USERNAME,
            broker_password   = config.BROKER_PASS,
            network_host_name = config.NETWORK_HOST_NAME,
            exchange_name     = config.EXCHANGE_NAME,
            queue_name        = config.QUEUE_NAME)

        # save main application callbacks
        self._event_handler = event_handler

    async def start(self):
        """Start the broker."""
        
        await self.connect()

        # register handlers
        await self.add_message_handler(
            routing_key='event.emitted',
            callback=self._handle_event)

        # get publish methods
        self._publish_persisted_event = self.get_publisher(
            routing_key='event.persisted')

    # on message callbacks

    async def _handle_event(self, message):
        """Wrapper for handling emitted events and forwarding them to the 
        persisted events, if successful."""

        log.info(f'processing incoming event {message}')
        body = self.decode_message(message)
        # any exceptions raised while processing will nack the incoming message
        persisted_event = self._event_handler(body)
        log.info(f'successfully processed the incoming event.')
        msg = self.create_message(persisted_event)
        await self._publish_persisted_event(msg)
