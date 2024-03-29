import asyncio
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from writemodel.state_manager.database import Database
from writemodel.state_manager.schema import CitationHash, GUID


@pytest.fixture
def hash():
    return "a2c4e6g"


@pytest.fixture
def guid():
    return "some-unique-guid"


@pytest.fixture
def value():
    return "a-123-guid!"


@pytest.fixture
def type():
    return "ANIMAL"


def test_check_citation_for_uniqueness(db, hash, guid):
    # returns none if table is empty
    res1 = db.check_citation_for_uniqueness(hash)
    assert res1 == None
    # add something and make sure it's there
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(CitationHash(hash=hash, GUID=guid))
    res2 = db.check_citation_for_uniqueness(hash)
    assert res2 == guid


def test_add_citation_hash(db, hash, guid):
    db.add_citation_hash(hash, guid)
    # retrieve it manually
    with Session(db._engine, future=True) as sess:
        result = sess.execute(
            select(CitationHash).where(CitationHash.hash == hash)
        ).scalar_one_or_none()
        assert result != None
        assert result.id == 1  # nothing else is in this database
        assert result.hash == hash
        assert result.GUID == guid


def test_check_guid_for_uniqueness(db, value, type):
    # returns none if table is empty
    res1 = db.check_id_for_uniqueness(value)
    assert res1 == None
    # add something and make sure it's there
    with Session(db._engine, future=True) as sess, sess.begin():
        sess.add(GUID(value=value, type=type))
    res2 = db.check_id_for_uniqueness(value)
    assert res2 == type


@pytest.mark.asyncio
async def test_citation_short_term_memory(db):
    db.add_to_stm(key="a2c4e", value="it worked!")
    assert db._Database__short_term_memory.get("a2c4e") == "it worked!"
    res = db.check_citation_for_uniqueness(text_hash="a2c4e")
    assert res == "it worked!"
    await asyncio.sleep(0.000001)
    res = db.check_citation_for_uniqueness(text_hash="a2c4e")
    assert res == None


@pytest.mark.asyncio
async def test_guid_short_term_memory(db):
    db.add_to_stm(key="a2c4e", value="it worked!")
    assert db._Database__short_term_memory.get("a2c4e") == "it worked!"
    res = db.check_id_for_uniqueness(id_="a2c4e")
    assert res == "it worked!"
    await asyncio.sleep(0.000001)
    res = db.check_id_for_uniqueness(id_="a2c4e")
    assert res == None
