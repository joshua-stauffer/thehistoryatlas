import logging
from datetime import datetime, timezone


from the_history_atlas.apps.accounts.errors import known_exceptions

log = logging.getLogger(__name__)


def update_last_login() -> str:
    """returns a string of the current time"""
    return str(datetime.now(timezone.utc))


def error_handler(func):
    """Decorator to transform known exceptions into meaningful messages"""

    def wrapper(*args, **kwargs):

        try:
            return func(*args, **kwargs)
        except known_exceptions as e:
            log.debug(f"Caught routine exception {e}")
            return {"type": "ERROR", "payload": {"error": str(e)}}
        except Exception as e:
            log.error(f"Unknown exception occurred: {e}")
            return {"type": "ERROR", "payload": {"error": "SERVER_ERROR", "code": 500}}

    return wrapper
