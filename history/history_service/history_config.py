from tha_config import Config

import os


class HistoryConfig(Config):
    """An extended utility class to organize configuration variables

    the History component requires a fixed database URI even when in testing mode,
    so we provide it with the dev database."""

    def __init__(self) -> None:
        super().__init__()
        self._TESTING_DB_URI = os.environ.get("TEST_DB_URI")
        if self.TESTING:
            self.DB_URI = self._TESTING_DB_URI
