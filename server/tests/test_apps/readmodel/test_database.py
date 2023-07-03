from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4, UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.seed.readmodel import PEOPLE, SUMMARIES, PLACES, NAMES, TIMES, CITATIONS
from the_history_atlas.apps.domain.models.readmodel.tables import (
    PersonModel,
    TagInstanceModel,
    NameModel,
    PlaceModel,
    TimeModel,
    CitationModel,
)
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


def test_session(engine):
    db = Database(database_client=engine)
    with db.Session() as session:
        lookup_id = UUID("1318e533-80e0-4f2b-bd08-ae7150ffee86")
        id = session.execute(
            text("select id from tags where tags.id = :id;"), {"id": lookup_id}
        ).scalar_one()
        assert id == lookup_id


def test_get_person_by_id_success(engine):
    person_id = PEOPLE[0].id
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        person = db.get_person_by_id(id=person_id, session=session)

    assert isinstance(person, PersonModel)
    assert person.id == person_id


def test_get_person_by_id_failure(engine):
    person_id = UUID("60e17edf-54ec-4212-9e3f-9f679bf70489")
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        person = db.get_person_by_id(id=person_id, session=session)

    assert person is None


def test_create_person(engine):
    person_id = UUID("6f43d599-07ca-403f-b2ca-a2126aac9e89")
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        person = db.create_person(id=person_id, session=session)
        session.commit()

    assert isinstance(person, PersonModel)

    with Session(engine, future=True) as session:
        res_id = session.execute(
            text("select (id) from person where person.id = :id"),
            {"id": person_id},
        ).scalar_one()
        assert res_id == person_id

        # cleanup
        session.execute(
            text(
                """
                delete from person where person.id = :id
                """
            ),
            {"id": person_id},
        )
        session.commit()


def test_get_place_by_id_success(engine):
    place_id = PLACES[0].id
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        place = db.get_place_by_id(id=place_id, session=session)

    assert isinstance(place, PlaceModel)
    assert place.id == place_id


def test_get_place_by_id_failure(engine):
    place_id = UUID("60e17edf-54ec-4212-9e3f-9f679bf70489")

    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        place = db.get_place_by_id(id=place_id, session=session)

    assert place is None


def test_create_place(engine):
    place_model = PlaceModel(
        id=uuid4(),
        latitude=10.3456,
        longitude=45.5335,
        geoshape=None,
        geonames_id=45678,
    )
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        result_model = db.create_place(
            session=session, **place_model.dict(exclude={"extra", "type"})
        )
        session.commit()

    with Session(engine, future=True) as session:
        stmt = """
            select id, latitude, longitude, geoshape, geonames_id 
            from place where place.id = :id
        """
        res = session.execute(text(stmt), {"id": place_model.id}).one()
        db_model = PlaceModel(
            id=res[0],
            latitude=res[1],
            longitude=res[2],
            geoshape=res[3],
            geonames_id=res[4],
        )
        assert place_model == result_model == db_model

        # cleanup
        delete_stmt = """
            delete from place where place.id = :id;
            delete from tags where tags.id = :id;
        """
        session.execute(
            text(delete_stmt),
            {"id": place_model.id},
        )


def test_get_time_by_id_success(engine):
    time_id = TIMES[0].id
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        time = db.get_time_by_id(id=time_id, session=session)

    assert isinstance(time, TimeModel)
    assert time.id == time_id


def test_get_time_by_id_failure(engine):
    time_id = UUID("60e17edf-54ec-4212-9e3f-9f679bf70489")
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        time = db.get_time_by_id(id=time_id, session=session)

    assert time is None


def test_create_time(engine):
    time_model = TimeModel(
        id=uuid4(),
        time=datetime(year=1685, month=3, day=21, tzinfo=timezone.utc),
        calendar_model="http://www.wikidata.org/entity/Q1985727",
        precision=6,
    )
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        result_model = db.create_time(
            session=session, **time_model.dict(exclude={"extra", "type"})
        )
        session.commit()

    with Session(engine, future=True) as session:
        stmt = """
            select id, time, calendar_model, precision 
            from time where time.id = :id
        """
        res = session.execute(text(stmt), {"id": time_model.id}).one()
        db_model = TimeModel(
            id=res[0],
            time=res[1],
            calendar_model=res[2],
            precision=res[3],
        )
        assert time_model == result_model == db_model

        # cleanup
        delete_stmt = """
            delete from time where time.id = :id;
            delete from tags where tags.id = :id;
        """
        session.execute(
            text(delete_stmt),
            {"id": time_model.id},
        )


def test_exists_tag_is_true(engine):
    tag_id = PLACES[0].id
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        exists = db.exists_tag(tag_id=tag_id, session=session)
        assert exists is True


