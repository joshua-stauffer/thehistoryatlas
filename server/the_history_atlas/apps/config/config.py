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
        self.DEBUG = bool(os.environ.get("DEBUG"))
        self.DB_URI = os.environ.get("THA_DB_URI")
        self.COMPUTE_STORY_ORDER = bool(os.environ.get("COMPUTE_STORY_ORDER", True))

    @staticmethod
    def get_timestamp() -> str:
        """Get the current time."""
        # todo: ensure tz
        return str(datetime.utcnow())

    @staticmethod
    def get_app_version() -> str:
        return VERSION
