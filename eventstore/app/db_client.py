from event_store import EventStore
from sqlalchemy import select
from sqlalchemy.orm import Session
from event_schema.EventSchema import Event

enjoy = "Yay!"

if __name__ == '__main__':
    store = EventStore()
    db = store.db
    engine = store.db._engine
    print('.' * 79)
    print('\nWelcome to the EventStore interactive client.\n')
    print('The following objects are available in the local namespace:')
    for obj in ('store: EventStore()', 'db: Database()', 'engine: Database._engine()', 'Event','select', 'Session'):
        print(obj)
    print('\nEnjoy !\n')
    print('.' * 79)
