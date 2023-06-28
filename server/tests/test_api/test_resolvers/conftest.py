from unittest.mock import Mock

import pytest

from the_history_atlas.api.context import Info
from the_history_atlas.apps.accounts.accounts import Accounts
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.writemodel import WriteModelApp


@pytest.fixture
def mock_apps(accounts_app, writemodel_app):
    app_manager = Mock(spec=AppManager)
    app_manager.accounts_app = accounts_app
    app_manager.writemodel_app = writemodel_app
    return app_manager


@pytest.fixture
def accounts_app():
    accounts_app = Mock(spec=Accounts)
    return accounts_app


@pytest.fixture
def writemodel_app():
    writemodel_app = Mock(spec=WriteModelApp)
    return writemodel_app


@pytest.fixture
def info(mock_apps):
    info = Mock(spec=Info)
    info.context.apps = mock_apps
    return info
