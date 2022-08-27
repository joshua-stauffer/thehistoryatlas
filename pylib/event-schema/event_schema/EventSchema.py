"""
SQLAlchemy database schema for the primary store of events in the History Atlas.
Used by both the History service and the EventStore.
"""

from sqlalchemy import INTEGER, Column
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    index = Column(INTEGER, primary_key=True)
    type = Column(VARCHAR, nullable=False)  # string
    transaction_id = Column(
        VARCHAR, nullable=False
    )  # group atomic events together if necessary
    app_version = Column(
        VARCHAR, nullable=False
    )  # keep track of which version created this event
    # to help with future compatability
    timestamp = Column(VARCHAR, nullable=False)  # Www, dd Mmm yyyy hh:mm:ss GMT
    user_id = Column(VARCHAR, nullable=False)  # user guid
    payload = Column(JSONB, nullable=False)

    def __repr__(self):
        return (
            f"Event(index: {self.index!r}, type: {self.type!r}, "
            + f"user: {self.user_id!r}, payload: {self.payload!r}, "
            + f"timestamp: {self.timestamp!r} transaction: {self.transaction_id!r}, "
            + f"app version: {self.app_version!r})"
        )

    def to_dict(self):
        """returns a dict representation of this Event"""
        return {
            "index": self.index,
            "type": self.type,
            "transaction_id": self.transaction_id,
            "app_version": self.app_version,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "payload": self.payload,
        }
