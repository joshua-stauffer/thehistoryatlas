from datetime import datetime, timezone
import random
from typing import Literal, Dict
from uuid import uuid4, UUID
from faker import Faker

import pytest
from fastapi.testclient import TestClient
from httpx import QueryParams
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import row
from sqlalchemy.orm import Session, scoped_session

from the_history_atlas.api.types.history import Story
from the_history_atlas.api.types.tags import (
    WikiDataPersonInput,
    WikiDataPlaceInput,
    WikiDataTimeInput,
    WikiDataTagsInput,
    WikiDataTagPointer,
    WikiDataEventInput,
    WikiDataCitationInput,
    TagInput,
    WikiDataPersonOutput,
    WikiDataPlaceOutput,
    WikiDataTimeOutput,
    WikiDataEventOutput,
)
from the_history_atlas.apps.domain.core import StoryOrder
from the_history_atlas.main import get_app

fake = Faker()


def generate_wikidata_id() -> str:
    """Generate a random Wikidata Q identifier."""
    return f"Q{random.randint(1, 99999999)}"


def generate_wikidata_url(wikidata_id: str) -> str:
    """Generate a Wikidata URL from a Q identifier."""
    return f"https://www.wikidata.org/wiki/{wikidata_id}"


def _generate_fake_place() -> WikiDataPlaceInput:
    """Generate a fake WikiData place entry."""
    wikidata_id = generate_wikidata_id()
    return WikiDataPlaceInput(
        wikidata_id=wikidata_id,
        wikidata_url=generate_wikidata_url(wikidata_id),
        name=fake.city(),
        latitude=float(fake.latitude()),
        longitude=float(fake.longitude()),
    )


def create_place(client: TestClient, auth_headers: dict) -> WikiDataPlaceOutput:
    place = _generate_fake_place()
    response = client.post(
        "/wikidata/places", data=place.model_dump_json(), headers=auth_headers
    )
    return WikiDataPlaceOutput.model_validate(response.json())


def _generate_fake_person() -> WikiDataPersonOutput:
    """Generate a fake WikiData person entry."""
    wikidata_id = generate_wikidata_id()
    return WikiDataPersonInput(
        wikidata_id=wikidata_id,
        wikidata_url=generate_wikidata_url(wikidata_id),
        name=fake.name(),
    )


def create_person(client: TestClient, auth_headers: dict) -> WikiDataPersonOutput:
    person = _generate_fake_person()
    person_output = client.post(
        "/wikidata/people", data=person.model_dump_json(), headers=auth_headers
    )
    return WikiDataPersonOutput.model_validate(person_output.json())


def _generate_fake_time(
    start_date: str | None = None, end_date: str | None = None
) -> WikiDataTimeInput:
    """Generate a fake WikiData time entry."""
    if not start_date:
        start_date = "-50y"
    if not end_date:
        end_date = "now"
    wikidata_id = generate_wikidata_id()
    date = fake.date_time_between(start_date=start_date, end_date=end_date)

    date_str = date.strftime("%d %B %Y")

    return WikiDataTimeInput(
        wikidata_id=wikidata_id,
        wikidata_url=generate_wikidata_url(wikidata_id),
        name=date_str,
        date=date,
        calendar_model="https://www.wikidata.org/wiki/Q12138",  # Gregorian calendar
        precision=random.randint(7, 11),
    )


def create_time(
    client: TestClient,
    auth_headers: dict,
    start_date: str | None = None,
    end_date: str | None = None,
) -> WikiDataTimeOutput:
    time = _generate_fake_time(start_date=start_date, end_date=end_date)

    time_output = client.post(
        "/wikidata/times", data=time.model_dump_json(), headers=auth_headers
    )
    return WikiDataTimeOutput.model_validate(time_output.json())


