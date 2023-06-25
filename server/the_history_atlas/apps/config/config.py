import os


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

        # are we testing?
        if self.test_for_truthiness(os.environ.get("TESTING")):
            self.TESTING = True
            # override the DB_URI:
            self.DB_URI = self._TESTING_DB_URI
        else:
            self.TESTING = False

        # get correct values for broker
        self.NETWORK_HOST_NAME = os.environ.get("HOST_NAME", "localhost")
        self.BROKER_USERNAME = os.environ.get("BROKER_USERNAME", "guest")
        self.BROKER_PASS = os.environ.get("BROKER_PASS", "guest")
        self.QUEUE_NAME = os.environ.get("QUEUE_NAME", "")
        self.EXCHANGE_NAME = os.environ.get("EXCHANGE_NAME", "")

        # set values for GQL server
        self.SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
        self.SERVER_PORT = os.environ.get("SERVER_PORT", 8888)

    @staticmethod
    def test_for_truthiness(val):
        """checks val for truthy values
        param val: string | None"""
        if not val:
            return False
        return "true" in val or "True" in val or "t" in val or "1" in val or "T" in val
