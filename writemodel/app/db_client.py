"""Provides easy shell access to the database"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from tha_config import Config
from app.state_manager.manager import Manager
from app.state_manager.schema import Base
from app.state_manager.schema import GUID
from app.state_manager.schema import CitationHash
from app.state_manager.schema import History



if __name__ == '__main__':
    config = Config()
    manager = Manager(config)
    db = manager.db
    engine = db._engine
    print('.' * 79)
    print('\nWelcome to the Write Model interactive client.\n')
    print('The following objects are available in the local namespace:')
    for obj in ('manager: Manager()', 'db: Database()', 'engine: Database._engine()',
                'CitationHash (db schema)', 'GUID (db schema)', 'History (db schema)',
                'select', 'Session'
                ):
        print(obj)
    session = Session(engine, future=True)
    print('\nAn active database connection is available as session\n')
    print('.' * 79)
