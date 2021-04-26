"""An asyncio AMQP interface for interacting with RabbitMQ.
Built to share broker code across the History Atlas backend.
April 25th, 2021
"""

import asyncio
import json
import logging
from aio_pika import (connect_robust, IncomingMessage, Message, 
    DeliveryMode, ExchangeType)

log = logging.getLogger(__name__)

class BrokerBase:
    """Batteries included base class for building a AMQP broker in Python.
    
    Designed for use in a AMQP Topic exchange. This class declares a standard
    connection, exchange, and queue, then exposes two hooks:
        add_message_handler: accepts a routing key and callback and invokes the
                             callback anytime a message is received with that
                             routing key.
        get_publisher: accepts a routing key and returns an asynchronous function
                       which will publish a message to that routing key.  
    """

    def __init__(self, 
        broker_username:    str,
        broker_password:    str,
        network_host_name:  str,
        exchange_name:      str,
        queue_name:         str='',
    ): 
        # AMQP settings that we want to set globally across all applications
        # Connection settings
        self._connection_settings = {
            "URL": f'amqp://{broker_username}' + \
                         f':{broker_password}@{network_host_name}/',
            "VHOST": "/",
            "SSL": False,
            "SSL_OPTIONS": None, # but use a dict if you need these
            "TIMEOUT": None
        }
        # Channel settings
        self._channel_settings = {
            "PUBLISHER_CONFIRMS": False
        }
        # Exchange settings
        self._exchange_settings = {
            "NAME": exchange_name,
            "TYPE": ExchangeType.Topic,
            "DURABLE": True,
            "AUTO_DELETE": False,   # delete queue when channel gets closed
            "TIMEOUT": None         # execution timeout
        }
        # Queue settings
        self._queue_settings = {
            "NAME": queue_name,
            "DURABLE": True,
            "EXCLUSIVE": False,
            "AUTODELETE": False,
            "TIMEOUT": None
        }
        # internal values used throughout class lifecycle
        self.__no_ack_msg_handlers = dict()
        self.__ack_msg_handlers = dict()
        self.__conn = None
        self.__channel = None
        self.__exchange = None
        self.__queue = None
        self.__ack_consumer_tag = None
        self.__no_ack_consumer_tag = None

    async def add_message_handler(self,
        routing_key: str,
        callback: function,
        ack: bool,
        timeout=None
        ) -> None:
        """Add a callback method to be invoked when a message is received with
        the given routing key.
        NOTE: The ack flag determines if 
        
        params:
            routing_key: AMQP topic routing key
            callback: potentially asynchronous function which will be invoked with
                      any messages received on the specified routing key.
            timeout: add a timeout to the queue binding
        """
        log.info(f'Added callback {callback} to routing key {routing_key}.')
        if ack:
            handler_dict = self.__ack_msg_handlers
        else:
            handler_dict = self.__no_ack_msg_handlers
        await self.__queue.bind(self.__exchange,
            routing_key=routing_key, timeout=timeout)
        handler_dict[routing_key] = callback

    def get_publisher(self, routing_key: str) -> function:
        """Returns an asynchronous function which will publish to param routing_key"""

        async def publish_func(message: Message):
            await self.__exchange.publish(message, routing_key=routing_key)
        publish_func.__doc__ = 'Publishes a message with the routing key ' + routing_key
        return publish_func

    async def publish_one(self, message: Message, routing_key: str):
        """Publish a single message to param routing key"""
        await self.__exchange.publish(message, routing_key=routing_key)

    @staticmethod
    def decode_message(message: Message):
        """Receives a aio-pika Message and returns a dict"""
        return json.loads(message.body.decode())

    @staticmethod
    def encode_message(message: dict):
        """Receives a dict and returns a binary json representation"""
        return json.dumps(message).encode()

    # methods for managing AMQP connection, channel, exchange, and queues.

    async def connect(self, retry=True, retry_timeout=500):
        """Create a connection to the AMQP broker.
        params:
            retry: 
            retry_timeout: wait time in ms between retry attempts

        Connection properties (set in BrokerBase.__init__)
            url (or use the following explicitly)
                host
                port
                login
                password
            virtualhost = '/'
            ssl: bool
        """
        try:
            log.debug('Getting connection')
            # set conf dict to connection settings
            conf = self._connection_settings
            loop = asyncio.get_event_loop()

            self._conn = await connect_robust(
                url=conf.get('URL'),
                virtualhost=conf.get('VHOST'),
                timeout=conf.get('TIMEOUT'),
                ssl=conf.get('SSL'),
                ssl_options=conf.get('SSL_OPTIONS'),
                loop=loop)
        except Exception as e:
            log.error(f'PyBroker is unable to connect to AMQP broker ' + \
                      f'{self._AMQP_URI} with exception {e}')
            if retry:
                await asyncio.sleep(retry_timeout)
                log.info('PyBroker is retrying connection to AMQP broker.')
                return await self.connect()
            else:
                log.info('PyBroker was unable to connect and is exiting.')
        else:
            log.info('PyBroker successfully connected to AMQP server.')
            return await self._get_exchange()

    async def _get_channel(self):
        """Declares a channel. Requires that a connection has already been established.
        
        Channel properties (set in BrokerBase.__init__)
            publisher_confirms: bool
        """
        # set conf dict to channel settings
        conf = self._channel_settings
        self.__channel = await self.__conn.channel(
            publisher_confirms=conf.get("PUBLISHER_CONFIRMS"))
        log.debug('Channel established')
        return await self._get_exchange()

    async def _get_exchange(self):
        """Declares an exchange. Requires that a connection and channel have 
        already been established.
        
        Exchange properties are set in BrokerBase.__init__
        """
        # set conf dict to exchange settings
        conf = self._exchange_settings
        self.__exchange = await self.__channel.declare_exchange(
            name=conf.get('NAME'),
            type=conf.get('TYPE'),
            durable=conf.get('DURABLE'),
            auto_delete=conf.get('AUTO_DELETE'),
            timeout=conf.get('TIMEOUT')
        )
        log.debug('Exchange established')
        return await self._get_queue()

    async def _get_queue(self):
        """Declares a queue. Requires that a connection, channel, and exchange
        have already been established.

        Queue properties are defined in BrokerBase.__init__
        """
        # set conf dict to queue settings
        conf = self._queue_settings
        self.__queue = await self.__channel.declare_queue(
            name=conf.get('NAME'),
            durable=conf.get('DURABLE'),
            exclusive=conf.get('EXCLUSIVE'),
            timeout=conf.get('TIMEOUT')
        )
        self.__no_ack_consumer_tag = self.__queue.consume(
                self._no_ack_consumer, no_ack=True, timeout=None)
        self.__ack_consumer_tag = self.__queue.consume(
                self._ack_consumer, no_ack=False, timeout=None)


    def _no_ack_consumer(self, message):
        """Adds a consumer for incoming messages that don't need acknowledgement"""
        if handler := self.__no_ack_msg_handlers.get(message.routing_key):
            handler(message)

    def _ack_consumer(self, message):
        """Adds a consumer for incoming messages that need acknowledgement"""
        if handler := self.__ack_msg_handlers.get(message.routing_key):
            with message.process():
                handler(message)
