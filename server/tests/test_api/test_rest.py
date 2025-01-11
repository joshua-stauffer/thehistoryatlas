import pytest
from fastapi.testclient import TestClient

from the_history_atlas.main import get_app


@pytest.fixture
def client():
    return TestClient(get_app())


def test_get_history(client: TestClient) -> None:
    response = client.get("/history")
    assert response.status_code == 200
