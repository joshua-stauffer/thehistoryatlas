from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.accounts.get_user import (
    GetUserResponsePayload,
    GetUserPayload,
)


def resolve_get_user(_, info: Info, token: str) -> GetUserResponsePayload:
    app = info.context.apps.accounts_app
    get_user_input = GetUserPayload(token=token)
    deactivate_account_output = app.get_user(data=get_user_input)
    return deactivate_account_output
