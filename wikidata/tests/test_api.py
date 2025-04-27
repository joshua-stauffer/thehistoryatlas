import json
import shutil
import tempfile
import pytest
from typing import Dict, Any, Generator
from fastapi.testclient import TestClient
from rocksdict import Rdict

from wikidata.repository import Repository, Config
from wikidata.main import app, get_config


# Test entity data
TEST_ENTITY = {
    "id": "Q1339",
    "labels": {
        "en": {"language": "en", "value": "Johann Sebastian Bach"},
        "fr": {"language": "fr", "value": "Jean-Sébastien Bach"},
        "de": {"language": "de", "value": "Johann Sebastian Bach"},
    },
    "descriptions": {
        "en": {"language": "en", "value": "German composer (1685–1750)"},
        "fr": {
            "language": "fr",
            "value": "claveciniste, organiste et compositeur allemand",
        },
        "de": {"language": "de", "value": "deutscher Komponist des Barock"},
    },
}


@pytest.fixture(scope="function")
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary directory for RocksDB data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def test_config(temp_db_path: str) -> Config:
    """Create a Config object with the test DB path."""
    return Config(DB_PATH=temp_db_path)


@pytest.fixture(scope="function")
def populate_db(test_config: Config) -> None:
    """Populate the test database with test data."""
    # Create and open the DB
    db = Rdict(test_config.DB_PATH)

    # Add test data
    try:
        db.put("Q1339".encode(), json.dumps(TEST_ENTITY).encode())
    finally:
        # Ensure the DB is properly closed
        db.close()


@pytest.fixture(scope="function")
def client(test_config: Config, populate_db: None) -> TestClient:
    """Create a test client with the test database."""
    # Override the config dependency
    app.dependency_overrides[get_config] = lambda: test_config

    # Create and return test client
    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides.clear()


class TestWikiDataAPI:
    def test_get_entity_success(self, client):
        """Test successful entity retrieval."""
        response = client.get("/v1/entities/items/Q1339")
        assert response.status_code == 200
        assert response.json() == TEST_ENTITY

    def test_get_entity_not_found(self, client):
        """Test entity retrieval when entity does not exist."""
        response = client.get("/v1/entities/items/Q999999")
        assert response.status_code == 404
        assert "No document found with id" in response.json()["detail"]

    def test_get_label_success(self, client):
        """Test successful label retrieval."""
        response = client.get("/v1/entities/items/Q1339/labels/en")
        assert response.status_code == 200
        assert response.json() == {"language": "en", "value": "Johann Sebastian Bach"}

    def test_get_label_entity_not_found(self, client):
        """Test label retrieval when entity does not exist."""
        response = client.get("/v1/entities/items/Q999999/labels/en")
        assert response.status_code == 404
        assert "No document found with id" in response.json()["detail"]

    def test_get_label_language_not_found(self, client):
        """Test label retrieval when language does not exist."""
        response = client.get("/v1/entities/items/Q1339/labels/es")
        assert response.status_code == 404
        assert "No label found for entity" in response.json()["detail"]

    def test_get_description_success(self, client):
        """Test successful description retrieval."""
        response = client.get("/v1/entities/items/Q1339/descriptions/en")
        assert response.status_code == 200
        assert response.json() == {
            "language": "en",
            "value": "German composer (1685–1750)",
        }

    def test_get_description_entity_not_found(self, client):
        """Test description retrieval when entity does not exist."""
        response = client.get("/v1/entities/items/Q999999/descriptions/en")
        assert response.status_code == 404
        assert "No document found with id" in response.json()["detail"]

    def test_get_description_language_not_found(self, client):
        """Test description retrieval when language does not exist."""
        response = client.get("/v1/entities/items/Q1339/descriptions/es")
        assert response.status_code == 404
        assert "No description found for entity" in response.json()["detail"]
