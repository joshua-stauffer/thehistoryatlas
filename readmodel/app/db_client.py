"""Provides easy shell access to the database"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from tha_config import Config
from app.state_manager.manager import Manager
from app.state_manager.schema import Citation
from app.state_manager.schema import TagInstance
from app.state_manager.schema import Tag
from app.state_manager.schema import Time
from app.state_manager.schema import Person
from app.state_manager.schema import Place
from app.state_manager.schema import Name
from app.state_manager.schema import History

if __name__ == '__main__':
    config = Config()
    manager = Manager(config)
    db = manager.db
    engine = db._engine
    print('.' * 79)
    print('\nWelcome to the Read Model interactive client.\n')
    print('The following objects are available in the local namespace:')
    for obj in ('manager: Manager()', 'db: Database()', 'engine: Database._engine()',
                'Citation', 'TagInstance', 'Tag', 'Time', 'Person', 'Place',
                'Name', 'History',
                'select', 'Session'
                ):
        print(obj)
    print('\nenjoy!\n')
    print('.' * 79)
