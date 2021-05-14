from uuid import uuid4
import pytest
from app.resolver import Resolver

@pytest.fixture
def query_geo():
    def query():
        pass
    return query

@pytest.fixture
def query_readmodel():
    def query():
        pass
    return query

@pytest.fixture
def resolver(query_readmodel, query_geo):
    r = Resolver(query_geo, query_readmodel)
    return r

@pytest.fixture
def entity_dict():
    return {
        'PERSON': [
            {'text': 'name1'},
            {'text': 'name2'},
            {'text': 'name3'},

        ],
        'PLACE': [
            {'text': 'name4'},
            {'text': 'name5'},
            {'text': 'name6'}
        ],
        'TIME': [
            {'text': 'name7'},
            {'text': 'name8'},
            {'text': 'name9'},
        ]
    }

@pytest.fixture
def name_guid_dict(entity_dict):
    name_dict = dict()
    for k in entity_dict.keys():
        for val in entity_dict[k]:
            name = val['text']
            name_dict[name] = [str(uuid4()) for _ in range(3)]
    return name_dict

def test_get_names_no_key(entity_dict, resolver):
    names = resolver._get_names(entity_dict)
    assert isinstance(names, list)
    assert len(names) == 9
    name_set = set(names)
    assert len(name_set) == len(names)
    
@pytest.mark.parametrize('key,names',
    [('PERSON', ['name1', 'name2', 'name3']),
     ('PLACE', ['name4', 'name5', 'name6']),
     ('TIME', ['name7', 'name8', 'name9'])])
def test_get_names_with_key(entity_dict, resolver, key, names):
    names = resolver._get_names(entity_dict, key=key)
    assert isinstance(names, list)
    assert len(names) == 3
    name_set = set(names)
    assert len(name_set) == len(names)
    for n in names:
        assert n in name_set

def test_add_guids_no_key(entity_dict, resolver, name_guid_dict):
    res = resolver._add_guids(entity_dict, name_guid_dict, 'guids', entity_key=None)
    for v in res.values():
        for tag in v:
            assert len(tag['guids']) == 3
            for e in tag['guids']:
                assert isinstance(e, str)

@pytest.mark.parametrize('key', ['PERSON', 'PLACE', 'TIME'])
def test_add_guids_with_key(entity_dict, resolver, name_guid_dict, key):
    res = resolver._add_guids(entity_dict, name_guid_dict, 'guids', entity_key=key)
    for tag in res[key]:
        print('tag ', tag)
        assert len(tag['guids']) == 3
        for e in tag['guids']:
            assert isinstance(e, str)

def test_add_guids_no_key(entity_dict, resolver, name_guid_dict):
    VAL_KEY = 'coords'
    res = resolver._add_guids(entity_dict, name_guid_dict, VAL_KEY, entity_key=None)
    for v in res.values():
        for tag in v:
            assert len(tag[VAL_KEY]) == 3
            for e in tag[VAL_KEY]:
                assert isinstance(e, str)

@pytest.mark.parametrize('key', ['PERSON', 'PLACE', 'TIME'])
def test_add_guids_with_key(entity_dict, resolver, name_guid_dict, key):
    VAL_KEY = 'coords'
    res = resolver._add_guids(entity_dict, name_guid_dict, VAL_KEY, entity_key=key)
    for tag in res[key]:
        print('tag ', tag)
        assert len(tag[VAL_KEY]) == 3
        for e in tag[VAL_KEY]:
            assert isinstance(e, str)

