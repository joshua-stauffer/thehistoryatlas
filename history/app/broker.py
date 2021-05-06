"""Broker implementation for the History application of the History Atlas.
Built on top of PyBroker.

April 27th, 2021"""

import logging
from pybroker import BrokerBase
from .broker_errors import MissingReplyFieldError

log = logging.getLogger(__name__)
log.setLevel('DEBUG')

class Broker(BrokerBase):

    def __init__(self, config, request_handler) -> None:
        super().__init__(
            broker_username   = config.BROKER_USERNAME,
            broker_password   = config.BROKER_PASS,
            network_host_name = config.NETWORK_HOST_NAME,
            exchange_name     = config.EXCHANGE_NAME,
            queue_name        = config.QUEUE_NAME)

        # save main application callbacks
        self._request_handler = request_handler

    async def start(self):
        """Start the broker."""
        
        log.info('Getting broker connection')
        await self.connect(retry=True, retry_timeout=0.5)

        # register handlers
        await self.add_message_handler(
            routing_key='event.replay.request',
            callback=self._handle_request)

    # on message callbacks

    async def _handle_request(self, message):
        """Wrapper for receiving replay requests and forwarding them to 
        the main application for processing."""

        log.info(f'received replay request {message}')
        body = self.decode_message(message)
        reply_to = message.reply_to
        if not reply_to:
            raise MissingReplyFieldError
        publisher = self.get_publisher(routing_key=reply_to)
        async def send_func(body):
            message = self.create_message(body)
            await publisher(message)
        send_func.__doc__ = 'A utility method created on the fly for publishing' + \
                            f'to routing_key {reply_to}.'
        await self._request_handler(body, send_func)
