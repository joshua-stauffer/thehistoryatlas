import os
from typing import Optional


class MissingEnvVariable(Exception):
    ...


def get_from_env(variable: str, default: Optional[str] = None) -> str:
    """
    Util to import a value from the environment, and raises MissingEnvVariable
    in case the value is not available.
    """
    value = os.environ.get(variable, None)
    if value is None and default is None:
        raise MissingEnvVariable
    elif value is None:
        return default
    else:
        return value
