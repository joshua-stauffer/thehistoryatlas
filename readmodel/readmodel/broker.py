"""Broker implementation for the ReadModel. Built on top of PyBroker.

May 6th, 2021"""

import asyncio
from collections import deque
import logging
from uuid import uuid4
from pybroker import BrokerBase


log = logging.getLogger(__name__)
log.setLevel("DEBUG")


class Broker(BrokerBase):
    def __init__(
        self, config, query_handler, event_handler, get_latest_event_id
    ) -> None:
        super().__init__(
            broker_username=config.BROKER_USERNAME,
            broker_password=config.BROKER_PASS,
            network_host_name=config.NETWORK_HOST_NAME,
            exchange_name=config.EXCHANGE_NAME,
            queue_name=config.QUEUE_NAME,
        )

        # do i want to try to catch up with queries after replay is over?
        self.is_history_replaying = False
        self._history_queue = deque()

        # save main application callbacks
        self._query_handler = query_handler
        self._event_handler = event_handler

        # history management
        self._get_latest_event_id = get_latest_event_id
        self._HISTORY_TIMEOUT = 1  # seconds we wait before remaking our replay
        # replay history request on no response.
        self._history_timeout_coro = None
        self._history_replay_corr_id = None

    async def start(self, is_initialized=False, replay_from=0):
        """Start the broker. Will request and process a event replay when
        after initialized unless flag is_initialized is True."""

        await self.connect()

        # register handlers
        await self.add_message_handler(
            routing_key="query.readmodel", callback=self._handle_query
        )
        await self.add_message_handler(
            routing_key="event.persisted", callback=self._handle_persisted_event
        )
        await self.add_message_handler(
            routing_key="event.replay.readmodel", callback=self._handle_replay_history
        )

        if not is_initialized:
            await self._request_history_replay(last_index=replay_from)

    async def _handle_query(self, message):
        """Primary handler for making ReadModel service available to the
        rest of the application."""
        # TODO: how to handle incoming queries while replaying history?
        # Errors thrown above this layer in application code will be
        # caught in the context manager which invoked this method, and
        # the faulty message will be nacked.
        body = self.decode_message(message)
        response = self._query_handler(body)
        msg = self.create_message(body=response, correlation_id=message.correlation_id)
        await self.publish_one(message=msg, routing_key=message.reply_to)

    async def _handle_persisted_event(self, message):
        """wrapper for handling persisted events"""
        body = self.decode_message(message)
        if self.is_history_replaying:
            # we'll process this message in order after completing the
            # history replay
            return self.__history_queue.append(body)
        self._event_handler(body)

    # history management

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
            reply_to="event.replay.readmodel",
            correlation_id=self._history_replay_corr_id,
        )

        await self.publish_one(msg, routing_key="event.replay.request")
        self._history_timeout_coro = asyncio.create_task(self._schedule_new_timeout())

    def _close_history_replay(self):
        """processes any new persisted events which came in while history was replaying,
        then closes out the replay and returns Broker to normal service."""

        log.debug("Ready to process events received while processing history replay")
        while len(self._history_queue):
            msg = self._history_queue.popleft()
            self._event_handler(msg)
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
