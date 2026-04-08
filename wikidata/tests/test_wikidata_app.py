import json
import pytest
from unittest.mock import Mock, patch
from wikidata.wikidata_app import WikiDataApp
from wikidata.repository import Repository


@pytest.fixture
def mock_repository():
    """Fixture that returns a mock Repository."""
    return Mock(spec=Repository)


@pytest.fixture
def sample_entity():
    """Fixture that returns a sample entity with labels and descriptions."""
    return {
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


class TestWikiDataApp:
    def test_get_entity_success(self, mock_repository, sample_entity):
        """Test successful entity retrieval."""
        # Arrange
        mock_repository.get.return_value = sample_entity
        app = WikiDataApp(mock_repository)

        # Act
        result = app.get_entity("Q1339")

        # Assert
        assert result == sample_entity
        mock_repository.get.assert_called_once_with("Q1339")

    def test_get_entity_not_found(self, mock_repository):
        """Test entity retrieval when the entity doesn't exist."""
        # Arrange
        mock_repository.get.side_effect = KeyError("No document found with id: Q999999")
        app = WikiDataApp(mock_repository)

        # Act & Assert
        with pytest.raises(KeyError):
            app.get_entity("Q999999")
        mock_repository.get.assert_called_once_with("Q999999")

    def test_get_label_success(self, mock_repository, sample_entity):
        """Test successful label retrieval."""
        # Arrange
        mock_repository.get.return_value = sample_entity
        app = WikiDataApp(mock_repository)

        # Act
        result = app.get_label("Q1339", "en")

        # Assert
        assert result == "Johann Sebastian Bach"
        mock_repository.get.assert_called_once_with("Q1339")

    def test_get_label_entity_not_found(self, mock_repository):
        """Test label retrieval when the entity doesn't exist."""
        # Arrange
        mock_repository.get.side_effect = KeyError("No document found with id: Q999999")
        app = WikiDataApp(mock_repository)

        # Act & Assert
        with pytest.raises(KeyError):
            app.get_label("Q999999", "en")
        mock_repository.get.assert_called_once_with("Q999999")

    def test_get_label_language_not_found(self, mock_repository, sample_entity):
        """Test label retrieval when the language doesn't exist."""
        # Arrange
        mock_repository.get.return_value = sample_entity
        app = WikiDataApp(mock_repository)

        # Act & Assert
        with pytest.raises(
            ValueError, match="No label found for entity Q1339 in language es"
        ):
            app.get_label("Q1339", "es")
        mock_repository.get.assert_called_once_with("Q1339")

    def test_get_description_success(self, mock_repository, sample_entity):
        """Test successful description retrieval."""
        # Arrange
        mock_repository.get.return_value = sample_entity
        app = WikiDataApp(mock_repository)

        # Act
        result = app.get_description("Q1339", "en")

        # Assert
        assert result == "German composer (1685–1750)"
        mock_repository.get.assert_called_once_with("Q1339")

    def test_get_description_entity_not_found(self, mock_repository):
        """Test description retrieval when the entity doesn't exist."""
        # Arrange
        mock_repository.get.side_effect = KeyError("No document found with id: Q999999")
        app = WikiDataApp(mock_repository)

        # Act & Assert
        with pytest.raises(KeyError):
            app.get_description("Q999999", "en")
        mock_repository.get.assert_called_once_with("Q999999")

    def test_get_description_language_not_found(self, mock_repository, sample_entity):
        """Test description retrieval when the language doesn't exist."""
        # Arrange
        mock_repository.get.return_value = sample_entity
        app = WikiDataApp(mock_repository)

        # Act & Assert
        with pytest.raises(
            ValueError, match="No description found for entity Q1339 in language es"
        ):
            app.get_description("Q1339", "es")
        mock_repository.get.assert_called_once_with("Q1339")
