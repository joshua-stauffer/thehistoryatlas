from typing import Any

from graphql import GraphQLResolveInfo

from the_history_atlas.apps.app_manager import AppManager


class Context:
    """Custom fields provided to resolvers."""

    request: Any
    apps: AppManager

    def __init__(self, request: Any, apps: AppManager):
        self.request = request
        self.apps = apps


class Info(GraphQLResolveInfo):
    """Extend GraphQLResolveInfo with our custom Context."""

    context: Context


def get_context(request, _apps: AppManager) -> Context:
    return Context(request=request, apps=_apps)
