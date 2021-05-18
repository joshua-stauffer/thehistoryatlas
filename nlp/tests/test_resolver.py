from random import random
from uuid import uuid4
import pytest
from app.resolver import Resolver

@pytest.fixture
def query_geo():
    async def query(query, corr_id):
        assert isinstance(query, dict)
        assert query['type'] == 'GET_COORDS_FROM_NAME_BATCH'
        assert isinstance(query['payload'], dict)
        assert isinstance(query['payload']['names'], list)
        assert isinstance(corr_id, str)
    return query

@pytest.fixture
def query_readmodel():
    async def query(query, corr_id):
        assert isinstance(query, dict)
        assert query['type'] == 'GET_GUIDS_BY_NAME_BATCH'
        assert isinstance(query['payload'], dict)
        assert isinstance(query['payload']['names'], list)
        assert isinstance(corr_id, str)
    return query

@pytest.fixture
def pub_func():
    async def pub(result):
        assert isinstance(result, dict)

    return pub

@pytest.fixture
def resolver(query_readmodel, query_geo, entity_dict, pub_func):
    r = Resolver(
            corr_id=str(uuid4()),
            text='not needed',
            text_map=entity_dict,
            pub_func=pub_func,
            query_geo=query_geo,
            query_readmodel=query_readmodel)
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

@pytest.fixture
def coord_dict(entity_dict):
    coord_dict = dict()
    for k in entity_dict.keys():
        for val in entity_dict[k]:
            name = val['text']
            coord_dict[name] = {
                'latitude': str(random()),
                'longitude': str(random())
            }
    return coord_dict


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

def test_add_guids(resolver, name_guid_dict):
    resolver._add_guids(name_guid_dict)
    for tag in resolver._tag_view:
        assert len(tag['guids']) == 3
        for e in tag['guids']:
            assert isinstance(e, str)

def test_add_coords(resolver, coord_dict):
    resolver._add_coords(coord_dict)
    for tag in resolver._tag_view:
        assert isinstance(tag['coords'], dict)
        for e in tag['coords'].values():
            assert isinstance(e, str)

def test_has_resolved(resolver):
    assert resolver.has_resolved == False
    resolver._geo_complete = True
    assert resolver.has_resolved == False
    resolver._rm_complete = True
    assert resolver.has_resolved == True
    resolver._geo_complete = False
    assert resolver.has_resolved == False
    