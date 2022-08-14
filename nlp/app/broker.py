"""Broker implementation for the NLP application of the History Atlas.
Built on top of PyBroker.

May 12th, 2021"""

import asyncio
import logging
from uuid import uuid4
from pybroker import BrokerBase
from app.broker_errors import MissingReplyFieldError

log = logging.getLogger(__name__)
log.setLevel("DEBUG")


class Broker(BrokerBase):
    def __init__(
        self,
        config,
        request_handler,
        response_handler,
        train_handler,
        event_handler,
        get_latest_event_id,
    ) -> None:
        # call the superclass's init method with our config properties
        super().__init__(
            broker_username=config.BROKER_USERNAME,
            broker_password=config.BROKER_PASS,
            network_host_name=config.NETWORK_HOST_NAME,
            exchange_name=config.EXCHANGE_NAME,
            queue_name=config.QUEUE_NAME,
        )
        # save main application callbacks
        self._request_handler = request_handler
        self._response_handler = response_handler
        self._train_handler = train_handler
        self._event_handler = event_handler
        # history management
        self._get_latest_event_id = get_latest_event_id
        self.is_history_replaying = False
        self._HISTORY_TIMEOUT = 1  # seconds we wait before remaking our replay
        # replay history request on no response.
        self._history_timeout_coro = None
        self._history_replay_corr_id = None

    async def start(self):
        """Start the broker."""

        log.info("Getting broker connection")
        await self.connect(retry=True, retry_timeout=0.5)

        # register handlers
        await self.add_message_handler(
            routing_key="query.nlp",  # public namespace for queries
            callback=self._handle_request,
        )

        await self.add_message_handler(
            routing_key="query.nlp.response",  # private namespace for sub queries
            callback=self._handle_query_response,
        )  # made while resolving a query request

        await self.add_message_handler(
            routing_key="signal.nlp.train",  # trigger a spaCy training session
            callback=self._handle_train_request,
        )

        await self.add_message_handler(
            routing_key="event.replay.nlp", callback=self._handle_replay_history
        )

        await self.add_message_handler(
            routing_key="event.persisted", callback=self._handle_persisted_event
        )

        # when event handling logic is in place, this will trigger
        # the history replay on start up:
        # await self._request_history_replay(last_index=0)

    # on message callbacks

    async def _handle_request(self, message):
        """Wrapper for receiving replay requests and forwarding them to
        the main application for processing."""

        log.info(f"received request for text processing {message}")
        body = self.decode_message(message)
        reply_to = message.reply_to
        correlation_id = message.correlation_id
        if not reply_to and correlation_id:
            raise MissingReplyFieldError

        async def request_response(result: dict):
            msg = self.create_message(body=result, correlation_id=correlation_id)
            log.debug(f"Sending result to {reply_to}")
            await self.publish_one(message=msg, routing_key=reply_to)

        log.info(f"Created new query for {reply_to} with id {correlation_id}")
        await self._request_handler(body, correlation_id, request_response)

    async def _handle_query_response(self, message):
        """Point of entry for responses to subqueries"""

        log.info(f"received query response {message}")
        body = self.decode_message(message)
        correlation_id = message.correlation_id
        if not correlation_id:
            raise MissingReplyFieldError
        await self._response_handler(body, correlation_id)

    async def _handle_train_request(self, message):
        """Listen for signals to retrain model."""

        log.info("Received request to retrain spaCy model.")
        self._train_handler()

    async def _handle_persisted_event(self, message):
        """wrapper for handling persisted events"""
        body = self.decode_message(message)
        if self.is_history_replaying:
            # ignore for now
            return
        self._event_handler(body)

    async def query_readmodel(self, query: dict, corr_id: str) -> None:
        """Publishes a query to the ReadModel service."""
        message = self.create_message(
            body=query, correlation_id=corr_id, reply_to="query.nlp.response"
        )
        await self.publish_one(message=message, routing_key="query.readmodel")

    async def query_geo(self, query: dict, corr_id: str) -> None:
        """Publishes a query to the Geo service."""
        message = self.create_message(
            body=query, correlation_id=corr_id, reply_to="query.nlp.response"
        )
        await self.publish_one(message=message, routing_key="query.geo")

    # history replay logic

    async def _request_history_replay(self, last_index=None):
        """Invokes a replay of the event store and directs the ensuing messages
        to the our replay history queue binding."""

        if last_index is None:
            # this means we're calling from Broker code (i.e. retrying after
            # a timeout), and we need to check the last received event
            last_index = self._get_latest_event_id()
        self._history_replay_corr_id = str(uuid4())

        log.info("Broker is requesting history replay")
        self.is_history_replaying = True
        msg_body = {
            "type": "REQUEST_HISTORY_REPLAY",
            "payload": {
                "last_event_id": last_index,
            },
        }
        msg = self.create_message(
            msg_body,
            reply_to="event.replay.nlp",
            correlation_id=self._history_replay_corr_id,
        )

        await self.publish_one(msg, routing_key="event.replay.request")
        self._history_timeout_coro = asyncio.create_task(self._schedule_new_timeout())

    async def _handle_replay_history(self, message):
        """wrapper for handling history replay"""
        if not self.is_history_replaying:
            return  # don't need to handle this message. maybe should raise exception?
        if message.correlation_id != self._history_replay_corr_id:
            return
        body = self.decode_message(message)
        if body.get("type") == "HISTORY_REPLAY_END":
            return self._close_history_replay()
        else:
            # cancel the last callback, if any
            if self._history_timeout_coro:
                self._history_timeout_coro.cancel()
            self._history_timeout_coro = asyncio.create_task(
                self._schedule_new_timeout()
            )
            return self._event_handler(body)

    def _close_history_replay(self):
        """Closes out the replay and returns Broker to normal service."""

        self.is_history_replaying = False
        self._cancel_history_timeout()
        log.info("Finished history replay")

    async def _schedule_new_timeout(self):
        """Schedule a new timeout coroutine."""

        await asyncio.sleep(self._HISTORY_TIMEOUT)
        # ignore any history messages that come in after this point
        # until we request a new replay.
        self.is_history_replaying = False
        asyncio.create_task(self._request_history_replay())

    def _cancel_history_timeout(self):
        """Cancel the history replay timeout and reset associated properties."""
        if self._history_timeout_coro:
            self._history_timeout_coro.cancel()
            self._history_timeout_coro = None
        self._history_replay_corr_id = None
