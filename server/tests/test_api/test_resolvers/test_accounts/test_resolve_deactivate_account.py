from the_history_atlas.api.resolvers import resolve_deactivate_account


def test_resolve_deactivate_account(info, accounts_app):
    token = "test-token"
    username = "test-username"
    output = resolve_deactivate_account(None, info, token=token, username=username)
    assert output == accounts_app.deactivate_account.return_value
