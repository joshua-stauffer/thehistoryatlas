"""Tests for text-reader repository methods."""

import pytest
from uuid import uuid4, UUID
from sqlalchemy import text
from sqlalchemy.orm import Session

from the_history_atlas.apps.history.repository import Repository
from the_history_atlas.apps.history.trie import Trie


# --- Helpers ---


def insert_tag(session, tag_id: UUID, tag_type: str):
    session.execute(
        text("INSERT INTO tags (id, type) VALUES (:id, :type)"),
        {"id": tag_id, "type": tag_type},
    )


def insert_name(session, name_id: UUID, name: str):
    session.execute(
        text("INSERT INTO names (id, name) VALUES (:id, :name)"),
        {"id": name_id, "name": name},
    )


def insert_tag_name(session, tag_id: UUID, name_id: UUID):
    session.execute(
        text("INSERT INTO tag_names (tag_id, name_id) VALUES (:tag_id, :name_id)"),
        {"tag_id": tag_id, "name_id": name_id},
    )


def insert_person(session, tag_id: UUID):
    insert_tag(session, tag_id, "PERSON")
    session.execute(
        text("INSERT INTO people (id) VALUES (:id)"),
        {"id": tag_id},
    )


def insert_place(session, tag_id: UUID, latitude: float, longitude: float):
    insert_tag(session, tag_id, "PLACE")
    session.execute(
        text("INSERT INTO places (id, latitude, longitude) VALUES (:id, :lat, :lng)"),
        {"id": tag_id, "lat": latitude, "lng": longitude},
    )


def insert_time(
    session, tag_id: UUID, datetime_val: str, calendar_model: str, precision: int
):
    insert_tag(session, tag_id, "TIME")
    session.execute(
        text(
            "INSERT INTO times (id, datetime, calendar_model, precision) "
            "VALUES (:id, :dt, :cm, :p)"
        ),
        {"id": tag_id, "dt": datetime_val, "cm": calendar_model, "p": precision},
    )


def insert_summary(
    session,
    summary_id: UUID,
    summary_text: str,
    datetime_val: str | None = None,
    calendar_model: str | None = None,
    precision: int | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):
    session.execute(
        text(
            "INSERT INTO summaries (id, text, datetime, calendar_model, precision, latitude, longitude) "
            "VALUES (:id, :text, :dt, :cm, :p, :lat, :lng)"
        ),
        {
            "id": summary_id,
            "text": summary_text,
            "dt": datetime_val,
            "cm": calendar_model,
            "p": precision,
            "lat": latitude,
            "lng": longitude,
        },
    )


def insert_tag_instance(session, tag_instance_id: UUID, summary_id: UUID, tag_id: UUID):
    session.execute(
        text(
            "INSERT INTO tag_instances (id, start_char, stop_char, summary_id, tag_id) "
            "VALUES (:id, 0, 10, :summary_id, :tag_id)"
        ),
        {"id": tag_instance_id, "summary_id": summary_id, "tag_id": tag_id},
    )


def insert_source(session, source_id: UUID, title: str = "Test Source"):
    session.execute(
        text(
            "INSERT INTO sources (id, title, author, publisher, kwargs) "
            "VALUES (:id, :title, 'Author', 'Publisher', '{}')"
        ),
        {"id": source_id, "title": title},
    )


def insert_citation(
    session,
    citation_id: UUID,
    summary_id: UUID,
    source_id: UUID,
    wikidata_item_id: str | None = None,
):
    session.execute(
        text(
            "INSERT INTO citations (id, text, source_id, summary_id, wikidata_item_id) "
            "VALUES (:id, 'citation text', :source_id, :summary_id, :wikidata_item_id)"
        ),
        {
            "id": citation_id,
            "summary_id": summary_id,
            "source_id": source_id,
            "wikidata_item_id": wikidata_item_id,
        },
    )


def insert_story(session, story_id: UUID, name: str, source_id: UUID | None = None):
    session.execute(
        text(
            "INSERT INTO stories (id, name, source_id, created_at) "
            "VALUES (:id, :name, :source_id, now())"
        ),
        {"id": story_id, "name": name, "source_id": source_id},
    )


