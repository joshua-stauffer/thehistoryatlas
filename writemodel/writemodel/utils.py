from datetime import datetime


def get_timestamp() -> str:
    """Get the current time."""
    return str(datetime.utcnow())
