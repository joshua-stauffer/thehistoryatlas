from datetime import datetime
from uuid import uuid4

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
)
from the_history_atlas.main import get_app


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
