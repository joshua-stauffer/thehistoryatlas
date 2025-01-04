from the_history_atlas.apps.accounts.accounts import Accounts
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.database import DatabaseApp
from the_history_atlas.apps.readmodel import ReadModelApp


class AppManager:
    config_app: Config
    database_app: DatabaseApp
    accounts_app: Accounts
    readmodel_app: ReadModelApp

    def __init__(self, config_app: Config):
        self.config_app = config_app
        self.database_app = DatabaseApp(config_app=self.config_app)
        self.accounts_app = Accounts(
            config=self.config_app, database_client=self.database_app.client()
        )

        self.readmodel_app = ReadModelApp(
            config_app=self.config_app,
            database_client=self.database_app.client(),
        )
