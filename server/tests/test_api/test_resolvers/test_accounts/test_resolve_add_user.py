from the_history_atlas.api.resolvers import resolve_add_user


def test_resolve_add_user(info, accounts_app):
    token = "test-token"
    user_details = {"username": "test"}
    output = resolve_add_user(None, info, token=token, user_details=user_details)
    assert output == accounts_app.add_user.return_value
