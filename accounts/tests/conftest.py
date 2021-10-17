import pytest
from sqlalchemy.orm import Session
from app.database import Database
from app.schema import User

class Config:
    """minimal class for setting up an in memory db for this test"""
    def __init__(self):
        self.DB_URI = 'sqlite+pysqlite:///:memory:'
        self.DEBUG = False


@pytest.fixture
def db():
    c = Config()
    return Database(c)

@pytest.fixture
def user_details():
    return {
        'id': 'a32fb4ef-5e18-4394-8f2b-473e738fdef1',
        'f_name': 'testy',
        'l_name': 'tester',
        'username': 'testersone',
        'password': 'vivaciously',  #
        'type': 'contrib',
    }

@pytest.fixture
def loaded_db(db, user_details):
    with Session(db._engine, future=True) as session:
        session.add(User(**user_details))
        session.commit()
    return db
