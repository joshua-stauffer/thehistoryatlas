from the_history_atlas.apps.accounts.accounts import Accounts
from the_history_atlas.apps.config import Config


class AppManager:
    config: Config
    accounts_app: Accounts

    def __init__(self):
        self.config = Config()
        self.accounts_app = Accounts(config=self.config)
