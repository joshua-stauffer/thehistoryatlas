from datetime import datetime, timezone, timedelta
from typing import Literal, Callable
from uuid import uuid4, UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.db_builder import DBBuilder
from tests.seed.names import NAMES
from tests.seed.people import PEOPLE
from tests.seed.summaries import SUMMARIES
from the_history_atlas.apps.domain.models.history.tables import (
    PersonModel,
    TagInstanceModel,
    NameModel,
    PlaceModel,
    TimeModel,
)
from the_history_atlas.apps.history.repository import Repository
from the_history_atlas.apps.history.trie import Trie


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


def test_create_person(history_db, cleanup_tag: Callable[[UUID], None]):
    person_id = UUID("6f43d599-07ca-403f-b2ca-a2126aac9e89")
    wikidata_id = "Q1339"
    wikidata_url = "https://www.wikidata.org/wiki/Q1339"
    cleanup_tag(person_id)
    with history_db.Session() as session:
        person = history_db.create_person(
            id=person_id,
            session=session,
            wikidata_id=wikidata_id,
            wikidata_url=wikidata_url,
        )
        session.commit()

    assert isinstance(person, PersonModel)

    with history_db.Session() as session:
        person_query = text(
            """
                select p.id, t.wikidata_id, t.wikidata_url
                from people p
                inner join tags t on p.id = t.id
                where p.id = :id;
            """
        )
        row = session.execute(
            person_query,
            {"id": person_id},
        ).one()
        assert row.id == person_id
        assert row.wikidata_id == wikidata_id
        assert row.wikidata_url == wikidata_url


def test_create_place(history_db):
    place_model = PlaceModel(
        id=uuid4(),
        latitude=10.3456,
        longitude=45.5335,
        geoshape=None,
    )

    with history_db.Session() as session:
        result_model = history_db.create_place(
            session=session, **place_model.dict(exclude={"extra", "type"})
        )
        session.commit()

    with history_db.Session() as session:
        stmt = """
            select id, latitude, longitude, geoshape
            from places where places.id = :id
        """
        res = session.execute(text(stmt), {"id": place_model.id}).one()
        db_model = PlaceModel(
            id=res[0],
            latitude=res[1],
            longitude=res[2],
            geoshape=res[3],
        )
        assert place_model == result_model == db_model

        # cleanup
        delete_stmt = """
            delete from places where places.id = :id;
            delete from tags where tags.id = :id;
        """
        session.execute(
            text(delete_stmt),
            {"id": place_model.id},
        )


def test_create_time(history_db):
    time_model = TimeModel(
        id=uuid4(),
        datetime="+1685-03-21T00:00:00Z",
        calendar_model="http://www.wikidata.org/entity/Q1985727",
        precision=6,
    )

    with history_db.Session() as session:
        result_model = history_db.create_time(
            session=session, **time_model.model_dump(exclude={"extra", "type"})
        )
        session.commit()

    with history_db.Session() as session:
        stmt = """
            select id, datetime, calendar_model, precision 
            from times where times.id = :id
        """
        res = session.execute(text(stmt), {"id": time_model.id}).one()
        db_model = TimeModel(
            id=res[0],
            datetime=res[1],
            calendar_model=res[2],
            precision=res[3],
        )
        assert time_model == result_model == db_model

        # cleanup
        delete_stmt = """
            delete from times where times.id = :id;
            delete from tags where tags.id = :id;
        """
        session.execute(
            text(delete_stmt),
            {"id": time_model.id},
        )


