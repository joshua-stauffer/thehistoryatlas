"""
SQLAlchemy database schema for the primary store of events in the History Atlas.

Warning: this file is duplicated in History Player and Event Store, and must
be identical in both.

Current version: 2 (4.8.21)
"""

import json
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    type = Column(String(36), nullable=False)           # string or guid
    timestamp = Column(String(32), nullable=False)      # Www, dd Mmm yyyy hh:mm:ss GMT
    user = Column(String(36), nullable=False)           # username string or guid?
    payload = Column(String, nullable=False)            # arbitrary length string
    priority = Column(Integer, nullable=False)          # 0 for preprocessing, 1 for normal
                                                        # leaves open possibility for post processing later

    def __repr__(self):
        return f"Event(id: {self.id!r}, type: {self.type!r}, " \
            + f"user: {self.user!r}, payload: {self.payload!r}" \
            + f"timestamp: {self.timestamp!r} priority: {self.priority!r})"

    def to_dict(self):
        """returns a dict representation of this Event"""
        return {
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp,
            "user": self.user,
            "payload": json.loads(self.payload),
            "priority": self.priority
        }
