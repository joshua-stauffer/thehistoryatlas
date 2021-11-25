import pytest
from app.query_handler import QueryHandler


@pytest.fixture
def handler(loaded_db):
    """An active QueryHandler class"""
    qh = QueryHandler(database_instance=loaded_db)
    return qh.handle_query


def test_login(handler, user_details):
    query = {
        "type": "LOGIN",
        "payload": {
            "username": user_details["username"],
            "password": user_details["password"],
        },
    }
    res = handler(query)
    assert res["type"] == "LOGIN"
    assert isinstance(res["payload"], dict)
    assert res["payload"]["success"] is True
    assert isinstance(res["payload"]["token"], bytes)


def test_add_user(handler, active_admin_token, other_user_details):
    query = {
        "type": "ADD_USER",
        "payload": {"token": active_admin_token, "user_data": {**other_user_details}},
    }
    res = handler(query)
    assert res["type"] == "ADD_USER"
    assert isinstance(res["payload"], dict)
    assert res["payload"]["token"] is active_admin_token
    assert isinstance(res["payload"]["user_details"], dict)


def test_get_user(handler, active_token):
    query = {"type": "GET_USER", "payload": {"token": active_token}}
    res = handler(query)
    assert res["type"] == "GET_USER"
    assert isinstance(res["payload"], dict)
    assert res["payload"]["token"] is active_token
    assert isinstance(res["payload"]["user_details"], dict)


def test_update_user(handler, active_token):
    query = {
        "type": "UPDATE_USER",
        "payload": {"token": active_token, "user_data": {"f_name": "sebastian"}},
    }
    res = handler(query)
    assert res["type"] == "UPDATE_USER"
    assert isinstance(res["payload"], dict)
    assert res["payload"]["token"] is active_token
    assert isinstance(res["payload"]["user_details"], dict)


def test_is_username_unique(handler):
    query = {"type": "IS_USERNAME_UNIQUE", "payload": {"username": "ludovico"}}
    res = handler(query)
    assert res["type"] == "IS_USERNAME_UNIQUE"
    assert isinstance(res["payload"], dict)
    assert isinstance(res["payload"]["is_unique"], bool)
    assert isinstance(res["payload"]["username"], str)


def test_deactivate_account(handler, active_admin_token, user_id):
    query = {
        "type": "DEACTIVATE_ACCOUNT",
        "payload": {"token": active_admin_token, "user_id": user_id},
    }
    res = handler(query)
    assert res["type"] == "DEACTIVATE_ACCOUNT"
    assert isinstance(res["payload"], dict)
    assert res["payload"]["token"] is active_admin_token
    assert isinstance(res["payload"]["user_details"], dict)


def test_confirm_account(handler, unconfirmed_user_token):
    query = {"type": "CONFIRM_ACCOUNT", "payload": {"token": unconfirmed_user_token}}
    res = handler(query)
    assert res["type"] == "CONFIRM_ACCOUNT"
    assert isinstance(res["payload"], dict)
    # emailed tokens should be changed immediately
    assert res["payload"]["token"] is not unconfirmed_user_token
    assert isinstance(res["payload"]["user_details"], dict)
