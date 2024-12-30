from datetime import datetime


def get_timestamp() -> str:
    """Get the current time."""
    return str(datetime.utcnow())


def get_app_version() -> str:
    return "0.0.1"
