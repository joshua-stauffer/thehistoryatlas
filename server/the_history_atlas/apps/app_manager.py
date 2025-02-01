from the_history_atlas.apps.accounts.accounts_app import AccountsApp
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.database import DatabaseApp
from the_history_atlas.apps.history import HistoryApp


class AppManager:
    config_app: Config
    database_app: DatabaseApp
    accounts_app: AccountsApp
    history_app: HistoryApp

    def __init__(self, config_app: Config):
        self.config_app = config_app
        self.database_app = DatabaseApp(config_app=self.config_app)
        self.accounts_app = AccountsApp(
            config=self.config_app, database_client=self.database_app.client()
        )
        self.history_app = HistoryApp(
            config_app=self.config_app,
            database_client=self.database_app.client(),
        )
