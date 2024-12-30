from the_history_atlas.api.resolvers import resolve_login


def test_resolve_login(info, accounts_app):
    username = "test-username"
    password = "test-password"
    output = resolve_login(None, info, username=username, password=password)
    assert output == accounts_app.login.return_value
