from the_history_atlas.apps.domain.models.accounts.deactivate_account import (
    DeactivateAccountResponsePayload,
)


def resolve_deactivate_account(
    _, info, token, username
) -> DeactivateAccountResponsePayload:
    ...
