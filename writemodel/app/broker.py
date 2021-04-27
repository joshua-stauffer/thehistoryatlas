
from collections import deque
import logging
from pybroker import BrokerBase
from broker_errors import MessageError
from state_manager.handler_errors import CitationExistsError

log = logging.getLogger(__name__)

class Broker(BrokerBase):

    def __init__(self, config, command_handler, event_handler) -> None:
        super().__init__(
            broker_username=    config.BROKER_USERNAME,
            broker_password=    config.BROKER_PASS,
            network_host_name=  config.NETWORK_HOST_NAME,
            exchange_name=      config.EXCHANGE_NAME,
            queue_name=         config.QUEUE_NAME)
            
        self.is_history_replaying = False
        self._history_queue = deque()

        # save main application callbacks
        self._command_handler = command_handler
        self._event_handler = event_handler

    async def start(self, is_initialized=False, replay_from=0):
        """Start the broker. Will request and process a event replay when
        after initialized unless flag is_initialized is True."""
        
        await self.connect()
        if not is_initialized:
            await self._request_history_replay(last_index=replay_from)

        # register handlers
        await self.add_message_handler(
            routing_key='command.writemodel',
            callback=self._handle_command,
            ack=True)

        # get publish methods
        self._publish_emitted_event = self.get_publisher(
            routing_key='event.emitted')
            
    async def _handle_command(self, message):
        """Wrapper for handling commands"""

        body = self.decode_message(message)
        # Now pass message body to main application for processing.
        # if the processing fails this line with raise an exception
        # and the context manager which called this method will
        # nack the message
        try:
            event = self._command_handler(body)
            msg = self.create_message(event)
            log.debug(f'Broker is publishing to emitted.event: {event}')
            await self._publish_emitted_event(msg)
            if message.reply_to:
                response = self.create_message({
                    "type": "COMMAND_SUCCESS"
                }, correlation_id=message.correlation_id,)
                await self.publish_one(response, message.reply_to)
        except CitationExistsError as e:
            log.info(f'Broker caught error from a duplicate event. ' + \
                'If sender included a reply_to value they will receive a ' + \
                'message now.')
            if message.reply_to:
                await self.publish_one({
                    "type": "COMMAND_FAILED",
                    "payload": {
                        "reason": "Citation already exists in database.",
                        "existing_event_guid": e.GUID
                    }
                }, message.correlation_id, message.reply_to)

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

    async def _request_history_replay(self, last_index=0):
        """Invokes a replay of the event store and directs the ensuing messages
         to the our replay history queue binding."""
        
        logging.info('Broker is requesting history replay')
        self.is_history_replaying = True
        msg_body = self.encode_message({
            "type": "HISTORY_REPLAY_REQUEST",
            "payload": {
                "last_event_id": last_index,
                "priority_sort": True,
                "routing_key": "event.replay.writemodel"
            }})
        msg = Message(
            msg_body,
            delivery_mode=DeliveryMode.PERSISTENT)
        await self._exchange.publish(msg, routing_key='event.replay.request')

    def _close_history_replay(self):
        """processes any new persisted events which came in while history was replaying,
        then closes out the replay and returns Broker to normal service."""

        logging.debug('Ready to process events received while processing history replay')
        handler = self._message_handlers.get('event.replay.writemodel').handler
        while len(self._history_queue):
            msg = self._history_queue.popleft()
            handler(msg)
        self.is_history_replaying = False
        logging.info('Finished history replay')