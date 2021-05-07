"""Broker implementation for the WriteModel. Built on top of PyBroker.

April 26th, 2021"""

import asyncio
from collections import deque
import logging
from pybroker import BrokerBase
from broker_errors import MessageError
from state_manager.handler_errors import CitationExistsError, CitationMissingFieldsError

log = logging.getLogger(__name__)
log.setLevel('DEBUG')

class Broker(BrokerBase):

    def __init__(self, config, command_handler, event_handler) -> None:
        super().__init__(
            broker_username   = config.BROKER_USERNAME,
            broker_password   = config.BROKER_PASS,
            network_host_name = config.NETWORK_HOST_NAME,
            exchange_name     = config.EXCHANGE_NAME,
            queue_name        = config.QUEUE_NAME)
            
        self.is_history_replaying = False
        self._history_queue = deque()

        # save main application callbacks
        self._command_handler = command_handler
        self._event_handler = event_handler

    async def start(self, is_initialized=False, replay_from=0):
        """Start the broker. Will request and process a event replay when
        after initialized unless flag is_initialized is True."""
        
        await self.connect()

        # register handlers
        await self.add_message_handler(
            routing_key='command.writemodel',
            callback=self._handle_command)
        await self.add_message_handler(
            routing_key='event.persisted',
            callback=self._handle_persisted_event)
        await self.add_message_handler(
            routing_key='event.replay.writemodel',
            callback=self._handle_replay_history)

        # get publish methods
        self._publish_emitted_event = self.get_publisher(
            routing_key='event.emitted')

        if not is_initialized:
            await self._request_history_replay(last_index=replay_from)

    # on message callbacks
            
    async def _handle_command(self, message):
        """Wrapper for handling commands"""
        body = self.decode_message(message)
        # Now pass message body to main application for processing.
        # if the processing fails this line with raise an exception
        # and the context manager which called this method will
        # nack the message
        try:
            event = self._command_handler(body)
            msg = self.create_message(event, headers=message.headers)
            log.debug(f'Broker is publishing to emitted.event: {event}')
            await self._publish_emitted_event(msg)
            # check if the publisher wants to hear a reply
            if message.reply_to:
                body = self.create_message({
                    "type": "COMMAND_SUCCESS"
                }, correlation_id=message.correlation_id, headers=message.headers)
                await self.publish_one(body, message.reply_to)
        except CitationExistsError as e:
            log.info(f'Broker caught error from a duplicate event. ' + \
                'If sender included a reply_to value they will receive a ' + \
                'message now.')
            if message.reply_to:
                body = self.create_message({
                    "type": "COMMAND_FAILED",
                    "payload": {
                        "reason": "Citation already exists in database.",
                        "existing_event_guid": e.GUID
                    }
                }, correlation_id=message.correlation_id, headers=message.headers)
                await self.publish_one(body, message.reply_to)
        except CitationMissingFieldsError as e:
            log.info(f'Broker caught an error from a citation missing fields. ' + \
                'If sender included a reply_to value they will receive a ' + \
                'message now.')
            log.info(e)
            if message.reply_to:
                body = self.create_message({
                    "type": "COMMAND_FAILED",
                    "payload": {
                        "reason": "Citation was missing fields (text, GUID, tags, or meta)."
                    }
                }, correlation_id=message.correlation_id, headers=message.headers)
                await self.publish_one(body, message.reply_to)        

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
        body = self.decode_message(message)
        if body.get('type') == 'HISTORY_REPLAY_END':
            return self._close_history_replay()
        else:
            return self._event_handler(body)

    async def _request_history_replay(self, last_index=0):
        """Invokes a replay of the event store and directs the ensuing messages
         to the our replay history queue binding."""
        
        log.info('Broker is requesting history replay')
        self.is_history_replaying = True
        msg_body = {
            "type": "REQUEST_HISTORY_REPLAY",
            "payload": {
                "last_event_id": last_index
            }}
        msg = self.create_message(
            msg_body,
            reply_to='event.replay.writemodel')
        while True:
            # 
            try:
                await self.publish_one(msg, routing_key='event.replay.request')
                return
            except Exception as e:
                log.error(f'Failed to publish history replay request due to: {e}\nTrying again in one second.')
                await asyncio.sleep(1)

    def _close_history_replay(self):
        """processes any new persisted events which came in while history was replaying,
        then closes out the replay and returns Broker to normal service."""

        log.debug('Ready to process events received while processing history replay')
        while len(self._history_queue):
            msg = self._history_queue.popleft()
            self._event_handler(msg)
        self.is_history_replaying = False
        log.info('Finished history replay')
