from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.schema import Base


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def readmodel_db(engine):

    db = Database(database_client=engine, stm_timeout=0)

    # if we're using db, ensure its fresh
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine, future=True) as session:
        session.add_all(
            [
                # add any necessary seed data here
            ]
        )
        session.commit()

    yield db

    # cleanup
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
