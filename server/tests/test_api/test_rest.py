from datetime import datetime, timezone
import random
from uuid import uuid4, UUID
from faker import Faker

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

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


def create_place(client: TestClient) -> WikiDataPlaceOutput:
    place = _generate_fake_place()
    response = client.post("/wikidata/places", data=place.model_dump_json())
    return WikiDataPlaceOutput.model_validate(response.json())


def _generate_fake_person() -> WikiDataPersonOutput:
    """Generate a fake WikiData person entry."""
    wikidata_id = generate_wikidata_id()
    return WikiDataPersonInput(
        wikidata_id=wikidata_id,
        wikidata_url=generate_wikidata_url(wikidata_id),
        name=fake.name(),
    )


def create_person(client: TestClient) -> WikiDataPersonOutput:
    person = _generate_fake_person()
    person_output = client.post("/wikidata/people", data=person.model_dump_json())
    return WikiDataPersonOutput.model_validate(person_output.json())


def _generate_fake_time() -> WikiDataTimeInput:
    """Generate a fake WikiData time entry."""
    wikidata_id = generate_wikidata_id()
    date = fake.date_time_between(start_date="-50y", end_date="now")

    # Format the date string similar to the example
    date_str = date.strftime("%d %B %Y")

    return WikiDataTimeInput(
        wikidata_id=wikidata_id,
        wikidata_url=generate_wikidata_url(wikidata_id),
        name=date_str,
        date=date,
        calendar_model="https://www.wikidata.org/wiki/Q12138",  # Gregorian calendar
        precision=random.randint(7, 11),  # Day precision, following the example
    )


def create_time(client: TestClient) -> WikiDataTimeOutput:
    time = _generate_fake_time()
    time_output = client.post("/wikidata/times", data=time.model_dump_json())
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
) -> WikiDataEventOutput:
    event = _generate_fake_event(person, place, time)
    event_output = client.post("/wikidata/events", data=event.model_dump_json())
    return WikiDataEventOutput.model_validate(event_output.json())


@pytest.fixture
def client(cleanup_db):
    return TestClient(get_app())


def test_get_history(client: TestClient) -> None:
    response = client.get("/history")
    assert response.status_code == 200


def test_create_person(client: TestClient) -> None:
    input = WikiDataPersonInput(
        wikidata_id="Q1339",
        wikidata_url="https://www.wikidata.org/wiki/Q1339",
        name="Johann Sebastian Bach",
    )

    response = client.post("/wikidata/people", data=input.model_dump_json())
    assert response.status_code == 200, response.text


def test_create_place(client: TestClient) -> None:
    input = WikiDataPlaceInput(
        wikidata_id="Q7070",
        wikidata_url="https://www.wikidata.org/wiki/Q7070",
        name="Eisenach",
        latitude=50.974722,
        longitude=10.324444,
    )

    response = client.post("/wikidata/places", data=input.model_dump_json())
    assert response.status_code == 200, response.text


def test_create_time(client: TestClient) -> None:
    input = WikiDataTimeInput(
        wikidata_id="Q69125241",
        wikidata_url="https://www.wikidata.org/wiki/Q69125241",
        name="31 March 1685",
        date=datetime(year=1685, month=3, day=31),
        calendar_model="https://www.wikidata.org/wiki/Q12138",
        precision=11,
    )

    response = client.post("/wikidata/times", data=input.model_dump_json())
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
    client: TestClient, wikidata_ids: list[WikiDataTagPointer]
) -> None:
    response = client.get(
        "/wikidata/tags",
        params={"wikidata_ids": [pointer.wikidata_id for pointer in wikidata_ids]},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "wikidata_ids": [o.model_dump(mode="json") for o in wikidata_ids]
    }


def test_get_tags_by_wikidata_ids_missing_tags(
    client: TestClient, wikidata_ids: list[WikiDataTagPointer]
) -> None:
    extra_id = "Q8943682"
    existing_ids = [pointer.wikidata_id for pointer in wikidata_ids]
    params = {"wikidata_ids": [*existing_ids, extra_id]}
    existing_pointers = [o.model_dump(mode="json") for o in wikidata_ids]
    expected_response = [
        *existing_pointers,
        {"wikidata_id": extra_id, "id": None},
    ]
    response = client.get("/wikidata/tags", params=params)
    assert response.status_code == 200, response.text
    assert response.json() == {"wikidata_ids": expected_response}


def test_create_event(
    client: TestClient,
):
    person_input = WikiDataPersonInput(
        wikidata_id="Q1339",
        wikidata_url="https://www.wikidata.org/wiki/Q1339",
        name="Johann Sebastian Bach",
    )

    created_person_output = client.post(
        "/wikidata/people", data=person_input.model_dump_json()
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
        "/wikidata/places", data=place_input.model_dump_json()
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
        "/wikidata/times", data=time_input.model_dump_json()
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
    response = client.post("/wikidata/events", data=event_input.model_dump_json())
    assert response.status_code == 200, response.text


def setup_events(
    client: TestClient,
    people: list[WikiDataPersonInput],
    places: list[WikiDataPlaceInput],
    times: list[WikiDataTimeInput],
    events: list[WikiDataEventInput],
):

    for time in times:
        client.post("/wikidata/times", data=time.model_dump_json())
    for event in events:
        client.post("/wikidata/events", data=event.model_dump_json())


def test_event_stories(client: TestClient):
    person = create_person(client)
    times = [create_time(client) for _ in range(10)]
    places = [create_place(client) for _ in range(10)]

    events = [
        create_event(person=person, place=place, time=time, client=client)
        for time, place in zip(times, places)
    ]
    print()