def test_exists_tag_is_false(engine):
    tag_id = UUID("beacc9c9-a1fc-4a37-95bc-58d56291c6f5")
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        exists = db.exists_tag(tag_id=tag_id, session=session)
        assert exists is False


def test_create_tag_instance(engine):
    tag_id = PEOPLE[0].id
    summary_id = SUMMARIES[0].id
    start_char = 5
    stop_char = 10
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        tag_instance = db.create_tag_instance(
            tag_id=tag_id,
            summary_id=summary_id,
            start_char=start_char,
            stop_char=stop_char,
            session=session,
        )
        session.commit()

    assert isinstance(tag_instance, TagInstanceModel)

    with Session(engine, future=True) as session:
        stmt = """
            select id, tag_id, summary_id, start_char, stop_char
            from taginstances where taginstances.id = :id;
        """
        res = session.execute(text(stmt), {"id": tag_instance.id}).one()
        assert res[0] == tag_instance.id
        assert res[1] == tag_instance.tag_id == tag_id
        assert res[2] == tag_instance.summary_id == summary_id
        assert res[3] == tag_instance.start_char == start_char
        assert res[4] == tag_instance.stop_char == stop_char

        # cleanup
        session.execute(
            text("delete from taginstances where taginstances.id = :id"),
            {"id": tag_instance.id},
        )
        session.commit()


def test_get_name_success(engine):
    seed_name_model = NAMES[0]
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        name_model = db.get_name(name=seed_name_model.name, session=session)

    assert isinstance(name_model, NameModel)
    assert name_model.id == seed_name_model.id
    assert name_model.name == seed_name_model.name


def test_get_name_failure(engine):
    nonexistent_name = "supercalifragilistic expialidocious"
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        name_model = db.get_name(name=nonexistent_name, session=session)

    assert name_model is None


def test_add_name_to_tag_with_nonexistent_name(engine, DBSession):
    db = Database(database_client=engine)
    tag_id = create_tag(engine, type="PERSON")
    name = "Charlie Parker"

    with DBSession() as session:
        db.add_name_to_tag(tag_id=tag_id, name=name, session=session)
        session.commit()

    with DBSession() as session:
        stmt = text(
            """
            select names.name
            from tag_name_assoc join names on tag_name_assoc.name_id = names.id
            where tag_name_assoc.tag_id = :tag_id;
        """
        )
        name_res = session.execute(stmt, {"tag_id": tag_id}).scalar_one()
        assert name_res == name

        stmt = """
            delete from tag_name_assoc where tag_name_assoc.tag_id = :tag_id;
            delete from tags where tags.id = :tag_id;
            delete from names where names.name = :name
        """
        session.execute(text(stmt), {"tag_id": tag_id, "name": name})
        session.commit()


def test_add_name_to_tag_with_existing_name(engine, DBSession):
    db = Database(database_client=engine)
    tag_id = create_tag(engine, type="PERSON")
    name = "Charlie Parker"
    name_id = create_name(engine, name=name)

    with DBSession() as session:
        db.add_name_to_tag(tag_id=tag_id, name=name, session=session)

        stmt = text(
            """
            select names.id
            from tag_name_assoc join names on tag_name_assoc.name_id = names.id
            where tag_name_assoc.tag_id = :tag_id;
        """
        )
        name_res = session.execute(stmt, {"tag_id": tag_id}).scalar_one()
        assert name_res == name_id

        # cleanup
        stmt = """
            delete from tag_name_assoc where tag_name_assoc.tag_id = :tag_id;
            delete from tags where tags.id = :tag_id;
            delete from names where names.name = :name
        """
        session.execute(text(stmt), {"tag_id": tag_id, "name": name})
        session.commit()


def test_add_name_to_tag_errors_if_tag_is_missing(engine, DBSession):
    db = Database(database_client=engine)
    tag_id = uuid4()
    name = "Charlie Parker"

    with DBSession() as session:
        with pytest.raises(IntegrityError):
            db.add_name_to_tag(tag_id=tag_id, name=name, session=session)


def test_create_citation(engine):
    db = Database(database_client=engine)
    id = uuid4()
    citation_text = "peter piper picked a peck of pickled peppers."
    page_num = 243
    access_date = "2022-04-19"

    with Session(engine, future=True) as session:
        db.create_citation(
            session=session,
            id=id,
            citation_text=citation_text,
            page_num=page_num,
            access_date=access_date,
        )
        session.commit()

        stmt = """
            select id, text, page_num, access_date
            from citations where citations.id = :id
        """
        res = session.execute(text(stmt), {"id": id}).one()
        assert res[0] == id
        assert res[1] == citation_text
        assert res[2] == page_num
        assert res[3] == access_date

        # cleanup
        session.execute(
            text("delete from citations where citations.id = :id"), {"id": id}
        )
        session.commit()


