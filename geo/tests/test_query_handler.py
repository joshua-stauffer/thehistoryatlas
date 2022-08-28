import pytest
from geo.state.query_handler import QueryHandler
from geo.errors import MessageMissingTypeError
from geo.errors import MessageMissingPayloadError
from geo.errors import UnknownQueryError

@pytest.fixture
def db(result_a, name_a, result_b, name_b, result_c, name_c):
    class DB:
        @staticmethod
        def get_coords_by_name(name):
            return result_a

        @staticmethod
        def get_coords_by_name_batch(names):
            return {
                name_a: result_a,
                name_b: result_b,
                name_c: result_c
            }
    return DB()

@pytest.fixture
def result_a():
    return [{'latitude': 1.1,
            'longitude': 2.2},
            {'latitude': 3.3,
            'longitude': 4.4}]

@pytest.fixture
def result_b():
    return [{'latitude': 5.5,
                'longitude': 6.6},
                {'latitude': 7.7,
                'longitude': 8.8}]
@pytest.fixture
def result_c():
    return []

@pytest.fixture
def name_a():
    return 'Raul Capablanca'

@pytest.fixture
def name_b():
    return 'Paul Morphy'

@pytest.fixture
def name_c():
    return 'François-André Danican Philidor'

@pytest.fixture
def coords_by_name_query(name_a):
    return {
        'type': 'GET_COORDS_BY_NAME',
        'payload': {'name': name_a}
    }

@pytest.fixture
def coords_by_name_batch_query(name_a, name_b, name_c):
    return {
        'type': 'GET_COORDS_BY_NAME_BATCH',
        'payload': {'names': [name_a, name_b, name_c]}
    }

@pytest.fixture
def qh(db):
    return QueryHandler(db)

def test_query_handler_exists(qh):
    assert qh != None

def test_handle_query_raises_missing_type_error(qh):
    no_type = {'payload': 'not important here'}
    with pytest.raises(MessageMissingTypeError):
        qh.handle_query(no_type)

def test_handle_query_raises_missing_payload_error(qh):
    no_type = {'type': 'doesnt matter yet'}
    with pytest.raises(MessageMissingPayloadError):
        qh.handle_query(no_type)

def test_handle_get_coords_by_name(qh, coords_by_name_query, result_a, name_a):
    res = qh.handle_query(coords_by_name_query)
    assert isinstance(res, dict)
    assert res['type'] == 'COORDS_BY_NAME'
    assert isinstance(res['payload'], dict)
    assert isinstance(res['payload']['coords'], dict)
    assert res['payload']['coords'][name_a] is result_a

def test_handle_get_coords_by_name_batch(qh, coords_by_name_batch_query, 
    result_a, name_a, result_b, name_b, result_c, name_c): 
    res = qh.handle_query(coords_by_name_batch_query)
    assert isinstance(res, dict)
    assert res['type'] == 'COORDS_BY_NAME_BATCH'
    assert isinstance(res['payload'], dict)
    assert isinstance(res['payload']['coords'], dict)
    assert res['payload']['coords'][name_a] is result_a
    assert res['payload']['coords'][name_b] is result_b
    assert res['payload']['coords'][name_c] is result_c