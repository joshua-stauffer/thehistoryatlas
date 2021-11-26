from datetime import datetime
from app.errors import known_exceptions


def update_last_login() -> str:
    """returns a string of the current time"""
    return str(datetime.utcnow())


def error_handler(func):
    """Decorator to transform known exceptions into meaningful messages"""

    def wrapper(*args, **kwargs):

        try:
            return func(*args, **kwargs)
        except known_exceptions as e:
            return {"type": "ERROR", "payload": {"error": str(e)}}

    return wrapper
