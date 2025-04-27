import json
from typing import Dict, Optional, Any
from rocksdict import Rdict, Options
from pydantic_settings import BaseSettings
from rocksdict.rocksdict import AccessType


class Config(BaseSettings):
    DB_PATH: str = "./data/rocks_db"


class Repository:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._db = None
        self._open_db()

    def _open_db(self):
        if self._db is None:
            self._db = Rdict(self.config.DB_PATH, access_type=AccessType.read_only())

    def close(self):
        """Close the database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None

    def __del__(self):
        self.close()

    def get(self, id: str) -> dict:
        """
        Retrieve a document by its ID from the repository.

        Args:
            id: The ID of the document to retrieve

        Returns:
            dict: The document data

        Raises:
            KeyError: If the document with the given ID doesn't exist
        """
        try:
            self._open_db()
            value = self._db.get(id.encode("utf-8"))
            if value is None:
                raise KeyError(f"No document found with id: {id}")
            return json.loads(value.decode("utf-8"))
        except Exception as e:
            if isinstance(e, KeyError):
                raise
            raise KeyError(f"Failed to retrieve document with id {id}: {str(e)}")

    def put(self, id: str, data: dict) -> None:
        """
        Store a document in the repository with the given ID.

        Args:
            id: The ID of the document to store
            data: The document data to store

        Raises:
            ValueError: If the data is not a dictionary
            RuntimeError: If there was an error storing the data
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        try:
            self._open_db()
            self._db.put(id.encode("utf-8"), json.dumps(data).encode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Failed to store document with id {id}: {str(e)}")
