from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.accounts import Credentials
from the_history_atlas.apps.domain.models.accounts.update_user import (
    UpdateUserResponsePayload,
    UpdateUserPayload,
)


def resolve_update_user(
    _, info: Info, token: str, user_details: dict, credentials: dict | None = None
) -> UpdateUserResponsePayload:
    app = info.context.apps.accounts_app
    if credentials is not None:
        credentials = Credentials(**credentials)
    input = UpdateUserPayload(
        token=token, user_details=user_details, credentials=credentials
    )
    output = app.update_user(data=input)
    return output
