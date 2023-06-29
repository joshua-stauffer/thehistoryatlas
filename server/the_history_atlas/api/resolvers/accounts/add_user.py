from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.accounts.add_user import (
    AddUserPayload,
    AddUserResponsePayload,
)


def resolve_add_user(
    _, info: Info, token: str, user_details: dict
) -> AddUserResponsePayload:
    app = info.context.apps.accounts_app
    add_user_input = AddUserPayload(token=token, user_details=user_details)
    add_user_output = app.add_user(add_user_input)
    return add_user_output
