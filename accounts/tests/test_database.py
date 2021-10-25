import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schema import User
from app.errors import UnauthorizedUserError
from app.schema import PROTECTED_FIELDS


def test_add_user(db, user_details):

    with Session(db._engine, future=True) as session:
        res = session.execute(
            select(User)
        ).scalars()
        assert len([r for r in res]) == 0, 'There shouldn\'t be any users in database.'
    del user_details['id'] # can't set id

    db.add_user(user_details)

    with Session(db._engine, future=True) as session:
        res = session.execute(
            select(User)
        ).scalar_one_or_none()
        assert res is not None, 'There should be one user in database.'
        assert res.password != user_details['password']


def test_add_user_cant_create_admin(loaded_db):
    with pytest.raises(UnauthorizedUserError):
        loaded_db.add_user({
            'username': 'bohdi',
            'f_name': 'b',
            'l_name': 's',
            'email': 'some@email',
            'type': 'admin'
        })


def test_partial_update_user(loaded_db, user_details, active_token):
    updated_user_info = {
        "f_name": "happy",
        "l_name": "gilmore",
    }
    loaded_db.update_user(
        token=active_token,
        user_dict=updated_user_info
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
                user_dict={
                    field: "cant change this"
                }
            )

def test_admin_can_update_protected_fields(loaded_db, active_admin_token):

    loaded_db.update_user(
        active_admin_token,
        user_dict={
            'id': 'some id',
            'last_login': 'tomorrow',
            'deactivated': True,
            'confirmed': False
        }
    )