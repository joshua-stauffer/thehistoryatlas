from unittest.mock import Mock

import pytest

from the_history_atlas.api.context import get_context
from the_history_atlas.api.schema import build_schema
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.eventstore import EventStore


@pytest.fixture
def apps(config):
    apps = AppManager(config_app=config)
    # remove eventstore, so apps are tested individually
    apps.events_app = Mock(spec=EventStore)
    return apps


@pytest.fixture
def schema(apps):
    """GraphQL schema with resolvers."""
    schema = build_schema()
    return schema


@pytest.fixture
def context_value(apps):
    context_value = get_context(request={}, _apps=apps)
    return context_value