def test_create_tag_instance(history_db):
    # arrange
    tag_id = PEOPLE[0].id
    summary_id = SUMMARIES[0].id
    start_char = 5
    stop_char = 10

    with history_db.Session() as session:
        db_builder = DBBuilder(session=session)
        db_builder.insert_people(people=PEOPLE)
        db_builder.insert_summaries(summaries=SUMMARIES)

        # act
        tag_instance = history_db.create_tag_instance(
            tag_id=tag_id,
            summary_id=summary_id,
            start_char=start_char,
            stop_char=stop_char,
            session=session,
            tag_instance_time=datetime.now(timezone.utc),
            time_precision=9,
            after=[],
        )
        session.commit()

    assert isinstance(tag_instance, TagInstanceModel)

    with history_db.Session() as session:
        stmt = """
            select id, tag_id, summary_id, start_char, stop_char
            from tag_instances where tag_instances.id = :id;
        """
        res = session.execute(text(stmt), {"id": tag_instance.id}).one()
        assert res[0] == tag_instance.id
        assert res[1] == tag_instance.tag_id == tag_id
        assert res[2] == tag_instance.summary_id == summary_id
        assert res[3] == tag_instance.start_char == start_char
        assert res[4] == tag_instance.stop_char == stop_char

        # cleanup
        session.execute(
            text("delete from tag_instances where tag_instances.id = :id"),
            {"id": tag_instance.id},
        )
        session.commit()


def test_get_name_success(history_db):
    seed_name_model = NAMES[0]

    with history_db.Session() as session:
        db_builder = DBBuilder(session=session)
        db_builder.insert_names(names=NAMES)
        name_model = history_db.get_name(name=seed_name_model.name, session=session)

    assert isinstance(name_model, NameModel)
    assert name_model.id == seed_name_model.id
    assert name_model.name == seed_name_model.name


def test_get_name_failure(history_db):
    nonexistent_name = "supercalifragilistic expialidocious"

    with history_db.Session() as session:
        name_model = history_db.get_name(name=nonexistent_name, session=session)

    assert name_model is None


def test_add_name_to_tag_with_nonexistent_name(engine, history_db):
    tag_id = create_tag(engine, type="PERSON")
    name = "Charlie Parker"

    with history_db.Session() as session:
        history_db.add_name_to_tag(tag_id=tag_id, name=name, session=session)
        session.commit()

    with history_db.Session() as session:
        stmt = text(
            """
            select names.name
            from tag_names join names on tag_names.name_id = names.id
            where tag_names.tag_id = :tag_id;
        """
        )
        name_res = session.execute(stmt, {"tag_id": tag_id}).scalar_one()
        assert name_res == name

        stmt = """
            delete from tag_names where tag_names.tag_id = :tag_id;
            delete from tags where tags.id = :tag_id;
            delete from names where names.name = :name
        """
        session.execute(text(stmt), {"tag_id": tag_id, "name": name})
        session.commit()


def test_add_name_to_tag_with_existing_name(history_db, engine):
    tag_id = create_tag(engine, type="PERSON")
    name = "Charlie Parker"
    name_id = create_name(engine, name=name)

    with history_db.Session() as session:
        history_db.add_name_to_tag(tag_id=tag_id, name=name, session=session)

        stmt = text(
            """
            select names.id
            from tag_names join names on tag_names.name_id = names.id
            where tag_names.tag_id = :tag_id;
        """
        )
        name_res = session.execute(stmt, {"tag_id": tag_id}).scalar_one()
        assert name_res == name_id

        # cleanup
        stmt = """
            delete from tag_names where tag_names.tag_id = :tag_id;
            delete from tags where tags.id = :tag_id;
            delete from names where names.name = :name
        """
        session.execute(text(stmt), {"tag_id": tag_id, "name": name})
        session.commit()


def test_add_name_to_tag_errors_if_tag_is_missing(history_db):
    tag_id = uuid4()
    name = "Charlie Parker"

    with history_db.Session() as session:
        with pytest.raises(IntegrityError):
            history_db.add_name_to_tag(tag_id=tag_id, name=name, session=session)


