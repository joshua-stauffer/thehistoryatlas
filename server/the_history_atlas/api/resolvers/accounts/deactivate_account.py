from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.accounts.deactivate_account import (
    DeactivateAccountResponsePayload,
    DeactivateAccountPayload,
)


def resolve_deactivate_account(
    _, info: Info, token: str, username: str
) -> DeactivateAccountResponsePayload:
    app = info.context.apps.accounts_app
    deactivate_account_input = DeactivateAccountPayload(token=token, username=username)
    deactivate_account_output = app.deactivate_account(data=deactivate_account_input)
    return deactivate_account_output
