from the_history_atlas.apps.domain.models.accounts.get_user import (
    GetUserResponsePayload,
)


def resolve_get_user(_, info, token: str) -> GetUserResponsePayload:
    ...
