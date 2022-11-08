import os
from typing import Union


class MissingEnvVariable(Exception):
    ...


ENV_TYPE = Union[str, bool]


def get_from_env(variable: str, default: ENV_TYPE = None) -> ENV_TYPE:
    """
    Util to import a value from the environment, and raises MissingEnvVariable
    in case the value is not available.
    """
    value = os.environ.get(variable, None)
    if value is None and default is None:
        raise MissingEnvVariable
    elif value is None:
        return default
    elif value == "True":
        return True
    elif value == "False":
        return False
    else:
        return value
