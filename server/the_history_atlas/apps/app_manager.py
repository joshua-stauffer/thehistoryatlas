from the_history_atlas.apps.accounts.accounts import Accounts
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.database import DatabaseApp
from the_history_atlas.apps.eventstore import EventStore
from the_history_atlas.apps.writemodel import WriteModelApp


class AppManager:
    config_app: Config
    database_app: DatabaseApp
    events_app: EventStore
    accounts_app: Accounts
    writemodel_app: WriteModelApp

    def __init__(self, config_app: Config):
        self.config_app = config_app
        self.database_app = DatabaseApp(config_app=self.config_app)
        self.events_app = EventStore(
            config=self.config_app, database_client=self.database_app.client()
        )
        self.accounts_app = Accounts(
            config=self.config_app, database_client=self.database_app.client()
        )
        self.writemodel_app = WriteModelApp(
            config=self.config_app,
            database_client=self.database_app.client(),
            events_app=self.events_app,
            accounts_app=self.accounts_app,
        )
