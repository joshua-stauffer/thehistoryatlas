from graphql import GraphQLResolveInfo

from the_history_atlas.apps.app_manager import AppManager


class Context:
    """Custom fields provided to resolvers."""

    apps: AppManager


class Info(GraphQLResolveInfo):
    """Extend GraphQLResolveInfo with our custom Context."""

    context: Context


def get_context(request, _apps: AppManager):
    return {"request": request, "apps": _apps}
