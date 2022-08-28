from sqlalchemy import select
from sqlalchemy.orm import Session
from geo.config import Config
from geo.state.database import Database
from geo.state.schema import Place
from geo.state.schema import Name
from geo.state.schema import UpdateTracker


if __name__ == '__main__':
    config = Config()
    db = Database(config)
    engine = db._engine
    session = Session(engine, future=True)
    print('.' * 79)
    print('\nWelcome to the Geo database interactive client.\n')
    print('The following objects are available in the local namespace:')
    for obj in ('db: Database()', 'session', 'Place', 'Name', 'UpdateTracker',
                'engine'):
        print(obj)
    print('\nEnjoy !\n')
    print('.' * 79)
