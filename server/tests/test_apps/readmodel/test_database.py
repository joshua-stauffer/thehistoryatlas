import random
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4, UUID

import pytest
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.seed.readmodel import PEOPLE, SUMMARIES, PLACES, NAMES, TIMES, CITATIONS
from the_history_atlas.apps.domain.models import CoordsByName
from the_history_atlas.apps.domain.models.readmodel import (
    Source as ADMSource,
    DefaultEntity,
)
from the_history_atlas.apps.domain.models.readmodel.queries.coords_by_name import Coords
from the_history_atlas.apps.domain.models.readmodel.tables import (
    PersonModel,
    TagInstanceModel,
    NameModel,
    PlaceModel,
    TimeModel,
)
from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.schema import Place


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


def test_session(readmodel_db):
    with readmodel_db.Session() as session:
        lookup_id = UUID("1318e533-80e0-4f2b-bd08-ae7150ffee86")
        id = session.execute(
            text("select id from tags where tags.id = :id;"), {"id": lookup_id}
        ).scalar_one()
        assert id == lookup_id


def test_get_person_by_id_success(readmodel_db):
    person_id = PEOPLE[0].id

    with readmodel_db.Session() as session:
        person = readmodel_db.get_person_by_id(id=person_id, session=session)

    assert isinstance(person, PersonModel)
    assert person.id == person_id


def test_get_person_by_id_failure(readmodel_db):
    person_id = UUID("60e17edf-54ec-4212-9e3f-9f679bf70489")

    with readmodel_db.Session() as session:
        person = readmodel_db.get_person_by_id(id=person_id, session=session)

    assert person is None


def test_create_person(readmodel_db):
    person_id = UUID("6f43d599-07ca-403f-b2ca-a2126aac9e89")

    with readmodel_db.Session() as session:
        person = readmodel_db.create_person(id=person_id, session=session)
        session.commit()

    assert isinstance(person, PersonModel)

    with readmodel_db.Session() as session:
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


def test_get_place_by_id_success(readmodel_db):
    place_id = PLACES[0].id

    with readmodel_db.Session() as session:
        place = readmodel_db.get_place_by_id(id=place_id, session=session)

    assert isinstance(place, PlaceModel)
    assert place.id == place_id


def test_get_place_by_id_failure(readmodel_db):
    place_id = UUID("60e17edf-54ec-4212-9e3f-9f679bf70489")

    with readmodel_db.Session() as session:
        place = readmodel_db.get_place_by_id(id=place_id, session=session)

    assert place is None


def test_create_place(readmodel_db):
    place_model = PlaceModel(
        id=uuid4(),
        latitude=10.3456,
        longitude=45.5335,
        geoshape=None,
        geonames_id=45678,
    )

    with readmodel_db.Session() as session:
        result_model = readmodel_db.create_place(
            session=session, **place_model.dict(exclude={"extra", "type"})
        )
        session.commit()

    with readmodel_db.Session() as session:
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


def test_get_time_by_id_success(readmodel_db):
    time_id = TIMES[0].id

    with readmodel_db.Session() as session:
        time = readmodel_db.get_time_by_id(id=time_id, session=session)

    assert isinstance(time, TimeModel)
    assert time.id == time_id


def test_get_time_by_id_failure(readmodel_db):
    time_id = UUID("60e17edf-54ec-4212-9e3f-9f679bf70489")

    with readmodel_db.Session() as session:
        time = readmodel_db.get_time_by_id(id=time_id, session=session)

    assert time is None


def test_create_time(readmodel_db):
    time_model = TimeModel(
        id=uuid4(),
        time=datetime(year=1685, month=3, day=21, tzinfo=timezone.utc),
        calendar_model="http://www.wikidata.org/entity/Q1985727",
        precision=6,
    )

    with readmodel_db.Session() as session:
        result_model = readmodel_db.create_time(
            session=session, **time_model.dict(exclude={"extra", "type"})
        )
        session.commit()

    with readmodel_db.Session() as session:
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


