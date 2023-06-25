from the_history_atlas.apps.domain.models.accounts.is_username_unique import (
    IsUsernameUniqueResponsePayload,
)


def resolve_is_username_unique(
    _, info, username: str
) -> IsUsernameUniqueResponsePayload:
    ...
