from sqlalchemy import text
from sqlalchemy.orm import Session

from the_history_atlas.apps.accounts.encryption import encrypt


def seed_users(engine):
    admin_user =

    with Session(engine, future=True) as session:
        session.execute(text(), {})
        session.commit()