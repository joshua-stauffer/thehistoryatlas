"""Broker component running on asyncio and aiormq."""

import asyncio
from collections import deque, namedtuple
import json
import aiormq
import aiormq.types

MessageHandler = namedtuple('MessageHandler', ['handler', 'should_ack'])

class Broker:
    
    def __init__(self, config, command_handler, event_handler, replay_history_handler):
        self._conn = None       # assign in Broker.connect
        self._channel = None    # assign in Broker.connect
        self.config = config
        self._AMQP_URI = f'amqp://{config.BROKER_USERNAME}' + \
                         f':{config.BROKER_PASS}@{config.NETWORK_HOST_NAME}/'
        self._EXCHANGE_NAME = 'main'
        self._QUEUE_NAME = 'write_model'
        self._message_handlers = {
            'command.writemodel': MessageHandler(command_handler, True),
            'event.persisted': MessageHandler(event_handler, True),
            'event.replay.writemodel': MessageHandler(replay_history_handler, True)
            }
        self.is_history_replaying = False
        self.history_queue = deque()

    async def connect(self):
        """Primary point of entry for the Broker class. Finishes asynchronous
        Broker initialization and begins listening for incoming messages."""
        loop = asyncio.get_event_loop()
        self._conn = await aiormq.connect(self._AMQP_URI, loop=loop)
        self._channel = await self.conn.channel()
        await self.basic_qos(prefetch_count=1)
        await self._channel.exchange_declare(self._EXCHANGE_NAME, exchange_type='topic')
        declare_ok = await self.channel.queue_declare(self._QUEUE_NAME, durable=True)
        for routing_key in self._message_handlers.keys():
            await self.channel.queue_bind(
                declare_ok.queue, self._EXCHANGE_NAME, routing_key=routing_key
            )
        await self._channel.basic_consume(declare_ok.queue, self._handle_message)

    async def _handle_message(self, message: aiormq.types.DeliveredMessage):
        """Callback function for handling message events"""
        routing_key = message.delivery.routing_key
        body = message.body
        msg_handler = self._message_handlers.get(routing_key)
        if not msg_handler:
            raise MessageError(f'No message handler was found for routing key {routing_key}')

    async def request_history_replay(self, last_index=0):
        """Invokes a replay of the event store and directs the stream to the supplied function"""
        self.is_history_replaying = True
        msg = json.dumps({
            "type": "REQUEST_HISTORY_REPLAY",
            "payload": {
                "last_index": last_index
            }
        })
        await self._channel.basic_publish(
            msg, self._EXCHANGE_NAME, routing_key='event.history',
            properties=aiormq.spec.Basic.Properties(
                
            )
        )

    def close_history_replay(self):
        """processes any new persisted events which came in while history was replaying,
        then closes out the replay and returns Broker to normal service."""
        handler = self._message_handlers.get('event.replay.writemodel').handler
        while len(self.history_queue):
            msg = self.history_queue.popleft()
            handler(msg)
        self.is_history_replaying = False

class BrokerError(Exception):
    """base class for WriteModel.Broker exceptions"""
    pass

class MessageError(BrokerError):
    def __init__(self, msg):
        self.msg = msg