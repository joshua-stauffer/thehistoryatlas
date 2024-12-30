from the_history_atlas.api.resolvers import resolve_is_username_unique


def test_resolve_is_username_unique(info, accounts_app):
    username = "test-username"
    output = resolve_is_username_unique(None, info, username=username)
    assert output == accounts_app.is_username_unique.return_value
