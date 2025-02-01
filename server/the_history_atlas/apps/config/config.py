import os
from datetime import datetime
from typing import Final

VERSION: Final = "0.1.0"


class Config:
    """This class makes configuration variables present in the environment available
    through the property syntax. Useful public values obtained include:
        TESTING
        CONFIG
        DB_URI
        NETWORK_HOST_NAME
        BROKER_USERNAME
        BROKER_PASS
        QUEUE_NAME
    """

    def __init__(self):

        # debug mode?
        self.DEBUG = self.test_for_truthiness(os.environ.get("DEBUG"))

        # database uris
        self._PROD_DB_URI = os.environ.get("PROD_DB_URI")
        self._DEV_DB_URI = os.environ.get("DEV_DB_URI")
        self._TESTING_DB_URI = "sqlite+pysqlite:///:memory:"

        # are we in production?
        prod = os.environ.get("CONFIG")
        if prod == "PRODUCTION":
            self.CONFIG = "PRODUCTION"
            self.DB_URI = self._PROD_DB_URI
        else:
            self.CONFIG = "DEVELOPMENT"
            self.DB_URI = self._DEV_DB_URI

        if self.test_for_truthiness(os.environ.get("TESTING")):
            self.TESTING = False
            # override the DB_URI:
            self.DB_URI = self._TESTING_DB_URI
        else:
            self.TESTING = False

    @staticmethod
    def test_for_truthiness(val):
        """checks val for truthy values
        param val: string | None"""
        if not val:
            return False
        return "true" in val or "True" in val or "t" in val or "1" in val or "T" in val

    @staticmethod
    def get_timestamp() -> str:
        """Get the current time."""
        # todo: ensure tz
        return str(datetime.utcnow())

    @staticmethod
    def get_app_version() -> str:
        return VERSION
