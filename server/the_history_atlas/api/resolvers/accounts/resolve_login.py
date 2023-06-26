from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.accounts import LoginResponse


def resolve_login(_, info: Info, username, password) -> LoginResponse:
    app = info.context["apps"].accounts_app
    result = app.login(username=username, password=password)
    return result
