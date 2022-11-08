import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

import pytest

from pybroker import BrokerBase
from tha_config import Config


@pytest.fixture(scope="session")
def TestBroker():
    class TestBroker(BrokerBase):
        def __init__(self, queue_name: str, listen_to: str):
            self._listen_to = listen_to
            config = Config()
            self.results = []
            super().__init__(
                broker_username=config.BROKER_USERNAME,
                broker_password=config.BROKER_PASS,
                network_host_name=config.NETWORK_HOST_NAME,
                exchange_name="main",
                queue_name=queue_name,
            )

        async def start(self):
            await self.connect()
            await self.add_message_handler(
                routing_key=self._listen_to, callback=self.handle_message
            )

        async def handle_message(self, message):
            body = self.decode_message(message)
            self.results.append(body)

    return TestBroker


def run_integration_test():
    def run_integration_test(broker, messages: List[Dict], routing_key: str, expected_result_count: int):

        loop = asyncio.new_event_loop()
        # setup test broker

        broker_start_coro = broker.start()
        loop.run_until_complete(broker_start_coro)

        for message in messages:
            msg = broker.create_message(body=message)
            broker_publish_coro = broker.publish_one(
                message=msg,
                routing_key=routing_key,
            )
            loop.run_until_complete(broker_publish_coro)
        start = datetime.utcnow()
        timeout = timedelta(seconds=30)
        while datetime.utcnow() - timeout <= start:
            if len(broker.results) >= expected_result_count:
                break
            else:
                sleep_coro = asyncio.sleep(0.1)
                loop.run_until_complete(sleep_coro)
        assert len(broker.results) > 0, "No events were received"
        stop_broker_coro = broker.cancel()
        loop.run_until_complete(stop_broker_coro)
        loop.stop()
        loop.close()
        return broker.results

    return run_integration_test