def insert_story_summary(session, story_id: UUID, summary_id: UUID, position: int):
    session.execute(
        text(
            "INSERT INTO story_summaries (id, story_id, summary_id, position) "
            "VALUES (:id, :story_id, :summary_id, :position)"
        ),
        {
            "id": uuid4(),
            "story_id": story_id,
            "summary_id": summary_id,
            "position": position,
        },
    )


def create_person_with_name(session, name: str) -> UUID:
    """Create a person tag with a name and return the tag_id."""
    tag_id = uuid4()
    name_id = uuid4()
    insert_person(session, tag_id)
    insert_name(session, name_id, name)
    insert_tag_name(session, tag_id, name_id)
    return tag_id


def create_place_with_name(
    session, name: str, latitude: float, longitude: float
) -> UUID:
    """Create a place tag with a name and return the tag_id."""
    tag_id = uuid4()
    name_id = uuid4()
    insert_place(session, tag_id, latitude, longitude)
    insert_name(session, name_id, name)
    insert_tag_name(session, tag_id, name_id)
    return tag_id


# --- Fixtures ---


@pytest.fixture
def repo(engine):
    source_trie = Trie()
    database = Repository(database_client=engine, source_trie=source_trie)
    source_trie.build(entity_tuples=database.get_all_source_titles_and_authors())
    return database


# --- Tests ---


class TestSearchTagsByNameAndType:
    def test_returns_empty_for_empty_name(self, repo):
        result = repo.search_tags_by_name_and_type(name="", tag_type="PERSON")

        assert result == []

    def test_finds_person_by_exact_name(self, repo, engine):
        with Session(engine, future=True) as session:
            tag_id = create_person_with_name(session, "Johann Sebastian Bach")
            session.commit()

        result = repo.search_tags_by_name_and_type(
            name="Johann Sebastian Bach", tag_type="PERSON"
        )

        assert any(r["id"] == tag_id for r in result)

    def test_finds_person_by_partial_name(self, repo, engine):
        with Session(engine, future=True) as session:
            tag_id = create_person_with_name(session, "Wolfgang Amadeus Mozart")
            session.commit()

        result = repo.search_tags_by_name_and_type(name="Mozart", tag_type="PERSON")

        assert any(r["id"] == tag_id for r in result)

    def test_returns_correct_fields(self, repo, engine):
        with Session(engine, future=True) as session:
            tag_id = create_person_with_name(session, "George Frideric Handel")
            session.commit()

        result = repo.search_tags_by_name_and_type(
            name="George Frideric Handel", tag_type="PERSON"
        )

        match = next(r for r in result if r["id"] == tag_id)
        assert set(match.keys()) == {
            "id",
            "name",
            "type",
            "description",
            "earliest_date",
            "latest_date",
        }

    def test_filters_by_type(self, repo, engine):
        with Session(engine, future=True) as session:
            create_person_with_name(session, "Antonio Vivaldi")
            session.commit()

        result = repo.search_tags_by_name_and_type(
            name="Antonio Vivaldi", tag_type="PLACE"
        )

        assert result == []

    def test_returns_no_results_for_nonexistent_name(self, repo):
        result = repo.search_tags_by_name_and_type(
            name="xyznonexistent123", tag_type="PERSON"
        )

        assert result == []