def _generate_fake_event(
    person: WikiDataPersonOutput, place: WikiDataPlaceOutput, time: WikiDataTimeOutput
) -> WikiDataEventInput:
    """
    Generate a fake WikiData event that combines a person, place, and time.
    Returns a properly formatted WikiDataEventInput with appropriate tags.
    """
    # Generate a natural-sounding summary using the provided entities
    event_types = [
        "was born",
        "visited",
        "gave a speech",
        "published their first work",
        "established their residence",
        "completed their masterpiece",
    ]
    event_type = random.choice(event_types)

    summary_text = f"{person.name} {event_type} on {time.name} in {place.name}."

    # Create tags for each entity
    tags = [
        TagInput(
            id=person.id,
            name=person.name,
            start_char=summary_text.find(person.name),
            stop_char=summary_text.find(person.name) + len(person.name),
        ),
        TagInput(
            id=place.id,
            name=place.name,
            start_char=summary_text.find(place.name),
            stop_char=summary_text.find(place.name) + len(place.name),
        ),
        TagInput(
            id=time.id,
            name=time.name,
            start_char=summary_text.find(time.name),
            stop_char=summary_text.find(time.name) + len(time.name),
        ),
    ]

    # Create citation using the person's WikiData information
    citation = WikiDataCitationInput(
        access_date=datetime.now(timezone.utc),
        wikidata_item_id=person.wikidata_id,
        wikidata_item_title=person.name,
        wikidata_item_url=person.wikidata_url,
    )

    return WikiDataEventInput(summary=summary_text, tags=tags, citation=citation)


def create_event(
    client: TestClient,
    person: WikiDataPersonOutput,
    place: WikiDataPlaceOutput,
    time: WikiDataTimeOutput,
    auth_headers: dict[str, str],
) -> WikiDataEventOutput:
    event = _generate_fake_event(person, place, time)
    event_output = client.post(
        "/wikidata/events", data=event.model_dump_json(), headers=auth_headers
    )
    return WikiDataEventOutput.model_validate(event_output.json())


@pytest.fixture
def client(cleanup_db):
    return TestClient(get_app())


@pytest.fixture
def auth_headers(active_token: str, seed_accounts: None) -> Dict[str, str]:
    return {"Authorization": f"Bearer {active_token}"}


def test_create_person(client: TestClient, auth_headers: dict) -> None:
    input = WikiDataPersonInput(
        wikidata_id="Q1339",
        wikidata_url="https://www.wikidata.org/wiki/Q1339",
        name="Johann Sebastian Bach",
    )

    response = client.post(
        "/wikidata/people", data=input.model_dump_json(), headers=auth_headers
    )
    assert response.status_code == 200, response.text


def test_create_place(client: TestClient, auth_headers: dict) -> None:
    input = WikiDataPlaceInput(
        wikidata_id="Q7070",
        wikidata_url="https://www.wikidata.org/wiki/Q7070",
        name="Eisenach",
        latitude=50.974722,
        longitude=10.324444,
    )

    response = client.post(
        "/wikidata/places", data=input.model_dump_json(), headers=auth_headers
    )
    assert response.status_code == 200, response.text


def test_create_time(client: TestClient, auth_headers: dict) -> None:
    input = WikiDataTimeInput(
        wikidata_id="Q69125241",
        wikidata_url="https://www.wikidata.org/wiki/Q69125241",
        name="31 March 1685",
        date=datetime(year=1685, month=3, day=31),
        calendar_model="https://www.wikidata.org/wiki/Q12138",
        precision=11,
    )

    response = client.post(
        "/wikidata/times", data=input.model_dump_json(), headers=auth_headers
    )
    assert response.status_code == 200, response.text


@pytest.fixture
def wikidata_ids(engine) -> list[str]:
    tags = [
        {
            "id": uuid4(),
            "wikidata_id": "Q1339",
            "type": "PERSON",
        },
        {
            "id": uuid4(),
            "wikidata_id": "Q7070",
            "type": "PLACE",
        },
        {
            "id": uuid4(),
            "wikidata_id": "Q69125241",
            "type": "TIME",
        },
    ]
    with Session(engine) as session:
        session.execute(
            text(
                """
                insert into tags (id, wikidata_id, type) values (:id, :wikidata_id, :type);
            """
            ),
            tags,
        )
        session.commit()
    return [
        WikiDataTagPointer(
            id=tag["id"],
            wikidata_id=tag["wikidata_id"],
        )
        for tag in tags
    ]


def test_get_tags_by_wikidata_ids_success(
    client: TestClient, wikidata_ids: list[WikiDataTagPointer], auth_headers: dict
) -> None:
    response = client.get(
        "/wikidata/tags",
        params={"wikidata_ids": [pointer.wikidata_id for pointer in wikidata_ids]},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "wikidata_ids": [o.model_dump(mode="json") for o in wikidata_ids]
    }


