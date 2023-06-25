from the_history_atlas.apps.domain.models.accounts.confirm_account import (
    ConfirmAccountResponsePayload,
)


def resolve_confirm_account(_, info, token) -> ConfirmAccountResponsePayload:
    ...
