
from collections.abc import Callable
import logging
from pybroker import BrokerBase
from .tackle_errors import ReplyToFieldNotProvidedError

log = logging.getLogger(__name__)

class Broker(BrokerBase):

    def __init__(self):
        super().__init__(
            broker_username='guest',
            broker_password='guest',
            network_host_name='broker',
            exchange_name='main',
            queue_name='test_queue')

    def get_callback(self,
        process_func: Callable,
        reply: bool=False,
        response_msg_success: dict=None,
        response_msg_failure: dict=None
        ) -> Callable:
        
        log.info('Creating callback')
        async def callback(message):
            log.info(f'Callback invoked: {message}')
            body = self.decode_message(message)
            # the corr_id is stored in the headers in order to avoid conflicting with
            # application-level use of correlation_id as a message property
            raw_corr_id = message.headers['corr_id']
            log.info(f'Retrieved correlation id of {raw_corr_id} from incoming message headers')
            corr_id = raw_corr_id.decode()
            res = process_func(body, corr_id)
            if res:
                if not message.reply_to:
                    raise ReplyToFieldNotProvidedError
                if res:
                    reply = self.create_message(response_msg_success)
                else:
                    reply = self.create_message(response_msg_failure)
                await self.publish_one(reply, routing_key=message.reply_to)

        return callback
