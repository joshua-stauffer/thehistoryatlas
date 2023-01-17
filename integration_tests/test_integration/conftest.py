import os

import pytest

from pybroker import BrokerBase
from tha_config import Config


@pytest.fixture
def gql_api_url() -> str:
    return os.environ.get("API_URL", "http://localhost:4400")


@pytest.fixture
def broker() -> BrokerBase:
    config = Config()
    return BrokerBase(
        broker_username=config.BROKER_USERNAME,
        broker_password=config.BROKER_USERNAME,
        network_host_name=config.NETWORK_HOST_NAME,
        exchange_name=config.EXCHANGE_NAME,
        queue_name=config.QUEUE_NAME,
    )


@pytest.fixture
def username() -> str:
    return os.environ.get("USERNAME", "admin")


@pytest.fixture
def password() -> str:
    return os.environ.get("PASSWORD", "admin")
