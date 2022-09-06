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
                network_host_name="localhost",  # "=config.NETWORK_HOST_NAME,
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


class TestBroker(BrokerBase):
    def __init__(self, queue_name: str, listen_to: str):
        self._listen_to = listen_to
        config = Config()
        self.results = []
        super().__init__(
            broker_username=config.BROKER_USERNAME,
            broker_password=config.BROKER_PASS,
            network_host_name="localhost",  # "=config.NETWORK_HOST_NAME,
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
