from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from the_history_atlas.api.types.tags import (
    WikiDataPersonInput,
    WikiDataPlaceInput,
    WikiDataTimeInput,
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