def test_create_citation(history_db):
    id = uuid4()
    citation_text = "peter piper picked a peck of pickled peppers."
    page_num = 243
    access_date = "2022-04-19"

    with history_db.Session() as session:
        history_db.create_citation(
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


def test_create_citation_source_fkey(history_db):
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
    with history_db.Session() as session:
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

        history_db.create_citation_source_fkey(
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


def test_create_citation_summary_fkey(history_db):
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
    with history_db.Session() as session:
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

        history_db.create_citation_summary_fkey(
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


def test_get_name_by_fuzzy_search(history_db):
    res1 = history_db.get_name_by_fuzzy_search("A person name")
    assert isinstance(res1, list)
    assert len(res1) <= 10


from datetime import datetime, timezone
from sqlalchemy.orm import Session


class TestTimeExists:
    def test_success(self, history_db, engine):
        test_time = datetime(2024, 3, 14, tzinfo=timezone.utc)
        test_calendar = "gregorian"
        test_precision = 11  # DAY precision

        # Create a test time entry using the engine directly
        time_id = create_tag(engine, "TIME")

        with history_db.Session() as session:
            # Insert the time data
            stmt = """
                insert into times (id, datetime, calendar_model, precision)
                values (:id, :datetime, :calendar_model, :precision)
            """
            session.execute(
                text(stmt),
                {
                    "id": time_id,
                    "datetime": str(test_time),  # Convert to string for storage
                    "calendar_model": test_calendar,
                    "precision": test_precision,
                },
            )
            session.commit()

            # Test the repository method directly
            id_result = history_db.time_exists(
                datetime=str(test_time),
                calendar_model=test_calendar,
                precision=test_precision,
                session=session,
            )
            assert id_result == time_id

            # Clean up
            cleanup_stmt = """
                delete from times where times.id = :id;
                delete from tags where tags.id = :id;
            """
            session.execute(text(cleanup_stmt), {"id": time_id})
            session.commit()

    def test_failure(self, history_db):
        test_calendar = "gregorian"
        test_precision = 11  # DAY precision
        non_existing_time = datetime(2023, 3, 14, tzinfo=timezone.utc)

        with history_db.Session() as session:
            # Test for a non-existent time
            id_result = history_db.time_exists(
                datetime=str(non_existing_time),
                calendar_model=test_calendar,
                precision=test_precision,
                session=session,
            )
            assert id_result is None


def test_update_story_order_bulk_simple_chain(history_db):
    """Test ordering with simple linear dependencies."""
    tag_id = uuid4()
    summaries = [uuid4() for _ in range(4)]
    time_ids = []

    with history_db.Session() as session:
        # Create tag
        session.execute(
            text("INSERT INTO tags (id, type) VALUES (:id, 'PERSON')"), {"id": tag_id}
        )

        # Create summaries and their relationships
        for i, summary_id in enumerate(summaries):
            # Create summary
            session.execute(
                text("INSERT INTO summaries (id, text) VALUES (:id, :text)"),
                {"id": summary_id, "text": f"Test summary {summary_id}"},
            )

            # Create tag instance with initial story_order
            session.execute(
                text(
                    """
                    INSERT INTO tag_instances
                    (id, summary_id, tag_id, start_char, stop_char, story_order)
                    VALUES (:id, :summary_id, :tag_id, 0, 10, :story_order)
                """
                ),
                {
                    "id": uuid4(),
                    "summary_id": summary_id,
                    "tag_id": tag_id,
                    "story_order": i * 1000,  # Initial ordering
                },
            )

        # Add time information
        for i, summary_id in enumerate(summaries):
            time_id = uuid4()
            time_ids.append(time_id)
            time = datetime.now(timezone.utc) + timedelta(days=i)

            session.execute(
                text("INSERT INTO tags (id, type) VALUES (:id, 'TIME')"),
                {"id": time_id},
            )

            session.execute(
                text(
                    """
                    INSERT INTO times (id, datetime, calendar_model, precision)
                    VALUES (:id, :datetime, 'gregorian', 11)
                """
                ),
                {"id": time_id, "datetime": time},
            )

            session.execute(
                text(
                    """
                    INSERT INTO tag_instances
                    (id, summary_id, tag_id, start_char, stop_char, story_order)
                    VALUES (:id, :summary_id, :tag_id, 0, 10, :story_order)
                """
                ),
                {
                    "id": uuid4(),
                    "summary_id": summary_id,
                    "tag_id": time_id,
                    "story_order": i * 1000,  # Initial ordering
                },
            )

        session.commit()

        # Run the bulk update
        history_db.update_story_order_bulk(tag_id=tag_id, session=session)

        # Verify results
        results = session.execute(
            text(
                """
                SELECT summary_id, story_order
                FROM tag_instances
                WHERE tag_id = :tag_id
                ORDER BY story_order
            """
            ),
            {"tag_id": tag_id},
        ).fetchall()

        # Check that order matches our chain
        result_ids = [r.summary_id for r in results]
        assert result_ids == summaries

        # Check that orders are properly spaced
        orders = [r.story_order for r in results]
        assert all(orders[i] < orders[i + 1] for i in range(len(orders) - 1))
        assert all(o % 1000 == 0 for o in orders)

        # Cleanup in correct order
        cleanup_queries = [
            "DELETE FROM tag_instances WHERE tag_id = :tag_id OR tag_id = ANY(:time_ids)",
            "DELETE FROM times WHERE id = ANY(:time_ids)",
            "DELETE FROM tags WHERE id = :tag_id OR id = ANY(:time_ids)",
            "DELETE FROM summaries WHERE id = ANY(:summary_ids)",
        ]

        for query in cleanup_queries:
            session.execute(
                text(query),
                {"tag_id": tag_id, "time_ids": time_ids, "summary_ids": summaries},
            )
        session.commit()


def test_update_story_order_bulk_circular_dependency(history_db):
    """Test that circular dependencies are detected and raise an error."""
    tag_id = uuid4()
    summaries = [uuid4() for _ in range(3)]

    with history_db.Session() as session:
        # Create tag
        session.execute(
            text("INSERT INTO tags (id, type) VALUES (:id, 'PERSON')"), {"id": tag_id}
        )

        # Create summaries and their relationships
        for summary_id in summaries:
            session.execute(
                text("INSERT INTO summaries (id, text) VALUES (:id, :text)"),
                {"id": summary_id, "text": f"Test summary {summary_id}"},
            )

        # Create circular dependency: 0 -> 1 -> 2 -> 0
        dependencies = {
            summaries[0]: [str(summaries[2])],  # Convert UUIDs to strings
            summaries[1]: [str(summaries[0])],
            summaries[2]: [str(summaries[1])],
        }

        for i, (summary_id, after) in enumerate(dependencies.items()):
            session.execute(
                text(
                    """
                    INSERT INTO tag_instances
                    (id, summary_id, tag_id, start_char, stop_char, story_order, after)
                    VALUES (:id, :summary_id, :tag_id, 0, 10, :story_order, to_jsonb(:after))
                """
                ),
                {
                    "id": uuid4(),
                    "summary_id": summary_id,
                    "tag_id": tag_id,
                    "story_order": i * 1000,  # Different initial orders
                    "after": after,
                },
            )

        session.commit()

        # Verify that circular dependency is detected
        with pytest.raises(ValueError, match="Circular dependency detected"):
            history_db.update_story_order_bulk(tag_id=tag_id, session=session)

        # Cleanup in correct order
        cleanup_queries = [
            "DELETE FROM tag_instances WHERE tag_id = :tag_id",
            "DELETE FROM tags WHERE id = :tag_id",
            "DELETE FROM summaries WHERE id IN :summary_ids",
        ]

        for query in cleanup_queries:
            session.execute(
                text(query), {"tag_id": tag_id, "summary_ids": tuple(summaries)}
            )
        session.commit()
