from datetime import datetime


def get_version() -> str:
    """Get the current app version."""
    return "0.0.1"


def get_current_time() -> str:
    """Get the current time."""
    return str(datetime.utcnow())
