from the_history_atlas.api.context import Info
from the_history_atlas.apps.accounts.accounts import Accounts
from the_history_atlas.apps.domain.models.accounts.confirm_account import (
    ConfirmAccountResponsePayload,
)


def resolve_confirm_account(_, info: Info, token: str) -> ConfirmAccountResponsePayload:
    app: Accounts = info.context.apps.accounts_app
    confirm_account_output = app.confirm_account(token=token)
    return confirm_account_output
