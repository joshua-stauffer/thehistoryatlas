from unittest.mock import Mock

import pytest

from the_history_atlas.apps.accounts.accounts import Accounts
from the_history_atlas.apps.app_manager import AppManager


@pytest.fixture
def mock_apps(accounts_app):
    app_manager = Mock(spec=AppManager)
    app_manager.accounts_app = accounts_app
    return app_manager


@pytest.fixture
def accounts_app():
    accounts_app = Mock(spec=Accounts)
    return accounts_app
