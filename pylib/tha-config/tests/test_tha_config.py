import os
import pytest
from tha_config import __version__, get_from_env, MissingEnvVariable
from tha_config.config import Config


def test_version():
    assert __version__ == "0.1.0"


@pytest.fixture
def prod_uri():
    return "a production uri"


@pytest.fixture
def dev_uri():
    return "a development uri"


@pytest.fixture
def dev_env(monkeypatch, prod_uri, dev_uri):
    dev_env = {"TESTING": False, "PROD_DB_URI": prod_uri, "DEV_DB_URI": dev_uri}
    monkeypatch.setattr(os, "environ", dev_env)


def test_config_no_env_variables():
    c = Config()
    assert c.TESTING == False
    assert c._DEV_DB_URI == None
    assert c._PROD_DB_URI == None
    assert c._TESTING_DB_URI == "sqlite+pysqlite:///:memory:"
    assert c.DB_URI == None
    assert c.NETWORK_HOST_NAME == "localhost"
    assert c.BROKER_USERNAME == "guest"
    assert c.BROKER_PASS == "guest"
    assert c.QUEUE_NAME == ""
    assert c.EXCHANGE_NAME == ""
    assert c.CONFIG == "DEVELOPMENT"


def test_config_picks_up_testing_env(dev_env, dev_uri):
    c = Config()
    assert c.DB_URI == dev_uri


@pytest.fixture
def simple_env(monkeypatch):
    env = {"foo": "bar"}
    monkeypatch.setattr(os, "environ", env)


def test_get_from_env_returns_value(simple_env):
    value = get_from_env("foo")
    assert value == "bar"


def test_get_from_env_with_default(simple_env):
    default = "default"
    value = get_from_env("nonexistent", default)
    assert value == default


def test_get_from_env_raises_exception(simple_env):
    with pytest.raises(MissingEnvVariable):
        _ = get_from_env("nonexistent")
