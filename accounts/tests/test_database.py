
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schema import User


def test_add_user(db, user_details):
    #del user_details['id']
    with Session(db._engine, future=True) as session:
        res = session.execute(
            select(User)
        ).scalars()
        assert len([r for r in res]) == 0, 'There shouldn\'t be any users in database.'

    db.add_user(user_details)

    with Session(db._engine, future=True) as session:
        res = session.execute(
            select(User)
        ).scalar_one_or_none()
        assert res is not None, 'There should be one user in database.'
        assert res.password != user_details['password']