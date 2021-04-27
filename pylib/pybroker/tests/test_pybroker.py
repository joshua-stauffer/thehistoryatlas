import asyncio
import pytest
import aio_pika

from pybroker import __version__
from pybroker.broker_base import BrokerBase

# let pytest know some tests will be coroutines
pytestmark = pytest.mark.asyncio

def test_version():
    assert __version__ == '0.1.0'

@pytest.fixture
def username():
    return 'test'

@pytest.fixture
def password():
    return 'test-123'

@pytest.fixture
def network_host_name():
    return 'some-network'

@pytest.fixture
def exchange_name():
    return 'an-exchange'

@pytest.fixture
def queue_name():
    return 'queuey-queue'


@pytest.fixture
def base(username, password, network_host_name, exchange_name, queue_name):
    return BrokerBase(
        broker_username=username,
        broker_password=password,
        network_host_name=network_host_name,
        exchange_name=exchange_name,
        queue_name=queue_name
    )

def test_broker_base_init(base, username, password, network_host_name, exchange_name, queue_name):
    # check that the values have ended up in the expected places
    # and that the expected constant values are present

    # connection
    assert base._connection_settings.get('URL') == \
        f'amqp://{username}:{password}@{network_host_name}/'
    assert base._connection_settings.get('VHOST') == '/' 
    assert base._connection_settings.get('SSL') == False
    assert base._connection_settings.get('SSL_OPTIONS') == None
    assert base._connection_settings.get('TIMEOUT') == None

    # exchange
    assert base._channel_settings.get('PUBLISHER_CONFIRMS') == False
    assert base._exchange_settings.get('NAME') == exchange_name
    assert base._exchange_settings.get('TYPE') == 'topic'
    assert base._exchange_settings.get('DURABLE') == True
    assert base._exchange_settings.get('AUTO_DELETE') == False
    assert base._exchange_settings.get('TIMEOUT') == None

    # queue
    assert base._queue_settings.get('NAME') == queue_name
    assert base._queue_settings.get('DURABLE') == True
    assert base._queue_settings.get('EXCLUSIVE') == False
    assert base._queue_settings.get('AUTO_DELETE') == False
    assert base._queue_settings.get('TIMEOUT') == None
    
    # internal values (accounting for python's name mangling)
    assert base._BrokerBase__no_ack_msg_handlers == dict()
    assert base._BrokerBase__ack_msg_handlers == dict()
    assert base._BrokerBase__conn == None
    assert base._BrokerBase__channel == None
    assert base._BrokerBase__exchange == None
    assert base._BrokerBase__queue == None
    assert base._BrokerBase__ack_consumer_tag == None
    assert base._BrokerBase__no_ack_consumer_tag == None


@pytest.mark.asyncio
@pytest.mark.skip('Throws code into an infinite loop if retry=True')
async def test_connect(monkeypatch, event_loop, base, username, password, network_host_name):

    store = dict()
    def fake_connect_robust(url, virtualhost, timeout, ssl, ssl_options, loop=event_loop):
        store['url'] = url
        store['virtualhost'] = virtualhost
        store['timeout'] = timeout
        store['ssl'] = ssl
        store['ssl_options'] = ssl_options
        store['loop'] = loop
        return 'fake-connection'

    monkeypatch.setattr(aio_pika, 'connect_robust', fake_connect_robust)
    monkeypatch.setattr(base, '_get_exchange', lambda : None)
    # double check that the monkey patches worked..
    assert base._get_exchange() == None
    assert aio_pika.connect_robust == fake_connect_robust

    await base.connect(retry=True)

    assert store['virtualhost'] == '/'
    assert store['loop'] == event_loop
    assert store['ssl'] == False
    assert store['ssl_options'] == None
    assert store['timeout'] == None
    assert store['url'] == f'amqp://{username}:{password}@{network_host_name}/'
    assert base._BrokerBase__conn == 'fake-connection'


def test_add_no_ack_consumer(base):
    store = None
    def fake_handler(msg):
        nonlocal store
        store = str(msg)
    base._BrokerBase__no_ack_msg_handlers['test'] = fake_handler

    class Msg:
        def __init__(self): self.routing_key = 'test'
        def __repr__(self): return 'hi'

    base._no_ack_consumer(Msg())
    assert store == 'hi'
