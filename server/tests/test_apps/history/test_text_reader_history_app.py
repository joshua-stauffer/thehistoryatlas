"""Tests for text-reader methods in HistoryApp."""

import pytest
from uuid import uuid4, UUID
from sqlalchemy import text
from sqlalchemy.orm import Session

from the_history_atlas.apps.domain.core import TagInstance


# --- Helpers ---


def insert_source(session, source_id: UUID, title: str):
    session.execute(
        text(
            "INSERT INTO sources (id, title, author, publisher, kwargs) "
            "VALUES (:id, :title, 'Author', 'Publisher', '{}')"
        ),
        {"id": source_id, "title": title},
    )


def insert_story(session, story_id: UUID, name: str, source_id: UUID | None = None):
    session.execute(
        text(
            "INSERT INTO stories (id, name, source_id, created_at) "
            "VALUES (:id, :name, :source_id, now())"
        ),
        {"id": story_id, "name": name, "source_id": source_id},
    )


# --- Tests ---


class TestCreatePersonWithoutWikidata:
    def test_returns_id(self, history_app, cleanup_tag):
        result = history_app.create_person_without_wikidata(name="Charles Burney")
        cleanup_tag(result["id"])

        assert result["id"] is not None

    def test_returns_name(self, history_app, cleanup_tag):
        result = history_app.create_person_without_wikidata(name="Charles Burney")
        cleanup_tag(result["id"])

        assert result["name"] == "Charles Burney"

    def test_creates_tag_in_db(self, history_app, engine, cleanup_tag):
        result = history_app.create_person_without_wikidata(name="George Handel")
        cleanup_tag(result["id"])

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT type FROM tags WHERE id = :id"),
                {"id": result["id"]},
            ).one()

        assert row.type == "PERSON"

    def test_creates_name_association(self, history_app, engine, cleanup_tag):
        result = history_app.create_person_without_wikidata(name="Antonio Vivaldi")
        cleanup_tag(result["id"])

        with Session(engine, future=True) as session:
            row = session.execute(
                text(
                    "SELECT n.name FROM names n "
                    "JOIN tag_names tn ON n.id = tn.name_id "
                    "WHERE tn.tag_id = :tag_id"
                ),
                {"tag_id": result["id"]},
            ).one()

        assert row.name == "Antonio Vivaldi"

    def test_has_null_wikidata_id(self, history_app, engine, cleanup_tag):
        result = history_app.create_person_without_wikidata(name="Test Person")
        cleanup_tag(result["id"])

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT wikidata_id FROM tags WHERE id = :id"),
                {"id": result["id"]},
            ).one()

        assert row.wikidata_id is None

    def test_creates_story_name(self, history_app, engine, cleanup_tag):
        result = history_app.create_person_without_wikidata(name="Johann Bach")
        cleanup_tag(result["id"])

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT name FROM story_names WHERE tag_id = :tag_id"),
                {"tag_id": result["id"]},
            ).one()

        assert row.name == "The Life of Johann Bach"


class TestCreatePlaceWithoutWikidata:
    def test_returns_id(self, history_app, cleanup_tag):
        result = history_app.create_place_without_wikidata(
            name="Leipzig", latitude=51.3, longitude=12.4
        )
        cleanup_tag(result["id"])

        assert result["id"] is not None

    def test_returns_coordinates(self, history_app, cleanup_tag):
        result = history_app.create_place_without_wikidata(
            name="Leipzig", latitude=51.3, longitude=12.4
        )
        cleanup_tag(result["id"])

        assert result["latitude"] == 51.3
        assert result["longitude"] == 12.4

    def test_creates_place_in_db(self, history_app, engine, cleanup_tag):
        result = history_app.create_place_without_wikidata(
            name="Dresden", latitude=51.05, longitude=13.74
        )
        cleanup_tag(result["id"])

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT latitude, longitude FROM places WHERE id = :id"),
                {"id": result["id"]},
            ).one()

        assert abs(row.latitude - 51.05) < 0.01

    def test_has_null_wikidata_id(self, history_app, engine, cleanup_tag):
        result = history_app.create_place_without_wikidata(
            name="Weimar", latitude=50.98, longitude=11.33
        )
        cleanup_tag(result["id"])

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT wikidata_id FROM tags WHERE id = :id"),
                {"id": result["id"]},
            ).one()

        assert row.wikidata_id is None

    def test_creates_story_name(self, history_app, engine, cleanup_tag):
        result = history_app.create_place_without_wikidata(
            name="Hamburg", latitude=53.55, longitude=10.0
        )
        cleanup_tag(result["id"])

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT name FROM story_names WHERE tag_id = :tag_id"),
                {"tag_id": result["id"]},
            ).one()

        assert row.name == "The History of Hamburg"


