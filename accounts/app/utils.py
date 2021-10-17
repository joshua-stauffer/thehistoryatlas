from datetime import datetime

def update_last_login() -> str:
    """returns a string of the current time"""
    return str(datetime.utcnow())
