import asyncio
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from the_history_atlas.apps.writemodel.state_manager.schema import CitationHash, GUID


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


def test_check_citation_for_uniqueness(writemodel_db, hash, guid):
    # returns none if table is empty
    res1 = writemodel_db.check_citation_for_uniqueness(hash)
    assert res1 == None
    # add something and make sure it's there
    with Session(writemodel_db._engine, future=True) as sess, sess.begin():
        sess.add(CitationHash(hash=hash, GUID=guid))
    res2 = writemodel_db.check_citation_for_uniqueness(hash)
    assert res2 == guid


@pytest.mark.xfail("unexpected extra row in db")
def test_add_citation_hash(writemodel_db, hash, guid):
    writemodel_db.add_citation_hash(hash, guid)
    # retrieve it manually
    with Session(writemodel_db._engine, future=True) as sess:
        result = sess.execute(
            select(CitationHash).where(CitationHash.hash == hash)
        ).scalar_one_or_none()
        assert result != None
        assert result.id == 1  # nothing else is in this database
        assert result.hash == hash
        assert result.GUID == guid


def test_check_guid_for_uniqueness(writemodel_db, value, type):
    # returns none if table is empty
    res1 = writemodel_db.check_id_for_uniqueness(value)
    assert res1 == None
    # add something and make sure it's there
    with Session(writemodel_db._engine, future=True) as sess, sess.begin():
        sess.add(GUID(value=value, type=type))
    res2 = writemodel_db.check_id_for_uniqueness(value)
    assert res2 == type


@pytest.mark.asyncio
async def test_citation_short_term_memory(writemodel_db):
    writemodel_db.add_to_stm(key="a2c4e", value="it worked!")
    assert writemodel_db._Database__short_term_memory.get("a2c4e") == "it worked!"
    res = writemodel_db.check_citation_for_uniqueness(text_hash="a2c4e")
    assert res == "it worked!"
    await asyncio.sleep(0.000001)
    res = writemodel_db.check_citation_for_uniqueness(text_hash="a2c4e")
    assert res == None


@pytest.mark.asyncio
async def test_guid_short_term_memory(writemodel_db):
    writemodel_db.add_to_stm(key="a2c4e", value="it worked!")
    assert writemodel_db._Database__short_term_memory.get("a2c4e") == "it worked!"
    res = writemodel_db.check_id_for_uniqueness(id_="a2c4e")
    assert res == "it worked!"
    await asyncio.sleep(0.000001)
    res = writemodel_db.check_id_for_uniqueness(id_="a2c4e")
    assert res == None
