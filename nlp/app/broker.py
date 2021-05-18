"""Broker implementation for the NLP application of the History Atlas.
Built on top of PyBroker.

May 12th, 2021"""

import logging
from pybroker import BrokerBase
from app.broker_errors import MissingReplyFieldError

log = logging.getLogger(__name__)
log.setLevel('DEBUG')


class Broker(BrokerBase):

    def __init__(self, config, request_handler, response_handler) -> None:
        super().__init__(
            broker_username   = config.BROKER_USERNAME,
            broker_password   = config.BROKER_PASS,
            network_host_name = config.NETWORK_HOST_NAME,
            exchange_name     = config.EXCHANGE_NAME,
            queue_name        = config.QUEUE_NAME)
        # save main application callbacks
        self._request_handler = request_handler
        self._response_handler = response_handler

    async def start(self):
        """Start the broker."""
        
        log.info('Getting broker connection')
        await self.connect(retry=True, retry_timeout=0.5)

        # register handlers
        await self.add_message_handler(
            routing_key='query.nlp',                # public namespace for queries
            callback=self._handle_request)

        await self.add_message_handler(
            routing_key='query.nlp.response',       # private namespace for sub queries 
            callback=self._handle_query_response)   # made while resolving a query request

        # get publish methods
        self._publish_rm_query = self.get_publisher(
            routing_key='query.readmodel')
        self._publish_geo_query = self.get_publisher(
            routing_key='query.geo')

    # on message callbacks

    async def _handle_request(self, message):
        """Wrapper for receiving replay requests and forwarding them to 
        the main application for processing."""

        log.info(f'received request for text processing {message}')
        body = self.decode_message(message)
        reply_to = message.reply_to
        correlation_id = message.correlation_id
        if not reply_to and correlation_id:
            raise MissingReplyFieldError

        async def request_response(result: dict):
            msg = self.create_message(
                body=result,
                correlation_id=correlation_id)
            log.debug(f'Sending result to {reply_to}')
            await self.publish_one(
                message=msg,
                routing_key=reply_to)

        log.info(f'Created new query for {reply_to} with id {correlation_id}')
        await self._request_handler(body, correlation_id, request_response)

    async def _handle_query_response(self, message):
        """Point of entry for responses to subqueries"""

        log.info(f'received query response {message}')
        body = self.decode_message(message)
        correlation_id = message.correlation_id
        if not correlation_id:
            raise MissingReplyFieldError
        await self._response_handler(body, correlation_id)

    async def query_readmodel(self,
        query: dict,
        corr_id: str
        ) -> None:
        """Publishes a query to the ReadModel service."""
        await self.publish_one(
            body=query,
            correlation_id=corr_id,
            routing_key='query.readmodel',
            reply_to='query.nlp.response')

    async def query_geo(self,
        query: dict,
        corr_id: str
        ) -> None:
        """Publishes a query to the Geo service."""
        await self.publish_one(
            body=query,
            correlation_id=corr_id,
            routing_key='query.geo',
            reply_to='query.nlp.response')
