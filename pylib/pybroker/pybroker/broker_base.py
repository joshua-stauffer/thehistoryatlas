"""An asyncio AMQP interface for interacting with RabbitMQ.
Built to share broker code across the History Atlas backend.
April 25th, 2021
"""

import asyncio
from collections.abc import Callable
import datetime
import json
import logging
from typing import Union
from aio_pika import (connect_robust, Message, 
    DeliveryMode, ExchangeType)

log = logging.getLogger(__name__)

class BrokerBase:
    """Batteries included base class for building a AMQP broker in Python.
    
    Designed for use in a AMQP Topic exchange. This class declares a standard
    connection, exchange, and queue, then exposes some hooks:
        add_message_handler: accepts a routing key and callback and invokes the
                             callback anytime a message is received with that
                             routing key.
        get_publisher: accepts a routing key and returns an asynchronous function
                       which will publish a message to that routing key.
        publish_one: send a single message to a routing key (useful for replying 
                     to a queue)

    Other useful methods:
        create_message: package a message body with properties
        decode_message: transform a message body into a dict
        encode_message: transform a dict into a message body of bytes

    The following aio_pika methods & properties are also included:
        DeliveryMode:   enum
        ExchangeType:   enum
        Message:        method
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
            # NOTE: Never this URL, or you will expose application secrets!
            # instead, use the SAFE_URL below
            "URL": f'amqp://{broker_username}' + \
                         f':{broker_password}@{network_host_name}/',
            "SAFE_URL": f'amqp://{broker_username}' + \
                         f':******@{network_host_name}/',
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
            "TYPE": 'topic', # using the enum ExchangeType.Topic throws an error here:
                             # defined at:
                             # https://github.com/mosquito/aio-pika/blob/94066fa900d9c08624d936f9b94037640267ac37/aio_pika/exchange.py
            "DURABLE": True,
            "AUTO_DELETE": False,   # delete queue when channel gets closed
            "TIMEOUT": None         # execution timeout
        }
        # Queue settings
        self._queue_settings = {
            "NAME": queue_name,
            "DURABLE": True,
            "EXCLUSIVE": False,
            "AUTO_DELETE": False,
            "TIMEOUT": None
        }
        # internal values used throughout class lifecycle
        self.__msg_handlers = dict()
        self.__conn = None
        self.__channel = None
        self.__exchange = None
        self.__queue = None
        self.__consumer_tag = None

        # aio_pika enums and methods
        self.DeliveryMode = DeliveryMode
        self.ExchangeType = ExchangeType
        self.Message = Message

    async def add_message_handler(self,
        routing_key: str,
        callback: Callable,
        timeout=None
        ) -> None:
        """Add a callback method to be invoked when a message is received with
        the given routing key.

        params:
            routing_key: AMQP topic routing key
            callback: potentially asynchronous function which will be invoked with
                      any messages received on the specified routing key.
            timeout: add a timeout to the queue binding
        """
        log.info(f'Added callback {callback} to routing key {routing_key}.')
        await self.__queue.bind(self.__exchange,
            routing_key=routing_key, timeout=timeout)
        self.__msg_handlers[routing_key] = callback

    def get_publisher(self, routing_key: str) -> Callable:
        """Returns an asynchronous function which will publish to param routing_key"""

        log.debug(f'Creating a new publisher for routing key {routing_key}')
        async def publish_func(message: Message):
            log.debug(f'Publishing {message} to routing key {routing_key}')
            await self.__exchange.publish(message, routing_key=routing_key)
        publish_func.__doc__ = 'Publishes a message with the routing key ' + routing_key
        return publish_func

    async def publish_one(self, message: Message, routing_key: str):
        """Publish a single message to param routing key"""
        log.debug(f'Publishing {message} to routing key {routing_key}')
        await self.__exchange.publish(message, routing_key=routing_key)

    def create_message(self,
        body: dict,
        correlation_id=None,
        content_type: str=None,
        reply_to: str=None,
        expiration:  Union[int, datetime.datetime, float, datetime.timedelta, None] =None,
        timestamp: Union[int, datetime.datetime, float, datetime.timedelta, None] =None,
        headers: dict=None
        ) -> Message:
        """Accepts a dict and correlation ID and returns a ready-for-the-wire message"""
        return Message(
            self.encode_message(body),
            correlation_id=correlation_id,
            content_type=content_type,
            reply_to=reply_to,
            expiration=expiration,
            timestamp=timestamp,
            headers=headers)

    @staticmethod
    def decode_message(message: Message):
        """Receives a aio-pika Message and returns a dict of the message body"""
        return json.loads(message.body.decode())

    @staticmethod
    def encode_message(message: dict):
        """Receives a dict and returns a binary json representation"""
        return json.dumps(message).encode()

    # methods for managing AMQP connection, channel, exchange, and queues.

    async def connect(self, retry=True, retry_timeout=0.5):
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
            log.debug(f'Retry setting is {retry} and timeout is {retry_timeout}')
            # set conf dict to connection settings
            conf = self._connection_settings
            loop = asyncio.get_event_loop()

            self.__conn = await connect_robust(
                url=conf.get('URL'),
                virtualhost=conf.get('VHOST'),
                timeout=conf.get('TIMEOUT'),
                ssl=conf.get('SSL'),
                ssl_options=conf.get('SSL_OPTIONS'),
                loop=loop)
        except Exception as e:
            log.error(f'PyBroker is unable to connect to AMQP broker ' + \
                      f'{conf.get("SAFE_URL")} with exception {e}')
            if retry:
                await asyncio.sleep(retry_timeout)
                log.info('PyBroker is retrying connection to AMQP broker.')
                return await self.connect()
            else:
                log.info('PyBroker was unable to connect and is exiting.')
        else:
            log.info('PyBroker successfully connected to AMQP server.')
            return await self._get_channel()

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
            timeout=conf.get('TIMEOUT'))
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
        self.__consumer_tag = await self.__queue.consume(
                self._consumer, no_ack=False, timeout=None)
        log.debug('Queue established and message handlers can now be bound.')

    async def _consumer(self, message):
        if handler := self.__msg_handlers.get(message.routing_key):
            log.debug(f'Handling a message with routing key {message.routing_key}')
            with message.process():
                await handler(message)
        else:
            log.debug(f"consumer couldn't find a handler for message {message}")

    async def cancel(self):
        """Gracefully close the broker connection"""

        log.debug('PyBroker is cancelling service.')
        await self.__queue.cancel(self.__consumer_tag)