class TestSearchPlacesByNameAndCoordinates:
    def test_finds_place_by_name(self, repo, engine):
        with Session(engine, future=True) as session:
            tag_id = create_place_with_name(session, "Constantinople", 41.0, 28.9)
            session.commit()

        result = repo.search_places_by_name_and_coordinates(name="Constantinople")

        assert any(r["id"] == tag_id for r in result)

    def test_finds_place_by_coordinates(self, repo, engine):
        with Session(engine, future=True) as session:
            tag_id = create_place_with_name(session, "Alexandria", 31.2, 29.9)
            session.commit()

        result = repo.search_places_by_name_and_coordinates(
            latitude=31.2, longitude=29.9, radius=0.5
        )

        assert any(r["id"] == tag_id for r in result)

    def test_excludes_places_outside_radius(self, repo, engine):
        with Session(engine, future=True) as session:
            tag_id = create_place_with_name(session, "Faraway City", 80.0, 80.0)
            session.commit()

        result = repo.search_places_by_name_and_coordinates(
            latitude=0.0, longitude=0.0, radius=1.0
        )

        assert not any(r["id"] == tag_id for r in result)

    def test_returns_correct_fields(self, repo, engine):
        with Session(engine, future=True) as session:
            tag_id = create_place_with_name(session, "Vienna", 48.2, 16.4)
            session.commit()

        result = repo.search_places_by_name_and_coordinates(name="Vienna")

        match = next(r for r in result if r["id"] == tag_id)
        assert set(match.keys()) == {"id", "name", "latitude", "longitude"}

    def test_returns_empty_with_no_params(self, repo):
        result = repo.search_places_by_name_and_coordinates()

        assert result == []

    def test_deduplicates_results_from_name_and_coordinates(self, repo, engine):
        with Session(engine, future=True) as session:
            tag_id = create_place_with_name(session, "Rome", 41.9, 12.5)
            session.commit()

        result = repo.search_places_by_name_and_coordinates(
            name="Rome", latitude=41.9, longitude=12.5, radius=1.0
        )

        ids = [r["id"] for r in result]
        assert ids.count(tag_id) == 1


