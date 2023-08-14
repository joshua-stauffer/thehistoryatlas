import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from the_history_atlas.apps.accounts.schema import User
from the_history_atlas.apps.accounts.database import PROTECTED_FIELDS
from the_history_atlas.apps.accounts.errors import UnauthorizedUserError
from the_history_atlas.apps.accounts.encryption import fernet


def test_admin_can_add_user(
    accounts_db, engine, other_user_details, active_admin_token
):
    token, user = accounts_db.add_user(
        token=active_admin_token, user_details=other_user_details
    )

    # double check that this worked
    with Session(engine, future=True) as session:
        res = session.execute(
            select(User).where(User.username == user["username"])
        ).scalar_one_or_none()
        assert res is not None, "This user should exist in the database."
        assert res.password != other_user_details["password"]


def test_non_admin_cant_add_user(accounts_loaded_db, user_details, active_token):
    user_details["username"] = "something else"
    with pytest.raises(UnauthorizedUserError):
        accounts_loaded_db.add_user(token=active_token, user_details=user_details)


def test_add_user_cant_create_admin(accounts_loaded_db, active_token):
    with pytest.raises(UnauthorizedUserError):
        accounts_loaded_db.add_user(
            token=active_token,
            user_details={
                "username": "bohdi",
                "f_name": "b",
                "l_name": "s",
                "email": "some@email",
                "type": "admin",
            },
        )


def test_partial_update_user(accounts_loaded_db, user_details, active_token):
    updated_user_info = {
        "f_name": "happy",
        "l_name": "gilmore",
    }
    accounts_loaded_db.update_user(
        token=active_token, user_details=updated_user_info, credentials=None
    )

    # verify
    with Session(accounts_loaded_db._engine, future=True) as session:
        user = session.execute(
            select(User).where(User.id == user_details["id"])
        ).scalar_one()
        assert user.f_name == updated_user_info["f_name"]
        assert user.l_name == updated_user_info["l_name"]
        assert user.email == user_details["email"]


def test_update_login_creds_fails_without_login(
    accounts_loaded_db, active_token, user_details
):
    username_test = {"username": "nope"}
    password_test = {"password": "nope"}
    with pytest.raises(
        KeyError
    ):  # gets translated to a MissingFieldsError in QueryHandler
        accounts_loaded_db.update_user(
            token=active_token, user_details=username_test, credentials=None
        )
    with pytest.raises(KeyError):
        accounts_loaded_db.update_user(
            token=active_token, user_details=password_test, credentials=None
        )

    # verify
    with Session(accounts_loaded_db._engine, future=True) as session:
        user = session.execute(
            select(User).where(User.id == user_details["id"])
        ).scalar_one()
        assert user.username == user_details["username"]
        assert (
            fernet.decrypt(user.password.encode()).decode() == user_details["password"]
        )


def test_update_login_creds_with_login(accounts_loaded_db, active_token, user_details):
    new_details = {"username": "fanciful", "password": "unlikely"}
    accounts_loaded_db.update_user(
        token=active_token,
        user_details=new_details,
        credentials={
            "username": user_details["username"],
            "password": user_details["password"],
        },
    )
    # verify
    with Session(accounts_loaded_db._engine, future=True) as session:
        user = session.execute(
            select(User).where(User.id == user_details["id"])
        ).scalar_one()
        assert user.username == new_details["username"]
        assert (
            fernet.decrypt(user.password.encode()).decode() == new_details["password"]
        )


def test_update_protected_field(accounts_loaded_db, active_token):

    for field in PROTECTED_FIELDS:
        with pytest.raises(UnauthorizedUserError):
            accounts_loaded_db.update_user(
                token=active_token,
                user_details={field: "cant change this"},
                credentials=None,
            )


def test_admin_can_update_protected_fields(accounts_loaded_db, active_admin_token):

    accounts_loaded_db.update_user(
        active_admin_token,
        user_details={
            "id": "some id",
            "last_login": "tomorrow",
            "deactivated": True,
            "confirmed": False,
        },
        credentials=None,
    )


def test_get_user(
    accounts_loaded_db, active_admin_token, admin_user_id, admin_user_details
):
    token, user_details = accounts_loaded_db.get_user(active_admin_token)
    assert token == active_admin_token
    with Session(accounts_loaded_db._engine, future=True) as session:
        user = session.execute(
            select(User).where(User.id == admin_user_id)
        ).scalar_one()
        assert user
        assert user.f_name == user_details["f_name"]
        assert user.l_name == user_details["l_name"]
        assert user.username == user_details["username"]
        assert user.email == user_details["email"]
        assert user.last_login == user_details["last_login"]


def test_login(accounts_loaded_db, admin_user_details):
    username = admin_user_details["username"]
    password = admin_user_details["password"]
    user_id = admin_user_details["id"]
    token = accounts_loaded_db.login(username=username, password=password)
    # user_id, token = validate_token(token)
    # assert user_id == user_id


def test_is_username_unique(accounts_loaded_db, user_details):
    this_username_exists = user_details["username"]
    this_username_is_unique = "pretty sure no one has chosen this one yet..."
    is_false = accounts_loaded_db.check_if_username_is_unique(this_username_exists)
    is_true = accounts_loaded_db.check_if_username_is_unique(this_username_is_unique)
    assert is_false is False
    assert is_true is True


def test_deactivate_account_with_admin_token(
    accounts_loaded_db, active_admin_token, user_id, user_details
):
    token, user_details = accounts_loaded_db.deactivate_account(
        token=active_admin_token, username=user_details["username"]
    )
    assert token == active_admin_token

    with Session(accounts_loaded_db._engine, future=True) as session:
        user = session.execute(select(User).where(User.id == user_id)).scalar_one()
        assert user.deactivated is True


def test_deactivate_account_with_non_admin_token(
    accounts_loaded_db, active_token, user_id, user_details
):

    with pytest.raises(UnauthorizedUserError):
        accounts_loaded_db.deactivate_account(
            token=active_token, username=user_details["username"]
        )

    with Session(accounts_loaded_db._engine, future=True) as session:
        user = session.execute(select(User).where(User.id == user_id)).scalar_one()
        assert user.deactivated is False


def test_confirm_account(
    accounts_loaded_db, unconfirmed_user_id, unconfirmed_user_token
):

    token, user_details = accounts_loaded_db.confirm_account(unconfirmed_user_token)
    with Session(accounts_loaded_db._engine, future=True) as session:
        user = session.execute(
            select(User).where(User.id == unconfirmed_user_id)
        ).scalar_one()
        assert user.confirmed is True


def test_require_admin_user_with_admin(accounts_loaded_db, admin_user_id):
    with Session(accounts_loaded_db._engine, future=True) as session:
        assert accounts_loaded_db._require_admin_user(admin_user_id, session)


def test_require_admin_user_without_admin(accounts_loaded_db, user_id):
    with Session(accounts_loaded_db._engine, future=True) as session:
        with pytest.raises(UnauthorizedUserError):
            accounts_loaded_db._require_admin_user(user_id, session)
