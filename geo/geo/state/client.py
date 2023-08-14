from sqlalchemy.orm import Session
from server.the_history_atlas import Config
from server.the_history_atlas import Database

if __name__ == "__main__":
    config = Config()
    db = Database(config)
    engine = db._engine
    session = Session(engine, future=True)
    print("." * 79)
    print("\nWelcome to the Geo database interactive client.\n")
    print("The following objects are available in the local namespace:")
    for obj in (
        "db: Database()",
        "session",
        "Place",
        "Name",
        "UpdateTracker",
        "engine",
    ):
        print(obj)
    print("\nEnjoy !\n")
    print("." * 79)
