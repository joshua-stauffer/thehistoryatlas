"""
SQLAlchemy database schema for the primary store of events in the History Atlas.
Used by both the History service and the EventStore.
"""
#NOTE: previous versions of this file were duplicated in multiple places, but
#      this is no longer the case.

import json
from sqlalchemy import INTEGER, Column
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'

    id = Column(INTEGER, primary_key=True)
    type = Column(VARCHAR, nullable=False)               # string
    transaction_guid = Column(VARCHAR, nullable=False)   # group atomic events together if necessary
    app_version = Column(VARCHAR, nullable=False)         # keep track of which version created this event
                                                            # to help with future compatability
    timestamp = Column(VARCHAR, nullable=False)          # Www, dd Mmm yyyy hh:mm:ss GMT
    user = Column(VARCHAR, nullable=False)               # user guid
    payload = Column(VARCHAR, nullable=False)                # arbitrary length string


    def __repr__(self):
        return f"Event(id: {self.id!r}, type: {self.type!r}, " \
            + f"user: {self.user!r}, payload: {self.payload!r}, " \
            + f"timestamp: {self.timestamp!r} transaction: {self.transaction_guid!r}, " \
            + f"app version: {self.app_version!r})"

    def to_dict(self):
        """returns a dict representation of this Event"""
        return {
            "event_id": self.id,
            "type": self.type,
            "transaction_guid": self.transaction_guid,
            "app_version": self.app_version,
            "timestamp": self.timestamp,
            "user": self.user,
            "payload": json.loads(self.payload),
        }
