from logging import getLogger

logger = getLogger(__name__)


class UnknownMessageError(Exception):
    def __init__(self, msg: dict):
        logger.error(f"Cannot resolve message: {msg}")
