from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.accounts import LoginResponse, Credentials


def resolve_login(_, info: Info, username: str, password: str) -> LoginResponse:
    app = info.context.apps.accounts_app
    input = Credentials(username=username, password=password)
    output = app.login(input)
    return output
