from typing import Literal
from uuid import uuid4, UUID

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.errors import MissingResourceError


def create_tag(engine, type: Literal["PERSON", "PLACE", "TIME"]) -> UUID:
    with Session(engine, future=True) as session:
        tag_id = uuid4()
        stmt = """
            insert into tags (id, type)
                values (:id, :type)
        """
        session.execute(text(stmt), {"id": tag_id, "type": type})
        session.commit()

    return tag_id


def create_name(engine, name: str) -> UUID:
    with Session(engine, future=True) as session:
        name_id = uuid4()
        stmt = """
            insert into names (id, name)
                values (:id, :name)
        """
        session.execute(text(stmt), {"id": name_id, "name": name})
        session.commit()
    return name_id


def test_add_name_to_tag_with_nonexistent_name(engine):
    db = Database(database_client=engine, stm_timeout=0)
    tag_id = create_tag(engine, type="PERSON")
    name = "Charlie Parker"

    db.add_name_to_tag(tag_id=tag_id, name=name)

    stmt = """
        select names.name
        from tag_name_assoc join names on tag_name_assoc.name_id = names.id
        where tag_name_assoc.tag_id = :tag_id;
    """
    with Session(engine, future=True) as session:
        name_res = session.execute(text(stmt), {"tag_id": tag_id}).scalar_one()
        assert name_res == name

    # cleanup
    with Session(engine, future=True) as session:
        stmt = """
            delete from tag_name_assoc where tag_name_assoc.tag_id = :tag_id;
            delete from tags where tags.id = :tag_id;
            delete from names where names.name = :name
        """
        session.execute(text(stmt), {"tag_id": tag_id, "name": name})
        session.commit()


def test_add_name_to_tag_with_existing_name(engine):
    db = Database(database_client=engine, stm_timeout=0)
    tag_id = create_tag(engine, type="PERSON")
    name = "Charlie Parker"
    name_id = create_name(engine, name=name)

    db.add_name_to_tag(tag_id=tag_id, name=name)

    stmt = """
        select names.id
        from tag_name_assoc join names on tag_name_assoc.name_id = names.id
        where tag_name_assoc.tag_id = :tag_id;
    """
    with Session(engine, future=True) as session:
        name_res = session.execute(text(stmt), {"tag_id": tag_id}).scalar_one()
        assert name_res == name_id

    # cleanup
    with Session(engine, future=True) as session:
        stmt = """
            delete from tag_name_assoc where tag_name_assoc.tag_id = :tag_id;
            delete from tags where tags.id = :tag_id;
            delete from names where names.name = :name
        """
        session.execute(text(stmt), {"tag_id": tag_id, "name": name})
        session.commit()


def test_add_name_to_tag_errors_if_tag_is_missing(engine):
    db = Database(database_client=engine, stm_timeout=0)
    tag_id = uuid4()
    name = "Charlie Parker"

    with pytest.raises(MissingResourceError):
        db.add_name_to_tag(tag_id=tag_id, name=name)
