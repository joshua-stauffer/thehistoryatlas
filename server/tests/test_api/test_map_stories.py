from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from the_history_atlas.api.types.history import (
    MapStoryRequest,
    MapStory,
    LatLong,
    CalendarDate,
    Point,
)
from the_history_atlas.main import get_app


@pytest.fixture
def client(cleanup_db):
    return TestClient(get_app())


@pytest.fixture
def setup_test_data(db_session: Session):
    """Set up test data for map stories tests"""
    # Create test data
    person_id = uuid4()
    place_id = uuid4()
    time_id = uuid4()
    summary_id = uuid4()
    name_id = uuid4()
    story_id = uuid4()

    # Create summary
    db_session.execute(
        text(
            """
            INSERT INTO summaries (id, text)
            VALUES (:id, :text)
            """
        ),
        {"id": summary_id, "text": "Test summary"},
    )

    # Create person tag
    db_session.execute(
        text(
            """
            INSERT INTO tags (id, type)
            VALUES (:id, :type)
            """
        ),
        {"id": person_id, "type": "PERSON"},
    )

    # Create person record
    db_session.execute(
        text(
            """
            INSERT INTO people (id)
            VALUES (:id)
            """
        ),
        {"id": person_id},
    )

    # Create tag instance linking summary and person
    db_session.execute(
        text(
            """
            INSERT INTO tag_instances (id, summary_id, tag_id, start_char, stop_char, story_order)
            VALUES (:id, :summary_id, :tag_id, :start_char, :stop_char, :story_order)
            """
        ),
        {
            "id": uuid4(),
            "summary_id": summary_id,
            "tag_id": person_id,
            "start_char": 0,
            "stop_char": 10,
            "story_order": 1,
        },
    )

    # Create story name for person
    db_session.execute(
        text(
            """
            INSERT INTO story_names (id, tag_id, name, lang, description)
            VALUES (:id, :tag_id, :name, :lang, :description)
            """
        ),
        {
            "id": story_id,
            "tag_id": person_id,
            "name": "Test Name",
            "lang": "en",
            "description": "Test summary",
        },
    )

    # Create place tag
    db_session.execute(
        text(
            """
            INSERT INTO tags (id, type)
            VALUES (:id, :type)
            """
        ),
        {"id": place_id, "type": "PLACE"},
    )

    # Create place record
    db_session.execute(
        text(
            """
            INSERT INTO places (id, latitude, longitude)
            VALUES (:id, :latitude, :longitude)
            """
        ),
        {"id": place_id, "latitude": 40.7128, "longitude": -74.0060},
    )

    # Create tag instance linking summary and place
    db_session.execute(
        text(
            """
            INSERT INTO tag_instances (id, summary_id, tag_id, start_char, stop_char, story_order)
            VALUES (:id, :summary_id, :tag_id, :start_char, :stop_char, :story_order)
            """
        ),
        {
            "id": uuid4(),
            "summary_id": summary_id,
            "tag_id": place_id,
            "start_char": 11,
            "stop_char": 20,
            "story_order": 2,
        },
    )

    # Create time tag
    db_session.execute(
        text(
            """
            INSERT INTO tags (id, type)
            VALUES (:id, :type)
            """
        ),
        {"id": time_id, "type": "TIME"},
    )

    # Create time record
    db_session.execute(
        text(
            """
            INSERT INTO times (id, datetime, calendar_model, precision)
            VALUES (:id, :datetime, :calendar_model, :precision)
            """
        ),
        {
            "id": time_id,
            "datetime": "+2024-01-01T00:00:00Z",
            "calendar_model": "gregorian",
            "precision": 11,
        },
    )

    # Create tag instance linking summary and time
    db_session.execute(
        text(
            """
            INSERT INTO tag_instances (id, summary_id, tag_id, start_char, stop_char, story_order)
            VALUES (:id, :summary_id, :tag_id, :start_char, :stop_char, :story_order)
            """
        ),
        {
            "id": uuid4(),
            "summary_id": summary_id,
            "tag_id": time_id,
            "start_char": 21,
            "stop_char": 30,
            "story_order": 3,
        },
    )

    # Commit the transaction
    db_session.commit()

    return {
        "summary_id": summary_id,
        "story_id": person_id,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "datetime": "+2024-01-01T00:00:00Z",
    }


def test_get_map_stories_by_bounds_and_time(client, setup_test_data):
    """Test getting map stories by bounds and time"""
    request = MapStoryRequest(
        northwest_bound=LatLong(latitude=41.0, longitude=-75.0),
        southeast_bound=LatLong(latitude=40.0, longitude=-73.0),
        date=CalendarDate(
            datetime="+2024-01-01T00:00:00Z",
            calendar="gregorian",
            precision=11,  # day precision
        ),
    )

    response = client.post("/map/stories", json=request.model_dump())
    assert response.status_code == 200
    stories = response.json()
    assert len(stories) == 1
    story = stories[0]
    assert story["storyId"] == str(setup_test_data["story_id"])
    assert story["point"]["latitude"] == setup_test_data["latitude"]
    assert story["point"]["longitude"] == setup_test_data["longitude"]
    assert story["date"]["datetime"] == setup_test_data["datetime"]


def test_get_map_stories_outside_bounds(client: TestClient, setup_test_data):
    """Test getting map stories outside geographic bounds."""
    request = MapStoryRequest(
        northwest_bound=LatLong(latitude=39.0, longitude=-73.0),
        southeast_bound=LatLong(latitude=38.0, longitude=-72.0),
        date=CalendarDate(
            datetime=setup_test_data["datetime"],
            calendar="gregorian",
            precision=11,  # day precision
        ),
    )

    response = client.post("/map/stories", json=request.model_dump())
    assert response.status_code == 200
    stories = response.json()
    assert len(stories) == 0


def test_get_map_stories_different_time(client: TestClient, setup_test_data):
    """Test getting map stories at a different time."""
    request = MapStoryRequest(
        northwest_bound=LatLong(latitude=41.0, longitude=-75.0),
        southeast_bound=LatLong(latitude=40.0, longitude=-73.0),
        date=CalendarDate(
            datetime=datetime(1999, 1, 1, tzinfo=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            calendar="gregorian",
            precision=11,  # day precision
        ),
    )

    response = client.post("/map/stories", json=request.model_dump())
    assert response.status_code == 200
    stories = response.json()
    assert len(stories) == 0
