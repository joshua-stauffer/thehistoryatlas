from the_history_atlas.api.resolvers import resolve_get_user


def test_resolve_get_user(info, accounts_app):
    token = "test-token"
    output = resolve_get_user(None, info, token=token)
    assert output == accounts_app.get_user.return_value