def test_exists_tag_is_true(readmodel_db):
    tag_id = PLACES[0].id

    with readmodel_db.Session() as session:
        exists = readmodel_db.exists_tag(tag_id=tag_id, session=session)
        assert exists is True


def test_exists_tag_is_false(readmodel_db):
    tag_id = UUID("beacc9c9-a1fc-4a37-95bc-58d56291c6f5")

    with readmodel_db.Session() as session:
        exists = readmodel_db.exists_tag(tag_id=tag_id, session=session)
        assert exists is False


def test_create_tag_instance(readmodel_db):
    tag_id = PEOPLE[0].id
    summary_id = SUMMARIES[0].id
    start_char = 5
    stop_char = 10

    with readmodel_db.Session() as session:
        tag_instance = readmodel_db.create_tag_instance(
            tag_id=tag_id,
            summary_id=summary_id,
            start_char=start_char,
            stop_char=stop_char,
            session=session,
        )
        session.commit()

    assert isinstance(tag_instance, TagInstanceModel)

    with readmodel_db.Session() as session:
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


def test_get_name_success(readmodel_db):
    seed_name_model = NAMES[0]

    with readmodel_db.Session() as session:
        name_model = readmodel_db.get_name(name=seed_name_model.name, session=session)

    assert isinstance(name_model, NameModel)
    assert name_model.id == seed_name_model.id
    assert name_model.name == seed_name_model.name


def test_get_name_failure(readmodel_db):
    nonexistent_name = "supercalifragilistic expialidocious"

    with readmodel_db.Session() as session:
        name_model = readmodel_db.get_name(name=nonexistent_name, session=session)

    assert name_model is None


def test_add_name_to_tag_with_nonexistent_name(engine, readmodel_db):
    tag_id = create_tag(engine, type="PERSON")
    name = "Charlie Parker"

    with readmodel_db.Session() as session:
        readmodel_db.add_name_to_tag(tag_id=tag_id, name=name, session=session)
        session.commit()

    with readmodel_db.Session() as session:
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


def test_add_name_to_tag_with_existing_name(readmodel_db, engine):
    tag_id = create_tag(engine, type="PERSON")
    name = "Charlie Parker"
    name_id = create_name(engine, name=name)

    with readmodel_db.Session() as session:
        readmodel_db.add_name_to_tag(tag_id=tag_id, name=name, session=session)

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


def test_add_name_to_tag_errors_if_tag_is_missing(readmodel_db):
    tag_id = uuid4()
    name = "Charlie Parker"

    with readmodel_db.Session() as session:
        with pytest.raises(IntegrityError):
            readmodel_db.add_name_to_tag(tag_id=tag_id, name=name, session=session)


