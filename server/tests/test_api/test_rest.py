import pytest
from fastapi.testclient import TestClient

from the_history_atlas.api.types.tags import WikiDataPersonInput
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