def test_get_tags_by_wikidata_ids_missing_tags(
    client: TestClient, wikidata_ids: list[WikiDataTagPointer], auth_headers: dict
) -> None:
    extra_id = "Q8943682"
    existing_ids = [pointer.wikidata_id for pointer in wikidata_ids]
    params = {"wikidata_ids": [*existing_ids, extra_id]}
    existing_pointers = [o.model_dump(mode="json") for o in wikidata_ids]
    expected_response = [
        *existing_pointers,
        {"wikidata_id": extra_id, "id": None},
    ]
    response = client.get("/wikidata/tags", params=params, headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json() == {"wikidata_ids": expected_response}


def test_create_event(client: TestClient, auth_headers: dict):
    person_input = WikiDataPersonInput(
        wikidata_id="Q1339",
        wikidata_url="https://www.wikidata.org/wiki/Q1339",
        name="Johann Sebastian Bach",
    )

    created_person_output = client.post(
        "/wikidata/people", data=person_input.model_dump_json(), headers=auth_headers
    )
    created_person = WikiDataPersonOutput.model_validate(created_person_output.json())

    place_input = WikiDataPlaceInput(
        wikidata_id="Q7070",
        wikidata_url="https://www.wikidata.org/wiki/Q7070",
        name="Eisenach",
        latitude=50.974722,
        longitude=10.324444,
    )

    created_place_output = client.post(
        "/wikidata/places", data=place_input.model_dump_json(), headers=auth_headers
    )
    created_place = WikiDataPlaceOutput.model_validate(created_place_output.json())

    time_input = WikiDataTimeInput(
        wikidata_id="Q69125241",
        wikidata_url="https://www.wikidata.org/wiki/Q69125241",
        name="March 31st, 1685",
        date=datetime(year=1685, month=3, day=31),
        calendar_model="https://www.wikidata.org/wiki/Q12138",
        precision=11,
    )

    created_time_output = client.post(
        "/wikidata/times", data=time_input.model_dump_json(), headers=auth_headers
    )
    created_time = WikiDataTimeOutput.model_validate(created_time_output.json())

    summary_text = "Johann Sebastian Bach was born on March 31st, 1685 in Eisenach."
    event_input = WikiDataEventInput(
        summary=summary_text,
        citation=WikiDataCitationInput(
            access_date=datetime.now(timezone.utc),
            wikidata_item_id="Q1339",
            wikidata_item_title="Johann Sebastian Bach",
            wikidata_item_url="https://www.wikidata.org/wiki/Q1339",
        ),
        tags=[
            TagInput(
                id=created_person.id,
                name=created_person.name,
                start_char=summary_text.find(created_person.name),
                stop_char=summary_text.find(created_person.name)
                + len(created_person.name),
            ),
            TagInput(
                id=created_place.id,
                name=created_place.name,
                start_char=summary_text.find(created_place.name),
                stop_char=summary_text.find(created_place.name)
                + len(created_place.name),
            ),
            TagInput(
                id=created_time.id,
                name=created_time.name,
                start_char=summary_text.find(created_time.name),
                stop_char=summary_text.find(created_time.name) + len(created_time.name),
            ),
        ],
    )
    response = client.post(
        "/wikidata/events", data=event_input.model_dump_json(), headers=auth_headers
    )
    assert response.status_code == 200, response.text


@pytest.fixture
def seed_story(client: TestClient, auth_headers: dict):
    person = create_person(client)
    times = [create_time(client) for _ in range(10)]
    places = [create_place(client) for _ in range(10)]
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


@pytest.mark.parametrize("EVENT_COUNT", [3, 10, 50])
def test_create_stories_order(
    client: TestClient, db_session, EVENT_COUNT, auth_headers: dict
):
    # arrange
    person = create_person(client, auth_headers)
    times = [create_time(client, auth_headers) for _ in range(EVENT_COUNT)]
    places = [create_place(client, auth_headers) for _ in range(EVENT_COUNT)]
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

    # act
    response = client.get("/api/history")
    assert response.status_code == 200
    story = Story.model_validate(response.json())

    # assert
    rows = db_session.execute(
        text(
            """
            select 
                summaries.id as summary_id,
                tag_instances.story_order as story_order,
                (
                    select times.datetime as datetime
                    from summaries as s2
                    join tag_instances as ti2 on ti2.summary_id = s2.id
                    join tags as t2 on t2.id = ti2.tag_id and t2.type = 'TIME'
                    join times on times.id = t2.id
                    where s2.id = summaries.id
                    order by times.datetime, times.precision
                    limit 1
                ) as datetime,
                (
                    select times.precision
                    from summaries as s2
                    join tag_instances as ti2 on ti2.summary_id = s2.id
                    join tags as t2 on t2.id = ti2.tag_id and t2.type = 'TIME'
                    join times on times.id = t2.id
                    where s2.id = summaries.id
                    order by times.datetime, times.precision
                    limit 1
                ) as precision
            from summaries
            join tag_instances on tag_instances.summary_id = summaries.id
            where summaries.id in (
                select summary_id 
                from tag_instances 
                where tag_id = :tag_id
            )
            and tag_instances.tag_id = :tag_id
            order by story_order;
        """
        ),
        {"tag_id": person.id},
    ).all()
    row_tuples = [(row.story_order, row.datetime) for row in rows]
    assert len(row_tuples) == EVENT_COUNT
    assert sorted(row_tuples) == row_tuples
    for i, (story_order, _) in enumerate(row_tuples):
        assert i == story_order


def get_all_events_in_order(
    db_session: scoped_session, tag_id: UUID
) -> list[StoryOrder]:
    rows = db_session.execute(
        text(
            """
            select 
                summaries.id as summary_id,
                tag_instances.story_order as story_order,
                (
                    select times.datetime as datetime
                    from summaries as s2
                    join tag_instances as ti2 on ti2.summary_id = s2.id
                    join tags as t2 on t2.id = ti2.tag_id and t2.type = 'TIME'
                    join times on times.id = t2.id
                    where s2.id = summaries.id
                    order by times.datetime, times.precision
                    limit 1
                ) as datetime,
                (
                    select times.precision
                    from summaries as s2
                    join tag_instances as ti2 on ti2.summary_id = s2.id
                    join tags as t2 on t2.id = ti2.tag_id and t2.type = 'TIME'
                    join times on times.id = t2.id
                    where s2.id = summaries.id
                    order by times.datetime, times.precision
                    limit 1
                ) as precision
            from summaries
            join tag_instances on tag_instances.summary_id = summaries.id
            where summaries.id in (
                select summary_id 
                from tag_instances 
                where tag_id = :tag_id
            )
            and tag_instances.tag_id = :tag_id
            order by story_order;
        """
        ),
        {"tag_id": tag_id},
    ).all()
    return [StoryOrder.model_validate(row, from_attributes=True) for row in rows]


class TestGetHistory:
    @pytest.mark.parametrize("EVENT_COUNT", [3, 10, 50])
    def test_no_params(
        self, client: TestClient, EVENT_COUNT, auth_headers: dict
    ) -> None:
        # arrange
        person = create_person(client, auth_headers)
        times = [create_time(client, auth_headers) for _ in range(EVENT_COUNT)]
        places = [create_place(client, auth_headers) for _ in range(EVENT_COUNT)]
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

        # act
        response = client.get("/api/history")

        # assert
        assert response.status_code == 200
        story = Story.model_validate(response.json())
        time_tags = sorted([time.date for time in times])
        for event, time in zip(story.events, time_tags):
            assert event.date.datetime.date() == time.date()

    def test_with_params(
        self, client: TestClient, db_session: scoped_session, auth_headers: dict
    ) -> None:
        """When passing in params but not next/prev, expect the event
        we pass in to be returned in the middle of the list."""
        # arrange
        EVENT_COUNT = 40
        person = create_person(client, auth_headers)
        times = [create_time(client, auth_headers) for _ in range(EVENT_COUNT)]
        places = [create_place(client, auth_headers) for _ in range(EVENT_COUNT)]
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
        story_in_order = get_all_events_in_order(
            db_session=db_session, tag_id=person.id
        )
        BASE_INDEX = 20  # index of the story we give as param
        START_INDEX = BASE_INDEX - 10  # start of range we expect
        END_INDEX = BASE_INDEX + 11  # end of range we expect (exclusive)
        start_event = story_in_order[BASE_INDEX]
        expected_events = story_in_order[START_INDEX:END_INDEX]

        # act
        response = client.get(
            "/api/history",
            params=QueryParams(
                storyId=person.id,
                eventId=start_event.summary_id,
            ),
        )

        # assert
        assert response.status_code == 200
        story = Story.model_validate(response.json())
        assert len(story.events) == 21
        # expect that the requested event is returned in the middle
        for event, expected_event in zip(story.events, expected_events):
            assert event.date.datetime.date() == expected_event.datetime.date()
            assert event.date.precision == expected_event.precision
            assert event.id == expected_event.summary_id

    def test_with_next(
        self, client: TestClient, db_session: scoped_session, auth_headers: dict
    ) -> None:
        # arrange
        EVENT_COUNT = 20
        person = create_person(client, auth_headers)
        times = [create_time(client, auth_headers) for _ in range(EVENT_COUNT)]
        places = [create_place(client, auth_headers) for _ in range(EVENT_COUNT)]
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
        story_in_order = get_all_events_in_order(
            db_session=db_session, tag_id=person.id
        )
        BASE_INDEX = 5  # index of the story we give as param
        START_INDEX = BASE_INDEX + 1  # index of event we expect to get back first
        END_INDEX = BASE_INDEX + 11  # index of event we expect to get back last
        start_event = story_in_order[BASE_INDEX]
        expected_events = story_in_order[START_INDEX:END_INDEX]

        # act
        response = client.get(
            "/api/history",
            params=QueryParams(
                storyId=person.id, eventId=start_event.summary_id, direction="next"
            ),
        )

        # assert
        assert response.status_code == 200
        story = Story.model_validate(response.json())
        assert len(story.events) == 10
        # expect that the requested event is returned in the middle
        for event, expected_event in zip(story.events, expected_events):
            assert event.date.datetime.date() == expected_event.datetime.date()
            assert event.date.precision == expected_event.precision
            assert event.id == expected_event.summary_id

    def test_next_person_to_place_story(
        self, client: TestClient, db_session: scoped_session, auth_headers: dict
    ) -> None:
        # arrange
        # setup a person's story
        PERSON_EVENT_COUNT = 4
        PERSON_END_DATE = "-20y"
        person = create_person(client, auth_headers)
        person_story_times = [
            create_time(client, end_date=PERSON_END_DATE, auth_headers=auth_headers)
            for _ in range(PERSON_EVENT_COUNT)
        ]
        person_story_places = [
            create_place(client, auth_headers) for _ in range(PERSON_EVENT_COUNT)
        ]
        time_place_tuples = list(zip(person_story_times, person_story_places))
        [
            create_event(
                person=person,
                place=place,
                time=time,
                client=client,
                auth_headers=auth_headers,
            )
            for time, place in time_place_tuples
        ]
        person_story_in_order = get_all_events_in_order(
            db_session=db_session, tag_id=person.id
        )
        person_event_ids = {
            story_order.summary_id for story_order in person_story_in_order
        }

        # setup a place's story
        PLACE_EVENT_COUNT = 7
        PLACE_START_DATE = "-19y"
        sorted_time_place_tuples = sorted(time_place_tuples, key=lambda t: t[0].date)
        last_time_place = sorted_time_place_tuples[-1]
        place = last_time_place[1]
        place_story_people = [
            create_person(client, auth_headers) for _ in range(PLACE_EVENT_COUNT)
        ]
        place_story_times = [
            create_time(client, start_date=PLACE_START_DATE, auth_headers=auth_headers)
            for _ in range(PLACE_EVENT_COUNT)
        ]
        [
            create_event(
                person=person,
                place=place,
                time=time,
                client=client,
                auth_headers=auth_headers,
            )
            for time, person in zip(place_story_times, place_story_people)
        ]
        place_story_in_order = get_all_events_in_order(
            db_session=db_session, tag_id=place.id
        )
        place_event_ids = {
            story_order.summary_id for story_order in place_story_in_order
        }

        # setup the list of events we expect to get back
        # the stories overlap on their last/first event, so we start the place story at 1
        story_in_order = person_story_in_order + place_story_in_order[1:]
        start_event = story_in_order[0]
        expected_events = story_in_order[1:]

        # act
        response = client.get(
            "/api/history",
            params=QueryParams(
                storyId=person.id, eventId=start_event.summary_id, direction="next"
            ),
        )

        # assert
        assert response.status_code == 200
        story = Story.model_validate(response.json())
        assert len(story.events) == len(expected_events)
        # expect that the requested event is returned in the middle
        for event, expected_event in zip(story.events, expected_events):
            assert event.date.datetime.date() == expected_event.datetime.date()
            assert event.date.precision == expected_event.precision
            assert event.id == expected_event.summary_id
            if event.id in person_event_ids:
                assert event.storyTitle == f"The Life of {person.name}"
            elif event.id in place_event_ids:
                assert event.storyTitle == f"The History of {place.name}"
            else:
                pytest.fail("unexpected event id")

    def test_with_prev(
        self, client: TestClient, db_session: scoped_session, auth_headers: dict
    ) -> None:
        """When passed the param direction=next, expect the event
        we pass in to be returned in the beginning of the event list."""
        # arrange
        EVENT_COUNT = 20
        person = create_person(client, auth_headers)
        times = [create_time(client, auth_headers) for _ in range(EVENT_COUNT)]
        places = [create_place(client, auth_headers) for _ in range(EVENT_COUNT)]
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
        story_in_order = get_all_events_in_order(
            db_session=db_session, tag_id=person.id
        )
        BASE_INDEX = 15  # index of the story we give as param
        START_INDEX = BASE_INDEX - 10  # beginning of range we expect to get back first
        END_INDEX = BASE_INDEX  # end of range we expect to get back last
        start_event = story_in_order[BASE_INDEX]
        expected_events = story_in_order[START_INDEX:END_INDEX]

        # act
        response = client.get(
            "/api/history",
            params=QueryParams(
                storyId=person.id, eventId=start_event.summary_id, direction="prev"
            ),
        )

        # assert
        assert response.status_code == 200
        story = Story.model_validate(response.json())
        assert len(story.events) == 10
        # expect that the requested event is returned in the middle
        for event, expected_event in zip(story.events, expected_events):
            assert event.date.datetime.date() == expected_event.datetime.date()
            assert event.date.precision == expected_event.precision
            assert event.id == expected_event.summary_id

    def test_prev_person_to_place_story(
        self, client: TestClient, db_session: scoped_session, auth_headers: dict
    ) -> None:
        # arrange
        # setup a person's story
        PERSON_EVENT_COUNT = 4
        PERSON_START_DATE = "-30y"
        person = create_person(client, auth_headers)
        person_story_times = [
            create_time(client, start_date=PERSON_START_DATE, auth_headers=auth_headers)
            for _ in range(PERSON_EVENT_COUNT)
        ]
        person_story_places = [
            create_place(client, auth_headers) for _ in range(PERSON_EVENT_COUNT)
        ]
        time_place_tuples = list(zip(person_story_times, person_story_places))
        [
            create_event(
                person=person,
                place=place,
                time=time,
                client=client,
                auth_headers=auth_headers,
            )
            for time, place in time_place_tuples
        ]
        person_story_in_order = get_all_events_in_order(
            db_session=db_session, tag_id=person.id
        )
        person_event_ids = {
            story_order.summary_id for story_order in person_story_in_order
        }

        # setup a place's story
        PLACE_EVENT_COUNT = 7
        PLACE_END_DATE = "-31y"
        sorted_time_place_tuples = sorted(time_place_tuples, key=lambda t: t[0].date)
        first_time_place = sorted_time_place_tuples[0]
        place = first_time_place[1]
        place_story_people = [
            create_person(client, auth_headers) for _ in range(PLACE_EVENT_COUNT)
        ]
        place_story_times = [
            create_time(client, end_date=PLACE_END_DATE, auth_headers=auth_headers)
            for _ in range(PLACE_EVENT_COUNT)
        ]
        [
            create_event(
                person=person,
                place=place,
                time=time,
                client=client,
                auth_headers=auth_headers,
            )
            for time, person in zip(place_story_times, place_story_people)
        ]
        place_story_in_order = get_all_events_in_order(
            db_session=db_session, tag_id=place.id
        )
        place_event_ids = {
            story_order.summary_id for story_order in place_story_in_order
        }

        # setup the list of events we expect to get back
        # the stories overlap on their last/first event, so we start the person story at 1,
        # and exclude the start event
        story_in_order = place_story_in_order + person_story_in_order[1:]
        start_event = story_in_order[-1]
        expected_events = story_in_order[:-1]

        # act
        response = client.get(
            "/api/history",
            params=QueryParams(
                storyId=person.id, eventId=start_event.summary_id, direction="prev"
            ),
        )

        # assert
        assert response.status_code == 200
        story = Story.model_validate(response.json())
        assert len(story.events) == len(expected_events)
        # expect that the requested event is returned in the middle
        for event, expected_event in zip(story.events, expected_events):
            assert event.date.datetime.date() == expected_event.datetime.date()
            assert event.date.precision == expected_event.precision
            assert event.id == expected_event.summary_id
            if event.id in person_event_ids:
                assert event.storyTitle == f"The Life of {person.name}"
            elif event.id in place_event_ids:
                assert event.storyTitle == f"The History of {place.name}"
            else:
                pytest.fail("unexpected event id")

    @pytest.mark.parametrize("direction", ["prev", "next"])
    def test_empty_result_with_direction(
        self, client: TestClient, direction: Literal["prev", "next"], auth_headers: dict
    ) -> None:
        # arrange
        EVENT_COUNT = 1
        person = create_person(client, auth_headers)
        times = [create_time(client, auth_headers) for _ in range(EVENT_COUNT)]
        places = [create_place(client, auth_headers) for _ in range(EVENT_COUNT)]
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

        # act
        response = client.get(
            "/api/history",
            params=QueryParams(
                storyId=person.id, eventId=events[0].id, direction=direction
            ),
        )

        # assert
        assert response.status_code == 200
        story = Story.model_validate(response.json())
        assert story.events == []

    def test_single_result(self, client: TestClient, auth_headers: dict) -> None:
        # arrange
        EVENT_COUNT = 1
        person = create_person(client, auth_headers)
        times = [create_time(client, auth_headers) for _ in range(EVENT_COUNT)]
        places = [create_place(client, auth_headers) for _ in range(EVENT_COUNT)]
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

        # act
        response = client.get(
            "/api/history",
            params=QueryParams(
                storyId=person.id,
                eventId=events[0].id,
            ),
        )

        # assert
        assert response.status_code == 200
        story = Story.model_validate(response.json())
        assert len(story.events) == 1

    def test_missing_story_raises_404(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        # arrange
        EVENT_COUNT = 1
        person = create_person(client, auth_headers)
        times = [create_time(client, auth_headers) for _ in range(EVENT_COUNT)]
        places = [create_place(client, auth_headers) for _ in range(EVENT_COUNT)]
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

        # act
        response = client.get(
            "/api/history",
            params=QueryParams(
                storyId=uuid4(),  # random ID
                eventId=uuid4(),
            ),
        )

        # assert
        assert response.status_code == 404

    def test_missing_event_raises_404(
        self, client: TestClient, auth_headers: dict
    ) -> None:
        # arrange
        EVENT_COUNT = 1
        person = create_person(client, auth_headers)
        times = [create_time(client, auth_headers) for _ in range(EVENT_COUNT)]
        places = [create_place(client, auth_headers) for _ in range(EVENT_COUNT)]
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

        # act
        response = client.get(
            "/api/history",
            params=QueryParams(
                storyId=events[0].id,
                eventId=uuid4(),
            ),
        )

        # assert
        assert response.status_code == 404


class TestLogin:
    def test_success(
        self, client: TestClient, user_details: dict, seed_accounts
    ) -> None:
        response = client.post(
            "/token",
            data={
                "username": user_details["username"],
                "password": user_details["password"],
            },
        )
        assert response.status_code == 200

    def test_unauthorized(self, client: TestClient, seed_accounts) -> None:
        response = client.post(
            "/token",
            data={
                "username": "Bilbo Baggins",
                "password": "it's precious",
            },
        )
        assert response.status_code == 401


class TestSampleData:
    @pytest.mark.skip(reason="This test uses test infrastructure to seed database.")
    def test_build_sample_data(self, auth_headers: dict) -> None:
        client = TestClient(get_app())
        NUM_PEOPLE = 100
        NUM_PLACES = 300
        MIN_EVENTS = 1
        MAX_EVENTS = 100
        people = [create_person(client, auth_headers) for _ in range(NUM_PEOPLE)]
        places = [create_place(client, auth_headers) for _ in range(NUM_PLACES)]

        num_events = random.randint(MIN_EVENTS, MAX_EVENTS)
        for person in people:
            self.build_person_story(
                person=person,
                num_events=num_events,
                auth_headers=auth_headers,
                client=client,
                places=places,
            )

    def build_person_story(
        self,
        person: WikiDataPersonOutput,
        num_events: int,
        auth_headers: dict,
        client: TestClient,
        places: list[WikiDataPlaceOutput],
    ):
        for _ in range(num_events):
            time = create_time(client, auth_headers)
            create_event(
                person=person,
                place=random.choice(places),
                time=time,
                client=client,
                auth_headers=auth_headers,
            )
