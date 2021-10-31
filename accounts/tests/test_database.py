import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schema import User
from app.errors import UnauthorizedUserError
from app.schema import PROTECTED_FIELDS
from app.encryption import validate_token
from app.errors import UnauthorizedUserError


def test_bare_db_is_empty(bare_db):
    with Session(bare_db._engine, future=True) as session:
        res = session.execute(
            select(User)
        ).scalars()
        assert len([r for r in res]) == 0, 'No users to start.'

def test_db_has_one_user(db):
    with Session(db._engine, future=True) as session:
        res = session.execute(
            select(User)
        ).scalars()
        assert len([r for r in res]) == 1, 'Only one admin user to start.'

def test_loaded_db_has_three_users(loaded_db):
    with Session(loaded_db._engine, future=True) as session:
        res = session.execute(
            select(User)
        ).scalars()
        assert len([r for r in res]) == 3, 'Three users to start.'

def test_admin_can_add_user(db, other_user_details, active_admin_token):
    token, user = db.add_user(
        token=active_admin_token,
        user_data=other_user_details
    )

    # double check that this worked
    with Session(db._engine, future=True) as session:
        res = session.execute(
            select(User).where(User.username == user['username'])
        ).scalar_one_or_none()
        assert res is not None, 'This user should exist in the database.'
        assert res.password != other_user_details['password']

def test_non_admin_cant_add_user(loaded_db, user_details, active_token):

    with pytest.raises(UnauthorizedUserError):
        loaded_db.add_user(
            token=active_token,
            user_data=user_details
        )

def test_add_user_cant_create_admin(loaded_db, active_token):
    with pytest.raises(UnauthorizedUserError):
        loaded_db.add_user(
            token=active_token,
            user_data={
                'username': 'bohdi',
                'f_name': 'b',
                'l_name': 's',
                'email': 'some@email',
                'type': 'admin'
            }
        )


def test_partial_update_user(loaded_db, user_details, active_token):
    updated_user_info = {
        "f_name": "happy",
        "l_name": "gilmore",
    }
    loaded_db.update_user(
        token=active_token,
        user_data=updated_user_info
    )

    # verify
    with Session(loaded_db._engine, future=True) as session:
        user = session.execute(
            select(User).where(User.id == user_details["id"])
        ).scalar_one()
        assert user.f_name == updated_user_info['f_name']
        assert user.l_name == updated_user_info['l_name']
        assert user.email == user_details['email']

def test_update_protected_field(loaded_db, active_token):

    for field in PROTECTED_FIELDS:
        with pytest.raises(UnauthorizedUserError):
            loaded_db.update_user(
                token=active_token,
                user_data={
                    field: "cant change this"
                }
            )

def test_admin_can_update_protected_fields(loaded_db, active_admin_token):

    loaded_db.update_user(
        active_admin_token,
        user_data={
            'id': 'some id',
            'last_login': 'tomorrow',
            'deactivated': True,
            'confirmed': False
        }
    )

def test_get_user(loaded_db, active_admin_token, admin_user_id, admin_user_details):
    token, user_details = loaded_db.get_user(active_admin_token)
    assert token is active_admin_token
    with Session(loaded_db._engine, future=True) as session:
        user = session.execute(
            select(User).where(User.id == admin_user_id)
        ).scalar_one()
        assert user
        assert user.f_name == user_details['f_name']
        assert user.l_name == user_details['l_name']
        assert user.username == user_details['username']
        assert user.email == user_details['email']
        assert user.last_login == user_details['last_login']


def test_login(loaded_db, admin_user_details):
    username = admin_user_details['username']
    password = admin_user_details['password']
    user_id = admin_user_details['id']
    token = loaded_db.login(
        username=username,
        password=password
    )
    # user_id, token = validate_token(token)
    # assert user_id == user_id


def test_is_username_unique(loaded_db, user_details):
    this_username_exists = user_details['username']
    this_username_is_unique = 'pretty sure no one has chosen this one yet...'
    is_false = loaded_db.check_if_username_is_unique(this_username_exists)
    is_true = loaded_db.check_if_username_is_unique(this_username_is_unique)
    assert is_false is False
    assert is_true is True

def test_deactivate_account_with_admin_token(
    loaded_db,
    active_admin_token,
    user_id,
):
    token, user_details = loaded_db.deactivate_account(
        token=active_admin_token,
        user_id=user_id
    )
    assert token is active_admin_token

    with Session(loaded_db._engine, future=True) as session:
        user = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one()
        assert user.deactivated is True



def test_deactivate_account_with_non_admin_token( loaded_db,
    active_token,
    user_id,
):
    with pytest.raises(UnauthorizedUserError):
        loaded_db.deactivate_account(
            token=active_token,
            user_id=user_id
        )

    with Session(loaded_db._engine, future=True) as session:
        user = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one()
        assert user.deactivated is False


def test_confirm_account(loaded_db, unconfirmed_user_id, unconfirmed_user_token):

    token, user_details = loaded_db.confirm_account(unconfirmed_user_token)
    with Session(loaded_db._engine, future=True) as session:
        user = session.execute(
            select(User).where(User.id == unconfirmed_user_id)
        ).scalar_one()
        assert user.confirmed is True

def test_require_admin_user_with_admin(loaded_db, admin_user_id):
    with Session(loaded_db._engine, future=True) as session:
        assert loaded_db._require_admin_user(admin_user_id, session)

def test_require_admin_user_without_admin(loaded_db, user_id):
    with Session(loaded_db._engine, future=True) as session:
        with pytest.raises(UnauthorizedUserError):
            loaded_db._require_admin_user(user_id, session)
