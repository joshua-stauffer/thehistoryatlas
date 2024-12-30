from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from the_history_atlas.apps.config import Config


DatabaseClient = Engine


class DatabaseApp:
    def __init__(self, config_app: Config):
        self.config_app = config_app
        self._client: DatabaseClient | None = None

    def _get_client(self) -> DatabaseClient:
        return create_engine(
            self.config_app.DB_URI, echo=self.config_app.DEBUG, future=True
        )

    def client(self) -> DatabaseClient:
        if self._client is None:
            self._client = self._get_client()
        return self._client
