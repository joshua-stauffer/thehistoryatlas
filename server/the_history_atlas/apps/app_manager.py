from sqlalchemy import create_engine

from the_history_atlas.apps.accounts.accounts import Accounts
from the_history_atlas.apps.config import Config


class AppManager:
    config: Config
    accounts_app: Accounts

    def __init__(self):

        self.config = Config()
        database_client = self._build_database_client()
        self.accounts_app = Accounts(
            config=self.config, database_client=database_client
        )

    def _build_database_client(self):
        return create_engine(self.config.DB_URI, echo=self.config.DEBUG, future=True)
