from the_history_atlas.apps.app_manager import AppManager


def get_context(request, _apps: AppManager):

    return {"request": request, "test": "TEST", "apps": _apps}
