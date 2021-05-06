"""Broker implementation for the ReadModel. Built on top of PyBroker.

May 6th, 2021"""


from collections import deque
import logging
from pybroker import BrokerBase
from broker_errors import MessageError


log = logging.getLogger(__name__)
log.setLevel('DEBUG')

class Broker(BrokerBase):

    def __init__(self, config, query_handler, event_handler) -> None:
        super().__init__(
            broker_username   = config.BROKER_USERNAME,
            broker_password   = config.BROKER_PASS,
            network_host_name = config.NETWORK_HOST_NAME,
            exchange_name     = config.EXCHANGE_NAME,
            queue_name        = config.QUEUE_NAME)
            
        # do i want to try to catch up with queries after replay is over?
        self.is_history_replaying = False
        self._history_queue = deque()

        # save main application callbacks
        self._command_handler = query_handler
        self._event_handler = event_handler

    async def start(self, is_initialized=False, replay_from=0):
        """Start the broker. Will request and process a event replay when
        after initialized unless flag is_initialized is True."""
        
        await self.connect()
        if not is_initialized:
            await self._request_history_replay(last_index=replay_from)

        # register handlers
        await self.add_message_handler(
            routing_key='query.readmodel',
            callback=self._handle_query)
        await self.add_message_handler(
            routing_key='event.persisted',
            callback=self._handle_persisted_event)
        await self.add_message_handler(
            routing_key='event.replay.readmodel',
            callback=self._handle_replay_history)

    async def _handle_query(self, message):
        """Primary handler for making ReadModel service available to the
        rest of the application."""
        # TODO: how to handle incoming queries while replaying history?
        # Errors thrown above this layer in application code will be
        # caught in the context manager which invoked this method, and 
        # the faulty message will be nacked.
        body = self.decode_message(message)
        response = self._query_handler(body)
        msg = self.create_message(
            body=response,
            correlation_id=message.correlation_id)
        await self.publish_one(
            message=msg,
            routing_key=message.reply_to)

    async def _handle_persisted_event(self, message):
        """wrapper for handling persisted events"""
        body = self.decode_message(message)
        if self.is_history_replaying:
            # we'll process this message in order after completing the
            # history replay
            return self.__history_queue.append(body)
        self._event_handler(body)

    async def _handle_replay_history(self, message):
        """wrapper for handling history replay"""
        body = self.decode_message(message)
        if body.get('type') == 'HISTORY_REPLAY_END':
            return self._close_history_replay()
        else:
            return self._event_handler(body)

    # history management

    async def _request_history_replay(self, last_index=0):
        """Invokes a replay of the event store and directs the ensuing messages
         to the our replay history queue binding."""
        
        log.info('Broker is requesting history replay')
        self.is_history_replaying = True
        msg_body = self.encode_message({
            "type": "HISTORY_REPLAY_REQUEST",
            "payload": {
                "last_event_id": last_index,
                "routing_key": "event.replay.readmodel"
            }})
        msg = self.create_message(
            msg_body,
            delivery_mode=self.DeliveryMode.PERSISTENT,
            reply_to='event.replay.readmodel')
        await self.publish_one(msg, routing_key='event.replay.request')

    def _close_history_replay(self):
        """processes any new persisted events which came in while history was replaying,
        then closes out the replay and returns Broker to normal service."""

        log.debug('Ready to process events received while processing history replay')
        while len(self._history_queue):
            msg = self._history_queue.popleft()
            self._event_handler(msg)
        self.is_history_replaying = False
        log.info('Finished history replay')
  