def test_create_citation_source_fkey(engine):
    citation_id = uuid4()
    citation_text = "eenie meanie miney moe"
    source_id = uuid4()
    title = "title"
    author = "author"
    publisher = "publisher"
    pub_date = "2022-03-03"
    kwargs = "{}"
    stmt = """
        insert into citations (id, text)
            values (:citation_id, :citation_text);
        insert into sources (id, title, author, publisher, pub_date, kwargs)
            values (:source_id, :title, :author, :publisher, :pub_date, :kwargs);
    """
    with Session(engine, future=True) as session:
        session.execute(
            text(stmt),
            {
                "citation_id": citation_id,
                "source_id": source_id,
                "citation_text": citation_text,
                "title": title,
                "author": author,
                "publisher": publisher,
                "pub_date": pub_date,
                "kwargs": kwargs,
            },
        )
        session.commit()
        db = Database(database_client=engine)

        db.create_citation_source_fkey(
            citation_id=citation_id, source_id=source_id, session=session
        )
        session.commit()

        res_source_id = session.execute(
            text("select source_id from citations where citations.id = :id;"),
            {"id": citation_id},
        ).scalar_one()
        assert res_source_id == source_id

        # cleanup
        session.execute(
            text(
                """
                delete from citations where citations.id = :citation_id;
                delete from sources where sources.id = :source_id
                """
            ),
            {"citation_id": citation_id, "source_id": source_id},
        )
        session.commit()


def test_create_citation_summary_fkey(engine):
    citation_id = uuid4()
    citation_text = "eenie meanie miney moe"
    summary_id = uuid4()
    summary_text = "catch a tiger"

    stmt = """
        insert into citations (id, text)
            values (:citation_id, :citation_text);
        insert into summaries (id, text)
            values (:summary_id, :summary_text);
    """
    with Session(engine, future=True) as session:
        session.execute(
            text(stmt),
            {
                "citation_id": citation_id,
                "summary_id": summary_id,
                "citation_text": citation_text,
                "summary_text": summary_text,
            },
        )
        session.commit()
        db = Database(database_client=engine)

        db.create_citation_summary_fkey(
            citation_id=citation_id, summary_id=summary_id, session=session
        )
        session.commit()

        res_summary_id = session.execute(
            text("select summary_id from citations where citations.id = :id;"),
            {"id": citation_id},
        ).scalar_one()
        assert res_summary_id == summary_id

        # cleanup
        session.execute(
            text(
                """
                delete from citations where citations.id = :citation_id;
                delete from summaries where summaries.id = :summary_id
                """
            ),
            {"citation_id": citation_id, "summary_id": summary_id},
        )
        session.commit()


def test_get_citation_by_id_success(engine):
    citation_model = CITATIONS[0]
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        citation = db.get_citation_by_id(id=citation_model.id, session=session)

    assert citation == citation_model


def test_get_citation_by_id_failure(engine):
    nonexistent_id = UUID("fd5a0077-6d53-4af3-b622-831f031002f2")
    db = Database(database_client=engine)

    with Session(engine, future=True) as session:
        citation = db.get_citation_by_id(id=nonexistent_id, session=session)

    assert citation is None


def test_add_source_to_citation(engine, DBSession):
    # setup resources
    stmt = """
        insert into sources 
            (id, title, author, publisher, pub_date, kwargs)
        values (:source_id, :title, :author, :publisher, :pub_date, :kwargs);
        insert into citations
            (id, text, page_num, access_date)
        values (:citation_id, :text, :page_num, :access_date);
    """
    source_id = uuid4()
    citation_id = uuid4()
    vars = {
        "source_id": source_id,
        "citation_id": citation_id,
        "title": "title",
        "author": "author",
        "publisher": "publisher",
        "pub_date": "2022-01-01",
        "kwargs": "{}",
        "text": "text",
        "page_num": 47,
        "access_date": "2022-01-01",
    }
    with DBSession() as session:
        session.execute(text(stmt), vars)
        session.commit()
    db = Database(database_client=engine)

    with DBSession() as session:
        db.add_source_to_citation(
            source_id=source_id, citation_id=citation_id, session=session
        )
        session.commit()

    with DBSession() as session:
        stmt = text("select source_id from citations where citations.id = :id")
        ret_source_id = session.execute(stmt, {"id": citation_id}).scalar_one()
        assert ret_source_id == source_id

        stmt = text(
            """
            delete from citations where citations.id = :citation_id;
            delete from sources where sources.id = :source_id;
        """
        )
        session.execute(stmt, {"source_id": source_id, "citation_id": citation_id})