class TestFindMatchingSummary:
    def test_finds_matching_summary(self, repo, engine):
        person_id = uuid4()
        place_id = uuid4()
        summary_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_person(session, person_id)
            insert_place(session, place_id, 48.2, 16.4)
            insert_source(session, source_id)
            insert_summary(
                session,
                summary_id,
                "Bach visited Vienna in 1720.",
                datetime_val="+1720-00-00T00:00:00Z",
                calendar_model="Q1985727",
                precision=9,
            )
            insert_tag_instance(session, uuid4(), summary_id, person_id)
            insert_tag_instance(session, uuid4(), summary_id, place_id)
            insert_citation(session, uuid4(), summary_id, source_id)
            session.commit()

        result = repo.find_matching_summary(
            person_ids=[person_id],
            place_id=place_id,
            datetime_val="+1720-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )

        assert result is not None
        assert result["summary_id"] == summary_id

    def test_returns_none_when_no_match(self, repo):
        result = repo.find_matching_summary(
            person_ids=[uuid4()],
            place_id=uuid4(),
            datetime_val="+1720-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )

        assert result is None

    def test_returns_summary_text(self, repo, engine):
        person_id = uuid4()
        place_id = uuid4()
        summary_id = uuid4()

        with Session(engine, future=True) as session:
            insert_person(session, person_id)
            insert_place(session, place_id, 41.0, 28.9)
            insert_summary(
                session,
                summary_id,
                "Handel traveled to Constantinople.",
                datetime_val="+1700-00-00T00:00:00Z",
                calendar_model="Q1985727",
                precision=9,
            )
            insert_tag_instance(session, uuid4(), summary_id, person_id)
            insert_tag_instance(session, uuid4(), summary_id, place_id)
            session.commit()

        result = repo.find_matching_summary(
            person_ids=[person_id],
            place_id=place_id,
            datetime_val="+1700-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )

        assert result["summary_text"] == "Handel traveled to Constantinople."

    def test_reports_wikidata_citation(self, repo, engine):
        person_id = uuid4()
        place_id = uuid4()
        summary_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_person(session, person_id)
            insert_place(session, place_id, 48.2, 16.4)
            insert_source(session, source_id)
            insert_summary(
                session,
                summary_id,
                "Vivaldi performed in Vienna.",
                datetime_val="+1730-00-00T00:00:00Z",
                calendar_model="Q1985727",
                precision=9,
            )
            insert_tag_instance(session, uuid4(), summary_id, person_id)
            insert_tag_instance(session, uuid4(), summary_id, place_id)
            insert_citation(
                session,
                uuid4(),
                summary_id,
                source_id,
                wikidata_item_id="Q12345",
            )
            session.commit()

        result = repo.find_matching_summary(
            person_ids=[person_id],
            place_id=place_id,
            datetime_val="+1730-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )

        assert result["has_wikidata_citation"] is True

    def test_reports_no_wikidata_citation(self, repo, engine):
        person_id = uuid4()
        place_id = uuid4()
        summary_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_person(session, person_id)
            insert_place(session, place_id, 48.2, 16.4)
            insert_source(session, source_id)
            insert_summary(
                session,
                summary_id,
                "Mozart played in Vienna.",
                datetime_val="+1760-00-00T00:00:00Z",
                calendar_model="Q1985727",
                precision=9,
            )
            insert_tag_instance(session, uuid4(), summary_id, person_id)
            insert_tag_instance(session, uuid4(), summary_id, place_id)
            insert_citation(session, uuid4(), summary_id, source_id)
            session.commit()

        result = repo.find_matching_summary(
            person_ids=[person_id],
            place_id=place_id,
            datetime_val="+1760-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )

        assert result["has_wikidata_citation"] is False

    def test_requires_all_person_ids_to_match(self, repo, engine):
        person1_id = uuid4()
        person2_id = uuid4()
        place_id = uuid4()
        summary_id = uuid4()

        with Session(engine, future=True) as session:
            insert_person(session, person1_id)
            insert_person(session, person2_id)
            insert_place(session, place_id, 48.2, 16.4)
            insert_summary(
                session,
                summary_id,
                "Only one person here.",
                datetime_val="+1750-00-00T00:00:00Z",
                calendar_model="Q1985727",
                precision=9,
            )
            # Only link person1, not person2
            insert_tag_instance(session, uuid4(), summary_id, person1_id)
            insert_tag_instance(session, uuid4(), summary_id, place_id)
            session.commit()

        result = repo.find_matching_summary(
            person_ids=[person1_id, person2_id],
            place_id=place_id,
            datetime_val="+1750-00-00T00:00:00Z",
            calendar_model="Q1985727",
            precision=9,
        )

        assert result is None


class TestCreateTextReaderStory:
    def test_creates_story(self, repo, engine):
        story_id = uuid4()

        repo.create_text_reader_story(id=story_id, name="Test Story")

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT id, name FROM stories WHERE id = :id"),
                {"id": story_id},
            ).one()

        assert row.id == story_id

    def test_stores_name(self, repo, engine):
        story_id = uuid4()

        repo.create_text_reader_story(id=story_id, name="My Great Story")

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT name FROM stories WHERE id = :id"),
                {"id": story_id},
            ).one()

        assert row.name == "My Great Story"

    def test_stores_description(self, repo, engine):
        story_id = uuid4()

        repo.create_text_reader_story(
            id=story_id, name="Story", description="A description"
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT description FROM stories WHERE id = :id"),
                {"id": story_id},
            ).one()

        assert row.description == "A description"

    def test_stores_source_id(self, repo, engine):
        story_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_source(session, source_id)
            session.commit()

        repo.create_text_reader_story(id=story_id, name="Story", source_id=source_id)

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT source_id FROM stories WHERE id = :id"),
                {"id": story_id},
            ).one()

        assert row.source_id == source_id

    def test_sets_created_at(self, repo, engine):
        story_id = uuid4()

        repo.create_text_reader_story(id=story_id, name="Story")

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT created_at FROM stories WHERE id = :id"),
                {"id": story_id},
            ).one()

        assert row.created_at is not None


class TestAddSummaryToStory:
    def test_links_summary_to_story(self, repo, engine):
        story_id = uuid4()
        summary_id = uuid4()

        with Session(engine, future=True) as session:
            insert_story(session, story_id, "Test Story")
            insert_summary(session, summary_id, "Test summary text.")
            session.commit()

        repo.add_summary_to_story(story_id=story_id, summary_id=summary_id, position=0)

        with Session(engine, future=True) as session:
            row = session.execute(
                text(
                    "SELECT story_id, summary_id, position FROM story_summaries "
                    "WHERE story_id = :story_id AND summary_id = :summary_id"
                ),
                {"story_id": story_id, "summary_id": summary_id},
            ).one()

        assert row.position == 0

    def test_stores_position(self, repo, engine):
        story_id = uuid4()
        summary_id = uuid4()

        with Session(engine, future=True) as session:
            insert_story(session, story_id, "Test Story")
            insert_summary(session, summary_id, "Another summary.")
            session.commit()

        repo.add_summary_to_story(story_id=story_id, summary_id=summary_id, position=5)

        with Session(engine, future=True) as session:
            row = session.execute(
                text(
                    "SELECT position FROM story_summaries " "WHERE story_id = :story_id"
                ),
                {"story_id": story_id},
            ).one()

        assert row.position == 5


class TestGetStoryBySourceId:
    def test_returns_story(self, repo, engine):
        story_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_source(session, source_id)
            insert_story(session, story_id, "Found Story", source_id=source_id)
            session.commit()

        result = repo.get_story_by_source_id(source_id=source_id)

        assert result["id"] == story_id

    def test_returns_none_when_not_found(self, repo):
        result = repo.get_story_by_source_id(source_id=uuid4())

        assert result is None

    def test_returns_correct_fields(self, repo, engine):
        story_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_source(session, source_id)
            insert_story(session, story_id, "My Story", source_id=source_id)
            session.commit()

        result = repo.get_story_by_source_id(source_id=source_id)

        assert set(result.keys()) == {"id", "name", "description", "source_id"}

    def test_returns_story_name(self, repo, engine):
        story_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_source(session, source_id)
            insert_story(session, story_id, "Burney History", source_id=source_id)
            session.commit()

        result = repo.get_story_by_source_id(source_id=source_id)

        assert result["name"] == "Burney History"


class TestGetNextStoryPosition:
    def test_returns_zero_for_empty_story(self, repo, engine):
        story_id = uuid4()

        with Session(engine, future=True) as session:
            insert_story(session, story_id, "Empty Story")
            session.commit()

        result = repo.get_next_story_position(story_id=story_id)

        assert result == 0

    def test_returns_next_after_existing(self, repo, engine):
        story_id = uuid4()
        summary_id = uuid4()

        with Session(engine, future=True) as session:
            insert_story(session, story_id, "Story with one summary")
            insert_summary(session, summary_id, "Existing summary.")
            insert_story_summary(session, story_id, summary_id, position=0)
            session.commit()

        result = repo.get_next_story_position(story_id=story_id)

        assert result == 1

    def test_returns_next_after_multiple(self, repo, engine):
        story_id = uuid4()
        s1, s2, s3 = uuid4(), uuid4(), uuid4()

        with Session(engine, future=True) as session:
            insert_story(session, story_id, "Story with three summaries")
            insert_summary(session, s1, "Summary one.")
            insert_summary(session, s2, "Summary two.")
            insert_summary(session, s3, "Summary three.")
            insert_story_summary(session, story_id, s1, position=0)
            insert_story_summary(session, story_id, s2, position=1)
            insert_story_summary(session, story_id, s3, position=2)
            session.commit()

        result = repo.get_next_story_position(story_id=story_id)

        assert result == 3


class TestUpdateSummaryText:
    def test_updates_text(self, repo, engine):
        summary_id = uuid4()

        with Session(engine, future=True) as session:
            insert_summary(session, summary_id, "Original text.")
            session.commit()

        repo.update_summary_text(summary_id=summary_id, new_text="Updated text.")

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT text FROM summaries WHERE id = :id"),
                {"id": summary_id},
            ).one()

        assert row.text == "Updated text."

    def test_preserves_other_fields(self, repo, engine):
        summary_id = uuid4()

        with Session(engine, future=True) as session:
            insert_summary(
                session,
                summary_id,
                "Original.",
                datetime_val="+1700-00-00T00:00:00Z",
                calendar_model="Q1985727",
                precision=9,
            )
            session.commit()

        repo.update_summary_text(summary_id=summary_id, new_text="New text.")

        with Session(engine, future=True) as session:
            row = session.execute(
                text(
                    "SELECT datetime, calendar_model, precision FROM summaries WHERE id = :id"
                ),
                {"id": summary_id},
            ).one()

        assert row.datetime == "+1700-00-00T00:00:00Z"


