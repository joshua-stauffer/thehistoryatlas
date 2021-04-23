"""Broker component running on asyncio and aio-pika."""

import asyncio
from collections import deque, namedtuple
import json
import logging
from aio_pika import (connect_robust, IncomingMessage, Message, 
    DeliveryMode, ExchangeType)
from broker_errors import MessageError
from state_manager.handler_errors import CitationExistsError

MessageHandler = namedtuple('MessageHandler', ['handler', 'should_ack'])

class Broker:
    """RabbitMQ interface for the WriteModel component of the History Atlas"""
    
    def __init__(self, config, command_handler, event_handler):
        """Interface for interacting with RabbitMQ.
        Broker.start() must be called in order to receive or send messages.
        
        params:
            command_handler(message: dict) -> dict
            event_handler(message: dict) -> dict
        """
        # Main application callbacks
        self._command_handler = command_handler
        self._event_handler = event_handler
        # aio_pika objects
        self._conn = None       # assign in Broker.connect
        self._channel = None    # assign in Broker.connect
        self._consumer_tag = None
        # Broker properties
        self.config = config
        self._AMQP_URI = f'amqp://{config.BROKER_USERNAME}' + \
                         f':{config.BROKER_PASS}@{config.NETWORK_HOST_NAME}/'
        self._EXCHANGE_NAME = 'main'
        self._QUEUE_NAME = 'write_model'
        self._message_handlers = {
            # TODO: if should_ack is set to false, need to adjust the
            # logic in _handle_message, since Message.process always acks or nacks
            'command.writemodel': MessageHandler(self._handle_command, True),
            'event.persisted': MessageHandler(self._handle_persisted_event, True),
            'event.replay.writemodel': MessageHandler(self._handle_replay_history, True)
            }
        self.is_history_replaying = False
        self._history_queue = deque()

    async def start(self, is_initialized=False, replay_from=0):
        """Start the broker. Will request and process a event replay when
        after initialized unless flag is_initialized is True."""
        
        await self._connect()
        if not is_initialized:
            await self._request_history_replay(last_index=replay_from)

    async def cancel(self):
        """Gracefully close the broker connection"""

        logging.debug('Broker is cancelling service.')
        await self._queue.cancel(self._consumer_tag)

    # Internal methods for managing the connection and routing callbacks

    async def _connect(self):
        """Primary point of entry for the Broker class. Finishes asynchronous
        Broker initialization and begins listening for incoming messages."""

        logging.info('Starting broker')
        loop = asyncio.get_event_loop()
        logging.debug('getting connection')
        self._conn = await connect_robust(self._AMQP_URI, loop=loop)
        logging.debug(f'got connection: {self._conn}')
        self._channel = await self._conn.channel()
        await self._channel.set_qos(prefetch_count=1)
        self._exchange = await self._channel.declare_exchange(
            self._EXCHANGE_NAME, ExchangeType.TOPIC)
        self._queue = await self._channel.declare_queue(
            self._QUEUE_NAME, durable=True)
        for routing_key in self._message_handlers.keys():
            await self._queue.bind(self._exchange, routing_key=routing_key)
        logging.info('Broker started')
        self._consumer_tag = await self._queue.consume(self._handle_message)
        logging.info('Broker ready to consume messages')

    async def _handle_message(self, message: IncomingMessage, requeue=False):
        """Direct incoming messages to the corresponding handler. 
        Acknowledges messages after handler returns, and rejects
        message if handler raises an exception."""
        
        logging.info('Broker: received message')
        with message.process(requeue=requeue):
            # exceptions raised in this context will reject message
            handler = self._message_handlers.get(message.routing_key).handler
            if not handler:
                raise MessageError(f'No message handler was found for ' + \
                                   f'routing key {message.routing_key}')
            else:
                # NOTE: passing entire message to handler, it's up to them to 
                #       get the body from the object and transform it from 
                #       bytes > json > dict.
                await handler(message)

    # wrappers for main application callbacks

    async def _handle_command(self, message):
        """Wrapper for handling commands"""
        body = self._decode_message(message)
        # Now pass message body to main application for processing.
        # if the processing fails this line with raise an exception
        # and the context manager which called this method will
        # nack the message
        try:
            event = self._command_handler(body)
            logging.debug(f'Broker is publishing to emitted.event: {event}')
            await self._publish_emitted_event(event)
            if message.reply_to:
                await self._publish_correlated_reply({
                    "type": "COMMAND_SUCCESS"
                }, message.correlation_id, message.reply_to)
        except CitationExistsError as e:
            logging.info(f'Broker caught error from a duplicate event. ' + \
                'If sender included a reply_to value they will receive a ' + \
                'message now.')
            if message.reply_to:
                await self._publish_correlated_reply({
                    "type": "COMMAND_FAILED",
                    "payload": {
                        "reason": "Citation already exists in database.",
                        "existing_event_guid": e.GUID
                    }
                }, message.correlation_id, message.reply_to)

    async def _handle_persisted_event(self, message):
        """wrapper for handling persisted events"""
        body = self._decode_message(message)
        if self.is_history_replaying:
            # we'll process this message in order after completing the
            # history replay
            return self.__history_queue.append(body)
        self._event_handler(body)

    async def _handle_replay_history(self, message):
        """wrapper for handling history replay"""
        body = self._decode_message(message)
        if body.get('type') == 'HISTORY_REPLAY_END':
            return self._close_history_replay()
        else:
            return self._event_handler(body)

    async def _request_history_replay(self, last_index=0):
        """Invokes a replay of the event store and directs the ensuing messages
         to the our replay history queue binding."""
        
        logging.info('Broker is requesting history replay')
        self.is_history_replaying = True
        msg_body = self._encode_message({
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

    # Message encoding/decoding utilities

    @staticmethod
    def _decode_message(message: Message):
        """Receives a aio-pika Message and returns a dict"""
        return json.loads(message.body.decode())

    @staticmethod
    def _encode_message(message: Message):
        """Receives a dict and returns a binary json representation"""
        return json.dumps(message).encode()

    # internal publishing methods

    async def __publish(self, msg, routing_key):
        """Expects a ready-for-the-wire message and publishes it to 
        the given routing address"""
        await self._exchange.publish(msg, routing_key=routing_key)

    async def _publish_emitted_event(self, body: dict):
        """Publishes to anyone listening on event.emitted"""
        msg = Message(self._encode_message(body))
        await self.__publish(msg, 'event.emitted')

    async def _publish_correlated_reply(self,
        body: dict, correlation_id: str, reply_to_queue: str) -> None:
        """Sends response directly to the reply_to_queue. 
        params:
            body: message
            correlation_id: tag for recipient to identify message
            reply_to_queue: recipient queue name (usually taken from 
                            Message.reply_to)
        """

        msg = Message(
            self._encode_message(body),
            correlation_id=correlation_id)
        await self.__publish(msg, routing_key=reply_to_queue)
