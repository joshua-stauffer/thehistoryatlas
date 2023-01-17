import os

import pytest

from pybroker import BrokerBase


@pytest.fixture
def gql_api_url() -> str:
    return "http://localhost:4400"


@pytest.fixture
def broker() -> BrokerBase:
    broker_username = os.environ.get("BROKER_USERNAME", None)
    broker_password = os.environ.get("BROKER_PASS", None)
    network_host_name = os.environ.get("HOST_NAME", None)
    exchange_name = os.environ.get("EXCHANGE_NAME", None)
    queue_name = os.environ.get("QUEUE_NAME", None)
    if any(
        [
            env_var is None
            for env_var in (
                broker_username,
                broker_password,
                network_host_name,
                exchange_name,
                queue_name,
            )
        ]
    ):
        raise Exception("Unable to create Broker due to missing env variable.")

    return BrokerBase(
        broker_username=broker_username,
        broker_password=broker_password,
        network_host_name=network_host_name,
        exchange_name=exchange_name,
        queue_name=queue_name,
    )


@pytest.fixture
def username() -> str:
    return os.environ.get("USERNAME", "admin")


@pytest.fixture
def password() -> str:
    return os.environ.get("PASSWORD", "admin")
