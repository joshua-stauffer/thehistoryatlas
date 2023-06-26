from the_history_atlas.api.resolvers import resolve_confirm_account


def test_resolve_confirm_account(info, accounts_app):
    token = "test-token"
    output = resolve_confirm_account(None, info, token=token)
    assert output == accounts_app.confirm_account.return_value