class TestCreateTimeWithoutWikidata:
    def test_returns_id(self, history_app, cleanup_tag):
        result = history_app.create_time_without_wikidata(
            name="1720",
            date="+1720-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )
        cleanup_tag(result["id"])

        assert result["id"] is not None

    def test_returns_date(self, history_app, cleanup_tag):
        result = history_app.create_time_without_wikidata(
            name="1721",
            date="+1721-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )
        cleanup_tag(result["id"])

        assert result["date"] == "+1721-00-00T00:00:00Z"

    def test_creates_time_in_db(self, history_app, engine, cleanup_tag):
        result = history_app.create_time_without_wikidata(
            name="1722",
            date="+1722-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )
        cleanup_tag(result["id"])

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT datetime, precision FROM times WHERE id = :id"),
                {"id": result["id"]},
            ).one()

        assert row.datetime == "+1722-00-00T00:00:00Z"

    def test_has_null_wikidata_id(self, history_app, engine, cleanup_tag):
        result = history_app.create_time_without_wikidata(
            name="1723",
            date="+1723-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )
        cleanup_tag(result["id"])

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT wikidata_id FROM tags WHERE id = :id"),
                {"id": result["id"]},
            ).one()

        assert row.wikidata_id is None

    def test_creates_story_name(self, history_app, engine, cleanup_tag):
        result = history_app.create_time_without_wikidata(
            name="1724",
            date="+1724-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )
        cleanup_tag(result["id"])

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT name FROM story_names WHERE tag_id = :tag_id"),
                {"tag_id": result["id"]},
            ).one()

        assert row.name == "Events of 1724"


class TestCreateTextReaderSource:
    def test_creates_new_source(self, history_app, engine):
        result = history_app.create_text_reader_source(
            title="A General History of Music",
            author="Charles Burney",
            publisher="Payne and Son",
            pub_date="1789",
        )

        assert result["title"] == "A General History of Music"

    def test_returns_id(self, history_app):
        result = history_app.create_text_reader_source(
            title="Music History Vol 2",
            author="Burney",
            publisher="Publisher",
            pub_date=None,
        )

        assert result["id"] is not None

    def test_returns_existing_source_by_title(self, history_app, engine):
        # Create a source first
        source_id = uuid4()
        with Session(engine, future=True) as session:
            insert_source(session, source_id, "Existing Source Title")
            session.commit()

        # Rebuild trie so it knows about the new source
        history_app._repository._source_trie.build(
            entity_tuples=history_app._repository.get_all_source_titles_and_authors()
        )

        result = history_app.create_text_reader_source(
            title="Existing Source Title",
            author="Author",
            publisher="Publisher",
            pub_date=None,
        )

        assert result["id"] == source_id


class TestCreateTextReaderStory:
    def test_returns_id(self, history_app):
        result = history_app.create_text_reader_story(name="Burney's Music History")

        assert result["id"] is not None

    def test_returns_name(self, history_app):
        result = history_app.create_text_reader_story(name="My Story")

        assert result["name"] == "My Story"

    def test_stores_source_id(self, history_app, engine):
        source_id = uuid4()
        with Session(engine, future=True) as session:
            insert_source(session, source_id, "Story Source")
            session.commit()

        result = history_app.create_text_reader_story(
            name="Story with Source", source_id=source_id
        )

        assert result["source_id"] == source_id

    def test_creates_story_in_db(self, history_app, engine):
        result = history_app.create_text_reader_story(name="DB Story")

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT name FROM stories WHERE id = :id"),
                {"id": result["id"]},
            ).one()

        assert row.name == "DB Story"


class TestGetStoryBySourceId:
    def test_returns_story(self, history_app, engine):
        source_id = uuid4()
        story_id = uuid4()

        with Session(engine, future=True) as session:
            insert_source(session, source_id, "Test Source")
            insert_story(session, story_id, "Found Story", source_id=source_id)
            session.commit()

        result = history_app.get_story_by_source_id(source_id=source_id)

        assert result["id"] == story_id

    def test_returns_none_when_not_found(self, history_app):
        result = history_app.get_story_by_source_id(source_id=uuid4())

        assert result is None


class TestSearchPeopleByName:
    def test_finds_person(self, history_app, cleanup_tag):
        result = history_app.create_person_without_wikidata(name="Christoph Gluck")
        cleanup_tag(result["id"])

        search_results = history_app.search_people_by_name(name="Christoph Gluck")

        assert any(r["id"] == result["id"] for r in search_results)

    def test_returns_empty_for_no_match(self, history_app):
        result = history_app.search_people_by_name(name="xyznonexistent999")

        assert result == []


class TestSearchPlaces:
    def test_finds_place_by_name(self, history_app, cleanup_tag):
        result = history_app.create_place_without_wikidata(
            name="Salzburg", latitude=47.8, longitude=13.0
        )
        cleanup_tag(result["id"])

        search_results = history_app.search_places(name="Salzburg")

        assert any(r["id"] == result["id"] for r in search_results)

    def test_finds_place_by_coordinates(self, history_app, cleanup_tag):
        result = history_app.create_place_without_wikidata(
            name="Eisenach", latitude=50.97, longitude=10.32
        )
        cleanup_tag(result["id"])

        search_results = history_app.search_places(
            latitude=50.97, longitude=10.32, radius=0.5
        )

        assert any(r["id"] == result["id"] for r in search_results)


class TestCreateTextReaderEvent:
    def test_returns_summary_id(self, history_app, engine, cleanup_tag):
        # Create prerequisite entities
        person = history_app.create_person_without_wikidata(name="Event Person")
        cleanup_tag(person["id"])
        place = history_app.create_place_without_wikidata(
            name="Event Place", latitude=48.2, longitude=16.4
        )
        cleanup_tag(place["id"])
        time_result = history_app.create_time_without_wikidata(
            name="1750",
            date="+1750-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )
        cleanup_tag(time_result["id"])
        source = history_app.create_text_reader_source(
            title="Event Source",
            author="Author",
            publisher="Pub",
            pub_date=None,
        )
        story = history_app.create_text_reader_story(
            name="Event Story",
            source_id=source["id"],
        )

        summary_id = history_app.create_text_reader_event(
            text="Event Person visited Event Place in 1750.",
            tags=[
                TagInstance(
                    id=person["id"], start_char=0, stop_char=12, name="Event Person"
                ),
                TagInstance(
                    id=place["id"], start_char=21, stop_char=32, name="Event Place"
                ),
                TagInstance(
                    id=time_result["id"], start_char=36, stop_char=40, name="1750"
                ),
            ],
            citation_text="Burney, vol. 1, p. 42",
            citation_page_num=42,
            citation_access_date="2026-03-11",
            source_id=source["id"],
            story_id=story["id"],
        )

        assert summary_id is not None

    def test_creates_summary_in_db(self, history_app, engine, cleanup_tag):
        person = history_app.create_person_without_wikidata(name="Summary Person")
        cleanup_tag(person["id"])
        place = history_app.create_place_without_wikidata(
            name="Summary Place", latitude=51.0, longitude=13.7
        )
        cleanup_tag(place["id"])
        time_result = history_app.create_time_without_wikidata(
            name="1751",
            date="+1751-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )
        cleanup_tag(time_result["id"])
        source = history_app.create_text_reader_source(
            title="Summary Source",
            author="A",
            publisher="P",
            pub_date=None,
        )
        story = history_app.create_text_reader_story(
            name="Summary Story",
            source_id=source["id"],
        )

        summary_id = history_app.create_text_reader_event(
            text="Summary Person visited Summary Place in 1751.",
            tags=[
                TagInstance(
                    id=person["id"], start_char=0, stop_char=14, name="Summary Person"
                ),
                TagInstance(
                    id=place["id"], start_char=23, stop_char=36, name="Summary Place"
                ),
                TagInstance(
                    id=time_result["id"], start_char=40, stop_char=44, name="1751"
                ),
            ],
            citation_text="citation",
            citation_page_num=None,
            citation_access_date=None,
            source_id=source["id"],
            story_id=story["id"],
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT text FROM summaries WHERE id = :id"),
                {"id": summary_id},
            ).one()

        assert row.text == "Summary Person visited Summary Place in 1751."

    def test_adds_summary_to_story(self, history_app, engine, cleanup_tag):
        person = history_app.create_person_without_wikidata(name="Story Person")
        cleanup_tag(person["id"])
        place = history_app.create_place_without_wikidata(
            name="Story Place", latitude=52.5, longitude=13.4
        )
        cleanup_tag(place["id"])
        time_result = history_app.create_time_without_wikidata(
            name="1752",
            date="+1752-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )
        cleanup_tag(time_result["id"])
        source = history_app.create_text_reader_source(
            title="Story Event Source",
            author="A",
            publisher="P",
            pub_date=None,
        )
        story = history_app.create_text_reader_story(
            name="Event Story 2",
            source_id=source["id"],
        )

        summary_id = history_app.create_text_reader_event(
            text="Story Person visited Story Place in 1752.",
            tags=[
                TagInstance(
                    id=person["id"], start_char=0, stop_char=12, name="Story Person"
                ),
                TagInstance(
                    id=place["id"], start_char=21, stop_char=32, name="Story Place"
                ),
                TagInstance(
                    id=time_result["id"], start_char=36, stop_char=40, name="1752"
                ),
            ],
            citation_text="citation",
            citation_page_num=None,
            citation_access_date=None,
            source_id=source["id"],
            story_id=story["id"],
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text(
                    "SELECT summary_id, position FROM story_summaries "
                    "WHERE story_id = :story_id"
                ),
                {"story_id": story["id"]},
            ).one()

        assert row.summary_id == summary_id

    def test_creates_citation(self, history_app, engine, cleanup_tag):
        person = history_app.create_person_without_wikidata(name="Citation Person")
        cleanup_tag(person["id"])
        place = history_app.create_place_without_wikidata(
            name="Citation Place", latitude=48.8, longitude=2.3
        )
        cleanup_tag(place["id"])
        time_result = history_app.create_time_without_wikidata(
            name="1753",
            date="+1753-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )
        cleanup_tag(time_result["id"])
        source = history_app.create_text_reader_source(
            title="Citation Source",
            author="A",
            publisher="P",
            pub_date=None,
        )
        story = history_app.create_text_reader_story(
            name="Citation Story",
            source_id=source["id"],
        )

        summary_id = history_app.create_text_reader_event(
            text="Citation Person visited Citation Place in 1753.",
            tags=[
                TagInstance(
                    id=person["id"], start_char=0, stop_char=15, name="Citation Person"
                ),
                TagInstance(
                    id=place["id"], start_char=24, stop_char=38, name="Citation Place"
                ),
                TagInstance(
                    id=time_result["id"], start_char=42, stop_char=46, name="1753"
                ),
            ],
            citation_text="Burney, vol. 2, p. 100",
            citation_page_num=100,
            citation_access_date="2026-03-11",
            source_id=source["id"],
            story_id=story["id"],
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT text, page_num FROM citations WHERE summary_id = :id"),
                {"id": summary_id},
            ).one()

        assert row.text == "Burney, vol. 2, p. 100"
