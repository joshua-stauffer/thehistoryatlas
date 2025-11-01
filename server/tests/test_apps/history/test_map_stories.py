from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from the_history_atlas.apps.domain.core import (
    LatLong,
    CalendarDate,
    MapStory,
    Precision,
)


@pytest.fixture
def setup_test_data(history_db):
    """Set up test data for map stories tests"""
    with Session(history_db._engine, future=True) as session:
        # Create test data
        person_id = uuid4()
        place_id = uuid4()
        time_id = uuid4()
        summary_id = uuid4()
        name_id = uuid4()
        tag_instance_id = uuid4()

        # Create person tag
        session.execute(
            text(
                """
                INSERT INTO tags (id, type)
                VALUES (:id, :type)
                """
            ),
            {"id": person_id, "type": "PERSON"},
        )

        session.execute(
            text(
                """
                INSERT INTO people (id)
                VALUES (:id)
                """
            ),
            {"id": person_id},
        )

        # Create name for person
        session.execute(
            text(
                """
                INSERT INTO names (id, name)
                VALUES (:id, :name)
                """
            ),
            {"id": name_id, "name": "Test Person"},
        )

        # Link name to person tag
        session.execute(
            text(
                """
                INSERT INTO tag_names (tag_id, name_id)
                VALUES (:tag_id, :name_id)
                """
            ),
            {"tag_id": person_id, "name_id": name_id},
        )

        # Create story name for person
        session.execute(
            text(
                """
                INSERT INTO story_names (id, tag_id, name, lang, description)
                VALUES (:id, :tag_id, :name, :lang, :description)
                """
            ),
            {
                "id": uuid4(),
                "tag_id": person_id,
                "name": "Test Person Story",
                "lang": "en",
                "description": "A test story",
            },
        )

        # Create place tag
        session.execute(
            text(
                """
                INSERT INTO tags (id, type)
                VALUES (:id, :type)
                """
            ),
            {"id": place_id, "type": "PLACE"},
        )

        session.execute(
            text(
                """
                INSERT INTO places (id, latitude, longitude)
                VALUES (:id, :latitude, :longitude)
                """
            ),
            {"id": place_id, "latitude": 0.0, "longitude": 0.0},
        )

        # Create time tag
        session.execute(
            text(
                """
                INSERT INTO tags (id, type)
                VALUES (:id, :type)
                """
            ),
            {"id": time_id, "type": "TIME"},
        )

        session.execute(
            text(
                """
                INSERT INTO times (id, datetime, calendar_model, precision)
                VALUES (:id, :datetime, :calendar_model, :precision)
                """
            ),
            {
                "id": time_id,
                "datetime": "+2000-01-01T00:00:00Z",
                "calendar_model": "gregorian",
                "precision": 9,  # year precision
            },
        )

        # Create summary
        session.execute(
            text(
                """
                INSERT INTO summaries (id, text)
                VALUES (:id, :text)
                """
            ),
            {"id": summary_id, "text": "Test summary"},
        )

        # Create tag instances linking summary to person, place, and time
        session.execute(
            text(
                """
                INSERT INTO tag_instances (id, summary_id, tag_id, story_order)
                VALUES (:id, :summary_id, :tag_id, :story_order)
                """
            ),
            {
                "id": uuid4(),
                "summary_id": summary_id,
                "tag_id": person_id,
                "story_order": 1,
            },
        )

        session.execute(
            text(
                """
                INSERT INTO tag_instances (id, summary_id, tag_id, story_order)
                VALUES (:id, :summary_id, :tag_id, :story_order)
                """
            ),
            {
                "id": uuid4(),
                "summary_id": summary_id,
                "tag_id": place_id,
                "story_order": 2,
            },
        )

        session.execute(
            text(
                """
                INSERT INTO tag_instances (id, summary_id, tag_id, story_order)
                VALUES (:id, :summary_id, :tag_id, :story_order)
                """
            ),
            {
                "id": uuid4(),
                "summary_id": summary_id,
                "tag_id": time_id,
                "story_order": 3,
            },
        )

        session.commit()

        return {
            "person_id": person_id,
            "place_id": place_id,
            "time_id": time_id,
            "summary_id": summary_id,
        }


def test_get_people_stories_by_bounds_and_time(history_db, setup_test_data):
    """Test getting people stories by geographic bounds and time window"""
    # Create test bounds
    min_bound = LatLong(latitude=-1.0, longitude=-1.0)
    max_bound = LatLong(latitude=1.0, longitude=1.0)

    # Create test calendar date
    calendar_date = CalendarDate(
        datetime="+2000-01-01T00:00:00Z",
        calendar="gregorian",
        precision=11,
    )

    # Get stories
    stories = history_db.get_people_stories_by_bounds_and_time(
        min_bound=min_bound,
        max_bound=max_bound,
        calendar_date=calendar_date,
    )

    # Verify results
    assert len(stories) == 1
    story = stories[0]
    assert story.title == "Test Person Story"
    assert story.description == "A test story"


def test_get_people_stories_by_bounds_and_time_no_results(history_db, setup_test_data):
    """Test getting people stories by bounds and time with no results"""
    # Test with bounds that don't include our test data
    min_bound = LatLong(latitude=0.0, longitude=0.0)
    max_bound = LatLong(latitude=1.0, longitude=1.0)
    calendar_date = CalendarDate(
        datetime="+2023-06-01T00:00:00Z",
        calendar="gregorian",
        precision=11,
    )

    stories = history_db.get_people_stories_by_bounds_and_time(
        min_bound=min_bound,
        max_bound=max_bound,
        calendar_date=calendar_date,
    )

    assert len(stories) == 0


def test_get_people_stories_by_bounds_and_time_wrong_year(history_db, setup_test_data):
    """Test getting people stories by bounds and time with wrong year"""
    # Test with correct bounds but wrong year
    min_bound = LatLong(latitude=39.0, longitude=-75.0)
    max_bound = LatLong(latitude=41.0, longitude=-73.0)
    calendar_date = CalendarDate(
        datetime="+2024-06-01T00:00:00Z",
        calendar="gregorian",
        precision=11,
    )

    stories = history_db.get_people_stories_by_bounds_and_time(
        min_bound=min_bound,
        max_bound=max_bound,
        calendar_date=calendar_date,
    )

    assert len(stories) == 0
