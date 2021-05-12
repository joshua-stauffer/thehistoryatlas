"""Broker implementation for the History application of the History Atlas.
Built on top of PyBroker.

April 27th, 2021"""

from collections import namedtuple
import logging
from pybroker import BrokerBase
from broker_errors import MissingReplyFieldError

log = logging.getLogger(__name__)
log.setLevel('DEBUG')

ReplayTuple = namedtuple('ReplayTuple', ['corr_id', 'task'])

class Broker(BrokerBase):

    def __init__(self, config, request_handler) -> None:
        super().__init__(
            broker_username   = config.BROKER_USERNAME,
            broker_password   = config.BROKER_PASS,
            network_host_name = config.NETWORK_HOST_NAME,
            exchange_name     = config.EXCHANGE_NAME,
            queue_name        = config.QUEUE_NAME)
        # save main application callbacks
        self._request_handler = request_handler
        # keep track of replays that are currently in progress
        self._active_replays = dict()

    async def start(self):
        """Start the broker."""
        
        log.info('Getting broker connection')
        await self.connect(retry=True, retry_timeout=0.5)

        # register handlers
        await self.add_message_handler(
            routing_key='event.replay.request',
            callback=self._handle_request)

    # on message callbacks

    async def _handle_request(self, message):
        """Wrapper for receiving replay requests and forwarding them to 
        the main application for processing."""

        log.info(f'received replay request {message}')
        body = self.decode_message(message)
        reply_to = message.reply_to
        correlation_id = message.correlation_id
        if not reply_to and correlation_id:
            raise MissingReplyFieldError
        # validate that this app hasn't already requested a replay
        if not self._validate_replay(reply_to, correlation_id):
            log.warn(f'Dropping replay request from {reply_to} with id {correlation_id}' + \
                      'because a request with that correlation id is already in process.')
            return # just going to drop this message, it's likely a duplicate

        # create a publishing function for the main application
        publisher = self.get_publisher(routing_key=reply_to)
        async def send_func(body):
            message = self.create_message(body)
            message.correlation_id = correlation_id
            await publisher(message)
        send_func.__doc__ = 'A utility method created on the fly for publishing' + \
                            f'to routing_key {reply_to}.'
        # create a cleanup function for when the main application has finished
        def close_func():
            del self._active_replays[reply_to]
        # give send_func and close_func to the main application, and get the
        # coroutine reference in return
        task = self._request_handler(body, send_func, close_func)
        replay_tuple = ReplayTuple(correlation_id, task)
        self._active_replays[reply_to] = replay_tuple

    def _validate_replay(self, reply_to, corr_id) -> bool:
        """Returns True if this request should go forward, else False"""
        # this has the effect of being forgiving if the client doesn't provide
        # a correlation id, as long as they continue to not provide one.
        if res := self._active_replays.get(reply_to):
            if res.correlation_id == corr_id:
                # this is a duplicate request, ignore it!
                return False
            # now we know this is a new request, so we need to cancel the 
            # stale replay, which is probably still in progress.
            res.task.cancel()
        return True

