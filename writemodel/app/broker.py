"""Broker component running on asyncio and aiormq."""

import asyncio
import aiormq
import aiormq.types

class Broker:
    
    def __init__(self, config, command_handler, event_handler):
        self._conn = None       # assign in Broker.connect
        self._channel = None    # assign in Broker.connect

        self.config = config
        self._AMQP_URI = f'amqp://{config.BROKER_USERNAME}' + \
                         f':{config.BROKER_PASS}@{config.NETWORK_HOST_NAME}/'
        self._ROUTING_KEYS = ['command.writemodel', 'event.persisted']
        self._EXCHANGE_NAME = 'main'
        self._QUEUE_NAME = 'write_model'
        self._message_handlers = {
            self._ROUTING_KEYS[0]: command_handler,
            self._ROUTING_KEYS[1]: event_handler
            }

    async def connect(self):
        loop = asyncio.get_event_loop()
        self.conn = await aiormq.connect(self._AMQP_URI, loop=loop)

        self._channel = await self.conn.channel()
        await self.basic_qos(prefetch_count=1)
        await self.channel.exchange_declare(self._EXCHANGE_NAME, exchange_type='topic')
        declare_ok = await self.channel.queue_declare(self._QUEUE_NAME, durable=True)
        for routing_key in self._ROUTING_KEYS:
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

class BrokerError(Exception):
    """base class for WriteModel.Broker exceptions"""
    pass

class MessageError(BrokerError):
    def __init__(self, msg):
        self.msg = msg