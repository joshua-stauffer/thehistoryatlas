from the_history_atlas.api.context import Info
from the_history_atlas.apps.accounts.accounts import Accounts
from the_history_atlas.apps.domain.models.accounts.is_username_unique import (
    IsUsernameUniqueResponsePayload,
    IsUsernameUniquePayload,
)


def resolve_is_username_unique(
    _, info: Info, username: str
) -> IsUsernameUniqueResponsePayload:
    app = info.context.apps.accounts_app
    input = IsUsernameUniquePayload(username=username)
    output = app.is_username_unique(data=input)
    return output
