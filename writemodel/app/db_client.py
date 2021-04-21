"""Provides easy shell access to the database"""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from write_model import WriteModel
from state_manager.schema import CitationHash

enjoy = 'wait, what?'

if __name__ == '__main__':
    wm = WriteModel()
    db = wm.manager.db
    engine = db._engine
    print('.' * 79)
    print('\nWelcome to the EventStore interactive client.\n')
    print('The following objects are available in the local namespace:')
    for obj in ('wm: WriteModel()', 'db: Database()', 'engine: Database._engine()',
                'CitationHash',
                'select', 'Session'
                ):
        print(obj)
    print('\nenjoy!\n')
    print('.' * 79)
