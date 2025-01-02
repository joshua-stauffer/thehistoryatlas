from typing import Literal
from uuid import UUID

from sqlalchemy import text

from the_history_atlas.apps.config import Config
from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.domain.models.core import Story


class CoreApp:
    # rename me
    def __init__(self, config_app: Config, database_client: DatabaseClient):
        self.config = config_app
        self.db_client = database_client
