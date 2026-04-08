from unittest.mock import MagicMock

import pytest
from the_history_atlas.apps.accounts.repository import Repository


@pytest.fixture
def mock_db():
    return MagicMock(spec=Repository)
