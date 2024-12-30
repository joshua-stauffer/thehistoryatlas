from unittest.mock import MagicMock

import pytest
from the_history_atlas.apps.accounts.database import Database


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)
