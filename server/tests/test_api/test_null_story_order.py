import pytest
from sqlalchemy import text
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from httpx import QueryParams

from the_history_atlas.api.types.history import Story

from tests.test_api.test_rest import (
    create_event,
    create_person,
    create_place,
    create_time,
    get_all_events_in_order,
    client,
    auth_headers,
)


@pytest.mark.parametrize("EVENT_COUNT", [3])
def test_null_story_order(
    client: TestClient, db_session: Session, EVENT_COUNT, auth_headers: dict
):
    """Test that the application works correctly with null story_order values."""
    # arrange
    person = create_person(client, auth_headers)
    times = [create_time(client, auth_headers) for _ in range(EVENT_COUNT)]
    places = [create_place(client, auth_headers) for _ in range(EVENT_COUNT)]

    # Create events with normal story_order values
    events = [
        create_event(
            person=person,
            place=place,
            time=time,
            client=client,
            auth_headers=auth_headers,
        )
        for time, place in zip(times, places)
    ]

    # Add a tag instance with null story_order
    null_summary_id = uuid4()
    null_tag_instance_id = uuid4()
    null_summary = "Test summary with null story_order"

    # Insert a summary
    db_session.execute(
        text(
            """
            INSERT INTO summaries (id, text)
            VALUES (:id, :text)
            """
        ),
        {"id": null_summary_id, "text": null_summary},
    )

    # Insert a tag instance with null story_order
    db_session.execute(
        text(
            """
            INSERT INTO tag_instances (id, start_char, stop_char, summary_id, tag_id, story_order)
            VALUES (:id, :start_char, :stop_char, :summary_id, :tag_id, NULL)
            """
        ),
        {
            "id": null_tag_instance_id,
            "start_char": 0,
            "stop_char": 5,
            "summary_id": null_summary_id,
            "tag_id": person.id,
        },
    )

    # act
    response = client.get(
        "/history",
        params=QueryParams(
            storyId=person.id,
        ),
    )

    # assert
    assert response.status_code == 200
    story = Story.model_validate(response.json())

    # We should only get the non-null story_order events
    assert len(story.events) == EVENT_COUNT

    summaries = [event.text for event in story.events]
    assert null_summary not in summaries
