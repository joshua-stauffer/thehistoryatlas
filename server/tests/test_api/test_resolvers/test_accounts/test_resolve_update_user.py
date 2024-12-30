from the_history_atlas.api.resolvers import resolve_update_user


def test_resolve_update_user(info, accounts_app):
    token = "test-token"
    user_details = {"f_name": "new_name", "password": "test-1-2-3"}
    credentials = {"username": "test", "password": "test"}
    output = resolve_update_user(
        None, info, token=token, user_details=user_details, credentials=credentials
    )
    assert output == accounts_app.update_user.return_value