class TestAddCitationToSummary:
    def test_returns_citation_id(self, repo, engine):
        summary_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_source(session, source_id)
            insert_summary(session, summary_id, "Summary for citation.")
            session.commit()

        citation_id = repo.add_citation_to_summary(
            summary_id=summary_id,
            source_id=source_id,
            citation_text="p. 42",
        )

        assert citation_id is not None

    def test_stores_citation_text(self, repo, engine):
        summary_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_source(session, source_id)
            insert_summary(session, summary_id, "Summary for text check.")
            session.commit()

        citation_id = repo.add_citation_to_summary(
            summary_id=summary_id,
            source_id=source_id,
            citation_text="Burney, vol. 1, p. 42",
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT text FROM citations WHERE id = :id"),
                {"id": citation_id},
            ).one()

        assert row.text == "Burney, vol. 1, p. 42"

    def test_stores_page_num(self, repo, engine):
        summary_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_source(session, source_id)
            insert_summary(session, summary_id, "Summary for page num.")
            session.commit()

        citation_id = repo.add_citation_to_summary(
            summary_id=summary_id,
            source_id=source_id,
            citation_text="citation",
            page_num=42,
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT page_num FROM citations WHERE id = :id"),
                {"id": citation_id},
            ).one()

        assert row.page_num == 42

    def test_stores_access_date(self, repo, engine):
        summary_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_source(session, source_id)
            insert_summary(session, summary_id, "Summary for access date.")
            session.commit()

        citation_id = repo.add_citation_to_summary(
            summary_id=summary_id,
            source_id=source_id,
            citation_text="citation",
            access_date="2026-03-11",
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT access_date FROM citations WHERE id = :id"),
                {"id": citation_id},
            ).one()

        assert row.access_date == "2026-03-11"

    def test_links_to_summary(self, repo, engine):
        summary_id = uuid4()
        source_id = uuid4()

        with Session(engine, future=True) as session:
            insert_source(session, source_id)
            insert_summary(session, summary_id, "Summary for link check.")
            session.commit()

        citation_id = repo.add_citation_to_summary(
            summary_id=summary_id,
            source_id=source_id,
            citation_text="citation",
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT summary_id FROM citations WHERE id = :id"),
                {"id": citation_id},
            ).one()

        assert row.summary_id == summary_id


