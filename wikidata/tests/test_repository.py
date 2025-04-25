import shutil
import tempfile
import pytest
from typing import Dict, Generator, Any

from rocksdict import Rdict
from wikidata.repository import Repository, Config


@pytest.fixture
def rocks_db_path() -> Generator[str, None, None]:
    """
    Fixture that creates a temporary directory for RocksDB and cleans it up after the test.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after the test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_config(rocks_db_path: str) -> Config:
    """
    Fixture that returns a Config object with a test DB path.
    """
    return Config(db_path=rocks_db_path)


@pytest.fixture
def test_data() -> Dict[str, Dict[str, Any]]:
    """
    Fixture that returns test data.
    """
    return {
        "item1": {"id": "item1", "name": "Test Item 1", "value": 42},
        "item2": {"id": "item2", "name": "Test Item 2", "value": 99},
    }


@pytest.fixture
def populate_db(test_config: Config, test_data: Dict[str, Dict[str, Any]]) -> None:
    """
    Fixture that creates and populates a RocksDB instance with test data.
    """
    # Populate the database with test data
    db = Rdict(test_config.db_path)

    try:
        for key, value in test_data.items():
            db.put(key, value)
    finally:
        # Close the database connection before yielding control
        db.close()


class TestRepository:
    def test_get_existing_item(
        self,
        test_config: Config,
        populate_db: None,
        test_data: Dict[str, Dict[str, Any]],
    ) -> None:
        """
        Test that the get method returns the correct item when it exists.
        """
        # Arrange
        repository = Repository(config=test_config)

        # Act
        result = repository.get("item1")

        # Assert
        assert result == test_data["item1"]

    def test_get_nonexistent_item(self, test_config: Config, populate_db: None) -> None:
        """
        Test that the get method raises a KeyError when the item doesn't exist.
        """
        # Arrange
        repository = Repository(config=test_config)

        # Act & Assert
        with pytest.raises(KeyError):
            repository.get("nonexistent_item")

    def test_put_new_item(self, test_config: Config) -> None:
        """
        Test that the put method stores a new item correctly.
        """
        # Arrange
        repository = Repository(config=test_config)
        new_item = {"id": "new_item", "name": "New Item", "value": 123}

        # Act
        repository.put("new_item", new_item)

        # Assert
        result = repository.get("new_item")
        assert result == new_item

    def test_put_update_existing_item(
        self, test_config: Config, populate_db: None
    ) -> None:
        """
        Test that the put method updates an existing item correctly.
        """
        # Arrange
        repository = Repository(config=test_config)
        updated_item = {"id": "item1", "name": "Updated Item 1", "value": 100}

        # Act
        repository.put("item1", updated_item)

        # Assert
        result = repository.get("item1")
        assert result == updated_item

    def test_put_invalid_data(self, test_config: Config) -> None:
        """
        Test that the put method raises a ValueError when given non-dict data.
        """
        # Arrange
        repository = Repository(config=test_config)

        # Act & Assert
        with pytest.raises(ValueError):
            repository.put("invalid", "not a dict")
