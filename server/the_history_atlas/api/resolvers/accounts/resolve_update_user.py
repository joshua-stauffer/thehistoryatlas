from the_history_atlas.apps.domain.models.accounts.update_user import (
    UpdateUserResponsePayload,
)


def resolve_update_user(
    _, info, token, user_details, credentials: str | None = None
) -> UpdateUserResponsePayload:
    ...
