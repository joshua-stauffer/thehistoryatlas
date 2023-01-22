import os

import pytest

from wiki_service.config import WikiServiceConfig


@pytest.fixture
def config():
    test_db_uri = os.environ.get("TEST_DB_URI", None)
    if test_db_uri is None:
        raise Exception("Env var TEST_DB_URI is required to run database tests.")
    config = WikiServiceConfig()
    config.DB_URI = test_db_uri
    return config
