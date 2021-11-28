import pytest
from uuid import uuid4
from app.state_manager.trie import Trie, Node

@pytest.fixture
def entity_tuples():
    return [
        ('aa', '84a03b1b-be16-4c39-85b5-65db589f7980'),
        ('aa', '671ce5f2-9224-4444-a6d2-f873c2cf5d9e'),
        ('ab', 'de6d9ea9-9478-4759-8a12-03d6fcab7b1f'),
        ('abc', 'd8f8f057-785f-4a9a-8a27-1add7abb6230'),
        ('bb', '933ef06a-9c5d-41fa-be95-c9b01e453934'),
        ('cb', '82cce8e8-0a17-4084-9016-09960a7905b')
    ]

@pytest.fixture
def trie(entity_tuples):
    return Trie(entity_tuples)
    
def test_build(trie):
    assert isinstance(trie.root, Node)
    root = trie.root
    assert len(root.children) == 3

def test_find_with_single_match(trie):
    res = trie.find('ab')
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0] == {
        'name': 'ab', 
        'guids': [
            'de6d9ea9-9478-4759-8a12-03d6fcab7b1f',
        ]
    }

def test_find_with_multiple_match(trie):
    res = trie.find('aa')
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]['name'] == 'aa'
    assert set(res[0]['guids']) == set([
            '84a03b1b-be16-4c39-85b5-65db589f7980',
            '671ce5f2-9224-4444-a6d2-f873c2cf5d9e',
        ])

def test_fuzzy_match(trie):
    res = trie.find(string='a', res_count=5)
    assert len(res) == 3

def test_limit_res_count(trie):
    res = trie.find(string='a', res_count=2)
    assert len(res) == 2

def test_delete(trie):    
    assert len(trie.find('bb')) == 1
    trie.delete('bb', '933ef06a-9c5d-41fa-be95-c9b01e453934')
    assert len(trie.find('bb')) == 0

def test_insert(trie: Trie):
    my_guid = str(uuid4())
    trie.insert(
        string='aaz',
        guid=my_guid
    )
    node = trie.root.children['a'].children['a'].children['z']
    assert len(node.ids) == 1
    assert my_guid in node.ids