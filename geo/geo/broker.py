"""Broker implementation for the NLP application of the History Atlas.
Built on top of PyBroker.

May 12th, 2021"""

import asyncio
import logging
from uuid import uuid4
from pybroker import BrokerBase
from geo.errors import MissingReplyFieldError


log = logging.getLogger(__name__)
log.setLevel('DEBUG')


class Broker(BrokerBase):

    def __init__(self,
    config,
    request_handler
    # event handlers from application here
    ) -> None:
        # call the superclass's init method with our config properties 
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
            routing_key='query.geo',                # public namespace for queries
            callback=self._handle_request)
    # on message callbacks

    async def _handle_request(self, message):
        """Wrapper for receiving replay requests and forwarding them to 
        the main application for processing."""

        log.info(f'received request for geo matching {message}')
        body = self.decode_message(message)
        reply_to = message.reply_to
        correlation_id = message.correlation_id
        if not reply_to and correlation_id:
            raise MissingReplyFieldError
        # send to main app for processing
        response = self._request_handler(body)
        msg = self.create_message(
                body=response,
                correlation_id=correlation_id)
        log.debug(f'Sending result to {reply_to}')
        await self.publish_one(
                message=msg,
                routing_key=reply_to)
