from datetime import datetime, timezone
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
from the_history_atlas.apps.domain.models.history.tables.tag_instance import (
    TagInstanceInput,
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
        tag_instance = TagInstanceInput(
            tag_id=tag_id,
            summary_id=summary_id,
            start_char=start_char,
            stop_char=stop_char,
        )
        # act
        tag_instances = history_db.bulk_create_tag_instances(
            tag_instances=[tag_instance],
            session=session,
            after=[],
        )
        session.commit()

    assert len(tag_instances) == 1
    tag_instance = tag_instances[0]
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


class TestRebalanceStoryOrder:
    def test_rebalance_story_order_success(self, history_db):
        """Test that story orders are rebalanced correctly while maintaining order"""
        # Create a tag and some tag instances with story orders
        tag_id = uuid4()

        with history_db.Session() as session:
            # Create tag
            session.execute(
                text("INSERT INTO tags (id, type) VALUES (:id, 'PERSON')"),
                {"id": tag_id},
            )

            # Create summary
            summary_id = uuid4()
            session.execute(
                text("INSERT INTO summaries (id, text) VALUES (:id, 'test summary')"),
                {"id": summary_id},
            )

            # Create tag instances with varying story orders
            instance_ids = []
            story_orders = [100000, 100001, 100500, 101000, 102000]
            for order in story_orders:
                instance_id = uuid4()
                instance_ids.append(instance_id)
                session.execute(
                    text(
                        """
                        INSERT INTO tag_instances 
                        (id, tag_id, summary_id, story_order, start_char, stop_char) 
                        VALUES (:id, :tag_id, :summary_id, :story_order, 0, 1)
                    """
                    ),
                    {
                        "id": instance_id,
                        "tag_id": tag_id,
                        "summary_id": summary_id,
                        "story_order": order,
                    },
                )

            # Also add a null story_order instance
            null_instance_id = uuid4()
            session.execute(
                text(
                    """
                    INSERT INTO tag_instances 
                    (id, tag_id, summary_id, story_order, start_char, stop_char) 
                    VALUES (:id, :tag_id, :summary_id, NULL, 0, 1)
                """
                ),
                {
                    "id": null_instance_id,
                    "tag_id": tag_id,
                    "summary_id": summary_id,
                },
            )
            session.commit()

            # Call rebalance
            result = history_db.rebalance_story_order(tag_id)

            # Verify the returned dictionary
            assert len(result) == len(story_orders)
            assert set(result.keys()) == set(instance_ids)

            # Verify the values are properly spaced
            orders = sorted(result.values())
            for i in range(len(orders) - 1):
                assert orders[i + 1] - orders[i] == 1000

            # Verify results in database
            rows = session.execute(
                text(
                    """
                    SELECT story_order 
                    FROM tag_instances 
                    WHERE tag_id = :tag_id 
                    AND story_order IS NOT NULL 
                    ORDER BY story_order ASC
                """
                ),
                {"tag_id": tag_id},
            ).all()

            # Check that we have the right number of non-null rows
            assert len(rows) == len(story_orders)

            # Check that the difference between each story_order is exactly 1000
            orders = [row[0] for row in rows]
            for i in range(len(orders) - 1):
                assert orders[i + 1] - orders[i] == 1000

            # Check that null story_order is still null
            null_row = session.execute(
                text(
                    """
                    SELECT story_order 
                    FROM tag_instances 
                    WHERE id = :id
                """
                ),
                {"id": null_instance_id},
            ).scalar_one()
            assert null_row is None

            # Cleanup
            session.execute(
                text("DELETE FROM tag_instances WHERE tag_id = :tag_id"),
                {"tag_id": tag_id},
            )
            session.execute(text("DELETE FROM tags WHERE id = :id"), {"id": tag_id})
            session.execute(
                text("DELETE FROM summaries WHERE id = :id"), {"id": summary_id}
            )
            session.commit()

    def test_rebalance_story_order_empty(self, history_db):
        """Test that rebalancing works with no tag instances"""
        tag_id = uuid4()
        with history_db.Session() as session:
            # Create tag
            session.execute(
                text("INSERT INTO tags (id, type) VALUES (:id, 'PERSON')"),
                {"id": tag_id},
            )
            session.commit()

            # Call rebalance - should not error and return empty dict
            result = history_db.rebalance_story_order(tag_id)
            assert result == {}

            # Cleanup
            session.execute(text("DELETE FROM tags WHERE id = :id"), {"id": tag_id})
            session.commit()

    def test_rebalance_story_order_all_null(self, history_db):
        """Test that rebalancing works when all story orders are null"""
        tag_id = uuid4()
        summary_id = uuid4()

        with history_db.Session() as session:
            # Create tag
            session.execute(
                text("INSERT INTO tags (id, type) VALUES (:id, 'PERSON')"),
                {"id": tag_id},
            )

            # Create summary
            session.execute(
                text("INSERT INTO summaries (id, text) VALUES (:id, 'test summary')"),
                {"id": summary_id},
            )

            # Create tag instances with null story orders
            for _ in range(3):
                instance_id = uuid4()
                session.execute(
                    text(
                        """
                        INSERT INTO tag_instances 
                        (id, tag_id, summary_id, story_order, start_char, stop_char) 
                        VALUES (:id, :tag_id, :summary_id, NULL, 0, 1)
                    """
                    ),
                    {"id": instance_id, "tag_id": tag_id, "summary_id": summary_id},
                )
            session.commit()

            # Call rebalance - should not error and return empty dict
            result = history_db.rebalance_story_order(tag_id)
            assert result == {}

            # Verify all story orders are still null
            rows = session.execute(
                text(
                    """
                    SELECT story_order 
                    FROM tag_instances 
                    WHERE tag_id = :tag_id
                """
                ),
                {"tag_id": tag_id},
            ).all()

            assert len(rows) == 3
            for row in rows:
                assert row[0] is None

            # Cleanup
            session.execute(
                text("DELETE FROM tag_instances WHERE tag_id = :tag_id"),
                {"tag_id": tag_id},
            )
            session.execute(text("DELETE FROM tags WHERE id = :id"), {"id": tag_id})
            session.execute(
                text("DELETE FROM summaries WHERE id = :id"), {"id": summary_id}
            )
            session.commit()


class TestGetTagIdsWithNullOrders:
    def test_get_tag_ids_with_null_orders(self, history_db):
        """Test that tag IDs with null story orders are correctly identified and ordered"""
        # Create three tags with carefully crafted UUIDs to ensure a predictable sort order
        tag_id_with_null_1 = uuid4()
        tag_id_with_null_2 = uuid4()
        tag_id_without_null = uuid4()

        # Ensure tag_id_with_null_1 < tag_id_with_null_2 for ordering test
        if tag_id_with_null_1 > tag_id_with_null_2:
            tag_id_with_null_1, tag_id_with_null_2 = (
                tag_id_with_null_2,
                tag_id_with_null_1,
            )

        summary_id = uuid4()

        with history_db.Session() as session:
            # Create tags
            session.execute(
                text(
                    "INSERT INTO tags (id, type) VALUES (:id1, 'PERSON'), (:id2, 'PERSON'), (:id3, 'PERSON')"
                ),
                {
                    "id1": tag_id_with_null_1,
                    "id2": tag_id_with_null_2,
                    "id3": tag_id_without_null,
                },
            )

            # Create a summary
            session.execute(
                text("INSERT INTO summaries (id, text) VALUES (:id, 'test summary')"),
                {"id": summary_id},
            )

            # Create tag instance with NULL story_order for first tag
            session.execute(
                text(
                    """
                    INSERT INTO tag_instances 
                    (id, tag_id, summary_id, story_order, start_char, stop_char) 
                    VALUES (:id, :tag_id, :summary_id, NULL, 0, 1)
                """
                ),
                {
                    "id": uuid4(),
                    "tag_id": tag_id_with_null_1,
                    "summary_id": summary_id,
                },
            )

            # Create tag instance with NULL story_order for second tag
            session.execute(
                text(
                    """
                    INSERT INTO tag_instances 
                    (id, tag_id, summary_id, story_order, start_char, stop_char) 
                    VALUES (:id, :tag_id, :summary_id, NULL, 0, 1)
                """
                ),
                {
                    "id": uuid4(),
                    "tag_id": tag_id_with_null_2,
                    "summary_id": summary_id,
                },
            )

            # Create tag instance with non-NULL story_order for first tag
            session.execute(
                text(
                    """
                    INSERT INTO tag_instances 
                    (id, tag_id, summary_id, story_order, start_char, stop_char) 
                    VALUES (:id, :tag_id, :summary_id, 100000, 0, 1)
                """
                ),
                {
                    "id": uuid4(),
                    "tag_id": tag_id_with_null_1,
                    "summary_id": summary_id,
                },
            )

            # Create tag instance with non-NULL story_order for third tag
            session.execute(
                text(
                    """
                    INSERT INTO tag_instances 
                    (id, tag_id, summary_id, story_order, start_char, stop_char) 
                    VALUES (:id, :tag_id, :summary_id, 100000, 0, 1)
                """
                ),
                {
                    "id": uuid4(),
                    "tag_id": tag_id_without_null,
                    "summary_id": summary_id,
                },
            )
            session.commit()

            # Call the method and verify results
            result = history_db.get_tag_ids_with_null_orders()

            assert isinstance(result, list)
            assert len(result) == 2
            assert tag_id_with_null_1 in result
            assert tag_id_with_null_2 in result
            assert tag_id_without_null not in result

            # Check ordering: tag_id_with_null_1 should come before tag_id_with_null_2
            assert result[0] == tag_id_with_null_1
            assert result[1] == tag_id_with_null_2

            # Test with start_tag_id parameter
            result_with_start = history_db.get_tag_ids_with_null_orders(
                start_tag_id=tag_id_with_null_2
            )
            assert len(result_with_start) == 1
            assert result_with_start[0] == tag_id_with_null_2

            # Test with stop_tag_id parameter
            result_with_stop = history_db.get_tag_ids_with_null_orders(
                stop_tag_id=tag_id_with_null_1
            )
            assert len(result_with_stop) == 1
            assert result_with_stop[0] == tag_id_with_null_1

            # Test with both parameters set to the same value (should return exactly one item)
            result_with_both_same = history_db.get_tag_ids_with_null_orders(
                start_tag_id=tag_id_with_null_1, stop_tag_id=tag_id_with_null_1
            )
            assert len(result_with_both_same) == 1
            assert result_with_both_same[0] == tag_id_with_null_1

            # Test with both parameters set to a range (should return both items)
            result_with_both_range = history_db.get_tag_ids_with_null_orders(
                start_tag_id=tag_id_with_null_1, stop_tag_id=tag_id_with_null_2
            )
            assert len(result_with_both_range) == 2
            assert result_with_both_range[0] == tag_id_with_null_1
            assert result_with_both_range[1] == tag_id_with_null_2

            # Cleanup
            session.execute(
                text("DELETE FROM tag_instances WHERE tag_id IN (:id1, :id2, :id3)"),
                {
                    "id1": tag_id_with_null_1,
                    "id2": tag_id_with_null_2,
                    "id3": tag_id_without_null,
                },
            )
            session.execute(
                text("DELETE FROM tags WHERE id IN (:id1, :id2, :id3)"),
                {
                    "id1": tag_id_with_null_1,
                    "id2": tag_id_with_null_2,
                    "id3": tag_id_without_null,
                },
            )
            session.execute(
                text("DELETE FROM summaries WHERE id = :id"),
                {"id": summary_id},
            )
            session.commit()

    def test_get_tag_ids_with_null_orders_with_nonexistent_bounds(self, history_db):
        """Test that using start_tag_id and stop_tag_id with values outside the range works correctly"""
        # Create tags
        tag_id_with_null_1 = uuid4()
        tag_id_with_null_2 = uuid4()

        # Ensure tag_id_with_null_1 < tag_id_with_null_2 for ordering test
        if tag_id_with_null_1 > tag_id_with_null_2:
            tag_id_with_null_1, tag_id_with_null_2 = (
                tag_id_with_null_2,
                tag_id_with_null_1,
            )

        summary_id = uuid4()

        # Create IDs for bounds testing that are definitely outside our range
        # UUID('00000000-0000-0000-0000-000000000000') is the smallest possible UUID
        # UUID('ffffffff-ffff-ffff-ffff-ffffffffffff') is the largest possible UUID
        too_small_id = UUID("00000000-0000-0000-0000-000000000000")
        too_large_id = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")

        with history_db.Session() as session:
            # Create tags
            session.execute(
                text(
                    "INSERT INTO tags (id, type) VALUES (:id1, 'PERSON'), (:id2, 'PERSON')"
                ),
                {
                    "id1": tag_id_with_null_1,
                    "id2": tag_id_with_null_2,
                },
            )

            # Create a summary
            session.execute(
                text("INSERT INTO summaries (id, text) VALUES (:id, 'test summary')"),
                {"id": summary_id},
            )

            # Create tag instances with NULL story_orders
            session.execute(
                text(
                    """
                    INSERT INTO tag_instances 
                    (id, tag_id, summary_id, story_order, start_char, stop_char) 
                    VALUES (:id1, :tag_id1, :summary_id, NULL, 0, 1),
                           (:id2, :tag_id2, :summary_id, NULL, 0, 1)
                """
                ),
                {
                    "id1": uuid4(),
                    "tag_id1": tag_id_with_null_1,
                    "id2": uuid4(),
                    "tag_id2": tag_id_with_null_2,
                    "summary_id": summary_id,
                },
            )
            session.commit()

            # Test with too small start_tag_id (should include all)
            result_with_small_start = history_db.get_tag_ids_with_null_orders(
                start_tag_id=too_small_id
            )
            assert len(result_with_small_start) == 2
            assert result_with_small_start[0] == tag_id_with_null_1
            assert result_with_small_start[1] == tag_id_with_null_2

            # Test with too large stop_tag_id (should include all)
            result_with_large_stop = history_db.get_tag_ids_with_null_orders(
                stop_tag_id=too_large_id
            )
            assert len(result_with_large_stop) == 2
            assert result_with_large_stop[0] == tag_id_with_null_1
            assert result_with_large_stop[1] == tag_id_with_null_2

            # Test with start_tag_id that's too large (should return empty)
            result_with_large_start = history_db.get_tag_ids_with_null_orders(
                start_tag_id=too_large_id
            )
            assert len(result_with_large_start) == 0

            # Test with stop_tag_id that's too small (should return empty)
            result_with_small_stop = history_db.get_tag_ids_with_null_orders(
                stop_tag_id=too_small_id
            )
            assert len(result_with_small_stop) == 0

            # Test with start_tag_id > stop_tag_id (should return empty)
            result_with_invalid_range = history_db.get_tag_ids_with_null_orders(
                start_tag_id=tag_id_with_null_2, stop_tag_id=tag_id_with_null_1
            )
            assert len(result_with_invalid_range) == 0

            # Cleanup
            session.execute(
                text("DELETE FROM tag_instances WHERE tag_id IN (:id1, :id2)"),
                {
                    "id1": tag_id_with_null_1,
                    "id2": tag_id_with_null_2,
                },
            )
            session.execute(
                text("DELETE FROM tags WHERE id IN (:id1, :id2)"),
                {
                    "id1": tag_id_with_null_1,
                    "id2": tag_id_with_null_2,
                },
            )
            session.execute(
                text("DELETE FROM summaries WHERE id = :id"),
                {"id": summary_id},
            )
            session.commit()

    def test_empty_result(self, history_db):
        """Test that empty list is returned when no tags have null orders"""
        # Create a tag
        tag_id = uuid4()
        summary_id = uuid4()

        with history_db.Session() as session:
            # Create tag
            session.execute(
                text("INSERT INTO tags (id, type) VALUES (:id, 'PERSON')"),
                {"id": tag_id},
            )

            # Create a summary
            session.execute(
                text("INSERT INTO summaries (id, text) VALUES (:id, 'test summary')"),
                {"id": summary_id},
            )

            # Create tag instance with non-NULL story_order
            session.execute(
                text(
                    """
                    INSERT INTO tag_instances 
                    (id, tag_id, summary_id, story_order, start_char, stop_char) 
                    VALUES (:id, :tag_id, :summary_id, 100000, 0, 1)
                """
                ),
                {
                    "id": uuid4(),
                    "tag_id": tag_id,
                    "summary_id": summary_id,
                },
            )
            session.commit()

            # Call the method and verify results
            result = history_db.get_tag_ids_with_null_orders()

            assert isinstance(result, list)
            assert len(result) == 0

            # Test with start_tag_id and stop_tag_id
            result_with_params = history_db.get_tag_ids_with_null_orders(
                start_tag_id=tag_id, stop_tag_id=tag_id
            )
            assert isinstance(result_with_params, list)
            assert len(result_with_params) == 0

            # Cleanup
            session.execute(
                text("DELETE FROM tag_instances WHERE tag_id = :id"),
                {"id": tag_id},
            )
            session.execute(
                text("DELETE FROM tags WHERE id = :id"),
                {"id": tag_id},
            )
            session.execute(
                text("DELETE FROM summaries WHERE id = :id"),
                {"id": summary_id},
            )
            session.commit()

    def test_no_tag_instances(self, history_db):
        """Test behavior when there are no tag instances"""
        # Create a tag but no tag instances
        tag_id = uuid4()

        with history_db.Session() as session:
            # Create tag
            session.execute(
                text("INSERT INTO tags (id, type) VALUES (:id, 'PERSON')"),
                {"id": tag_id},
            )
            session.commit()

            # Call the method and verify results
            result = history_db.get_tag_ids_with_null_orders()

            assert isinstance(result, list)
            assert len(result) == 0

            # Test with start_tag_id and stop_tag_id
            result_with_params = history_db.get_tag_ids_with_null_orders(
                start_tag_id=tag_id, stop_tag_id=tag_id
            )
            assert isinstance(result_with_params, list)
            assert len(result_with_params) == 0

            # Cleanup
            session.execute(
                text("DELETE FROM tags WHERE id = :id"),
                {"id": tag_id},
            )
            session.commit()
