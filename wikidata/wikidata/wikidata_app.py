from typing import Dict, Optional, Any

from .repository import Repository


class WikiDataApp:
    def __init__(self, repository: Repository):
        """
        Initialize the WikiDataApp with a Repository instance.

        Args:
            repository: An instance of the Repository class to use for data retrieval.
        """
        self.repository = repository

    def get_entity(self, id: str) -> dict:
        """
        Retrieve an entity from the repository by its ID.

        Args:
            id: The ID of the entity to retrieve.

        Returns:
            The entity data as a dictionary.

        Raises:
            KeyError: If the entity with the given ID doesn't exist.
        """
        return self.repository.get(id)

    def get_label(self, id: str, lang: str) -> str:
        """
        Get the label for an entity in the specified language.

        Args:
            id: The ID of the entity.
            lang: The language code for the label.

        Returns:
            The label text.

        Raises:
            KeyError: If the entity with the given ID doesn't exist.
            ValueError: If the label in the specified language doesn't exist.
        """
        entity = self.get_entity(id)
        label = entity.get("labels", {}).get(lang, {}).get("value")

        if label is None:
            raise ValueError(f"No label found for entity {id} in language {lang}")

        return label

    def get_description(self, id: str, lang: str) -> str:
        """
        Get the description for an entity in the specified language.

        Args:
            id: The ID of the entity.
            lang: The language code for the description.

        Returns:
            The description text.

        Raises:
            KeyError: If the entity with the given ID doesn't exist.
            ValueError: If the description in the specified language doesn't exist.
        """
        entity = self.get_entity(id)
        description = entity.get("descriptions", {}).get(lang, {}).get("value")

        if description is None:
            raise ValueError(f"No description found for entity {id} in language {lang}")

        return description