class TestCreateSourceWithSession:
    def test_creates_source(self, repo, engine):
        source_id = uuid4()

        repo.create_source_with_session(
            id=source_id,
            title="A General History of Music",
            author="Charles Burney",
            publisher="Payne and Son",
            pub_date="1789",
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT id, title FROM sources WHERE id = :id"),
                {"id": source_id},
            ).one()

        assert row.id == source_id

    def test_stores_title(self, repo, engine):
        source_id = uuid4()

        repo.create_source_with_session(
            id=source_id,
            title="Musical History",
            author="Author",
            publisher="Publisher",
            pub_date=None,
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT title FROM sources WHERE id = :id"),
                {"id": source_id},
            ).one()

        assert row.title == "Musical History"

    def test_stores_author(self, repo, engine):
        source_id = uuid4()

        repo.create_source_with_session(
            id=source_id,
            title="Title",
            author="Dr. Charles Burney",
            publisher="Publisher",
            pub_date=None,
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT author FROM sources WHERE id = :id"),
                {"id": source_id},
            ).one()

        assert row.author == "Dr. Charles Burney"

    def test_handles_null_pub_date(self, repo, engine):
        source_id = uuid4()

        repo.create_source_with_session(
            id=source_id,
            title="Title",
            author="Author",
            publisher="Publisher",
            pub_date=None,
        )

        with Session(engine, future=True) as session:
            row = session.execute(
                text("SELECT pub_date FROM sources WHERE id = :id"),
                {"id": source_id},
            ).one()

        assert row.pub_date is None

    def test_adds_source_to_trie(self, repo, engine):
        source_id = uuid4()

        repo.create_source_with_session(
            id=source_id,
            title="A General History of Music",
            author="Charles Burney",
            publisher="Payne and Son",
            pub_date="1789",
        )

        trie_results = repo._source_trie.find("A General History")

        assert len(trie_results) > 0