def test_create_citation(readmodel_db):
    id = uuid4()
    citation_text = "peter piper picked a peck of pickled peppers."
    page_num = 243
    access_date = "2022-04-19"

    with readmodel_db.Session() as session:
        readmodel_db.create_citation(
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


def test_create_citation_source_fkey(readmodel_db):
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
    with readmodel_db.Session() as session:
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

        readmodel_db.create_citation_source_fkey(
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


def test_create_citation_summary_fkey(readmodel_db):
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
    with readmodel_db.Session() as session:
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

        readmodel_db.create_citation_summary_fkey(
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


def test_get_citation_by_id_success(readmodel_db):
    citation_model = CITATIONS[0]

    with readmodel_db.Session() as session:
        citation = readmodel_db.get_citation_by_id(
            id=citation_model.id, session=session
        )

    assert citation == citation_model


def test_get_citation_by_id_failure(readmodel_db):
    nonexistent_id = UUID("fd5a0077-6d53-4af3-b622-831f031002f2")

    with readmodel_db.Session() as session:
        citation = readmodel_db.get_citation_by_id(id=nonexistent_id, session=session)

    assert citation is None


@pytest.mark.xfail(reason="test not implemented")
def test_get_citation():
    assert False, "Remove method or add test"


@pytest.mark.xfail(reason="test not implemented")
def test_get_summaries():
    assert False, "Remove method or add test"


@pytest.mark.xfail(reason="test not implemented")
def test_get_all_source_titles_and_authors():
    assert False, "Remove method or add test"


def test_get_coords_by_names(readmodel_db):
    names = ["Eisenach"]

    with readmodel_db.Session() as session:
        coords_by_name = readmodel_db.get_coords_by_names(names=names, session=session)

    assert coords_by_name == CoordsByName(
        coords={
            "Eisenach": [
                Coords(
                    latitude=10.3147,
                    longitude=50.9796,
                )
            ]
        }
    )


@pytest.mark.xfail(reason="test not implemented")
def test_create_summary():
    assert False, "Remove method or add test"


@pytest.mark.xfail(reason="test not implemented")
def test_create_name():
    assert False, "Remove method or add test"


@pytest.mark.xfail(reason="test not implemented")
def test_create_source():
    assert False, "Remove method or add test"


def test_get_citation_returns_error_with_unknown_guid(readmodel_db):
    guid = "f4cba804-b500-46c8-9f83-89749b777a40"
    res = readmodel_db.get_citation(guid)
    assert isinstance(res, dict)
    assert len(res.keys()) == 0


def test_get_summaries_returns_error_with_unknown_guid(readmodel_db):
    guid = "f4cba804-b500-46c8-9f83-89749b777a40"
    res = readmodel_db.get_summaries([guid])
    assert len(res) == 0


def test_get_manifest_by_person_returns_empty_list(readmodel_db):
    tags, timelines = readmodel_db.get_manifest_by_person(
        "f4cba804-b500-46c8-9f83-89749b777a40"
    )
    assert isinstance(timelines, list)
    assert len(timelines) == 0
    assert isinstance(tags, list)
    assert len(tags) == 0


@pytest.mark.xfail(
    raises=AssertionError, reason="data seems to be missing", strict=True
)
def test_get_manifest_by_person(readmodel_db):
    person_guids = [str(person.id) for person in PEOPLE]
    for guid in person_guids:
        manifest_res, timeline_res = readmodel_db.get_manifest_by_person(guid)
        assert isinstance(manifest_res, list)
        assert all(isinstance(e, str) for e in manifest_res)
        assert len(manifest_res) > 0
        assert isinstance(timeline_res, list)
        for res in timeline_res:
            assert isinstance(res, dict)
            assert isinstance(res["count"], int)
            assert isinstance(res["root_id"], str)
            assert isinstance(res["year"], int)


@pytest.mark.xfail(
    raises=AssertionError, reason="data seems to be missing", strict=True
)
def test_get_manifest_by_place(readmodel_db):
    place_guids = [str(person.id) for person in PEOPLE]
    for guid in place_guids:
        manifest_res, timeline_res = readmodel_db.get_manifest_by_place(guid)
        assert isinstance(manifest_res, list)
        assert all(isinstance(e, str) for e in manifest_res)
        assert len(manifest_res) > 0
        assert isinstance(timeline_res, list)
        for res in timeline_res:
            assert isinstance(res, dict)
            assert isinstance(res["count"], int)
            assert isinstance(res["root_id"], str)
            assert isinstance(res["year"], int)


@pytest.mark.xfail(
    raises=AssertionError, reason="data seems to be missing", strict=True
)
def test_get_manifest_by_time(readmodel_db):
    time_guids = [str(time.id) for time in TIMES]
    for guid in time_guids:
        manifest_res, timeline_res = readmodel_db.get_manifest_by_time(guid)
        assert isinstance(manifest_res, list)
        assert all(isinstance(e, str) for e in manifest_res)
        assert len(manifest_res) > 0
        assert isinstance(timeline_res, list)
        for res in timeline_res:
            assert isinstance(res, dict)
            assert isinstance(res["count"], int)
            assert isinstance(res["root_id"], str)
            assert isinstance(res["year"], int)


def test_get_guids_by_name(readmodel_db):
    name = NAMES[0].name
    res = readmodel_db.get_guids_by_name(name)
    assert len(res) == 1


def test_get_guids_by_name_returns_empty(readmodel_db):
    res = readmodel_db.get_guids_by_name("This name doesnt exist")
    assert isinstance(res, list)
    assert len(res) == 0


def test_get_entity_summary_by_guid_batch_returns_empty(readmodel_db):
    res = readmodel_db.get_entity_summary_by_guid_batch([])
    assert isinstance(res, list)
    assert len(res) == 0


def test_get_entity_summary_by_guid_batch(readmodel_db):
    time_guids = [str(time.id) for time in TIMES]
    person_guids = [str(person.id) for person in PEOPLE]
    place_guids = [str(place.id) for place in PLACES]
    combined_guids = [*time_guids, *place_guids, *person_guids]
    res = readmodel_db.get_entity_summary_by_guid_batch(combined_guids)
    assert isinstance(res, list)
    assert len(res) == len(combined_guids)
    for summary in res:
        assert isinstance(summary, dict)
        guid = summary["id"]
        assert isinstance(guid, str)
        if summary["type"] == "TIME":
            assert guid in time_guids
        elif summary["type"] == "PLACE":
            assert guid in place_guids
        elif summary["type"] == "PERSON":
            assert guid in person_guids
        else:
            assert False  # Summary type had an unexpected value
        assert summary["citation_count"] > 0
        assert isinstance(summary["names"], list)
        for name in summary["names"]:
            assert isinstance(name, str)
        assert isinstance(summary["first_citation_date"], str)
        assert isinstance(summary["last_citation_date"], str)
        assert summary["first_citation_date"] <= summary["last_citation_date"]


def test_get_all_entity_names(readmodel_db):
    res = readmodel_db.get_all_entity_names()
    assert len(res) > 0
    assert isinstance(res, list)
    for tup in res:
        assert isinstance(tup, tuple)
        name, guid = tup
        assert isinstance(name, str)
        assert isinstance(guid, UUID)


@pytest.mark.xfail(reason="UUID provided to TrieResult.guids instead of string")
def test_get_name_by_fuzzy_search(readmodel_db):
    res1 = readmodel_db.get_name_by_fuzzy_search("A person name")
    assert isinstance(res1, list)
    assert len(res1) <= 10


@pytest.mark.xfail(reason="finish test")
def test_get_sources_by_search_term_title(readmodel_db, source_title):

    sources = readmodel_db.get_sources_by_search_term(source_title)

    with readmodel_db.Session() as session:
        sql = text(
            """
            
        """
        )


def test_get_place_by_coords(readmodel_db):
    """Cover successful path - coordinates are found"""
    # find a set of coordinates to query
    place_guid = str(PLACES[0].id)
    with readmodel_db.Session() as session:
        res = session.execute(select(Place).where(Place.id == place_guid)).scalar_one()
        latitude = res.latitude
        longitude = res.longitude

    guid = readmodel_db.get_place_by_coords(latitude=latitude, longitude=longitude)
    assert guid == UUID(place_guid)


def test_get_place_by_coords_with_new_coords(readmodel_db):
    """Cover failed path -- no coordinates are found"""
    # coords are set by random.random(), which is less than one.
    latitude = 1 + random.random()
    longitude = 1 - random.random()

    guid = readmodel_db.get_place_by_coords(latitude=latitude, longitude=longitude)
    assert guid is None


def test_get_default_entity(readmodel_db):
    entity = readmodel_db.get_default_entity()
    assert isinstance(entity, DefaultEntity)
