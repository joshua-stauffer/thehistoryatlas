"""SQLAlchemy database schema for the Read Model service.

May 3rd 2021
"""

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER, FLOAT
from app.errors import EmptyNameError

Base = declarative_base()


class Summary(Base):
    """Model representing a user-created event summary"""

    __tablename__ = "summaries"
    id = Column(INTEGER, primary_key=True)
    guid = Column(VARCHAR)
    text = Column(VARCHAR)

    # specific instances of tags anchored in the summary text
    tags = relationship("TagInstance", back_populates="summary")

    # TODO: this won't work with multiple time tags, gotta figure out a more
    #       efficient way to calculate the correct time
    time_tag = Column(VARCHAR)  # cache timetag name for sorting

    # each summary may have multiple citations
    citations = relationship("Citation", back_populates="summary")


class Citation(Base):
    """Model representing citations and their meta data, with links to
    their tags"""

    __tablename__ = "citations"
    id = Column(INTEGER, primary_key=True)
    guid = Column(VARCHAR(36))
    text = Column(VARCHAR)
    # meta data stored as json string with arbitrary fields
    # not planning on querying against this, just need it available
    meta = Column(VARCHAR)
    summary_id = Column(INTEGER, ForeignKey("summaries.id"))
    summary = relationship("Summary", back_populates="citations")

    def __repr__(self):
        return f"Citation(id: {self.id}, text: {self.text}, meta: {self.meta})"


class TagInstance(Base):
    """Model representing the connection point between a summary slice and
    a tag."""

    __tablename__ = "taginstances"
    id = Column(INTEGER, primary_key=True)
    start_char = Column(INTEGER)
    stop_char = Column(INTEGER)
    # parent summary
    summary_id = Column(INTEGER, ForeignKey("summaries.id"))
    summary = relationship("Summary", back_populates="tags")
    # parent tag
    tag_id = Column(INTEGER, ForeignKey("tags.id"))
    tag = relationship("Tag", back_populates="tag_instances")

    def __repr__(self):
        return f"{self.tag.type}"


class Tag(Base):
    """Base class for time, person, and place tags"""

    __tablename__ = "tags"
    id = Column(INTEGER, primary_key=True)
    guid = Column(VARCHAR)
    type = Column(VARCHAR)  # 'TIME' | 'PERSON' | 'PLACE'
    tag_instances = relationship("TagInstance", back_populates="tag")

    __mapper_args__ = {"polymorphic_identity": "TAG", "polymorphic_on": type}


class Time(Tag):

    __tablename__ = "time"
    id = Column(INTEGER, ForeignKey("tags.id"), primary_key=True)
    name = Column(VARCHAR)

    __mapper_args__ = {"polymorphic_identity": "TIME"}

    def __repr__(self):
        return f"TimeTag(id: {self.id}, name: {self.name})"


class Person(Tag):

    __tablename__ = "person"
    id = Column(INTEGER, ForeignKey("tags.id"), primary_key=True)
    names = Column(VARCHAR)

    __mapper_args__ = {"polymorphic_identity": "PERSON"}

    def __repr__(self):
        return f"PersonTag(id: {self.id}, names: {self.names})"


class Place(Tag):

    __tablename__ = "place"

    id = Column(INTEGER, ForeignKey("tags.id"), primary_key=True)
    names = Column(VARCHAR)
    latitude = Column(FLOAT)
    longitude = Column(FLOAT)
    geoshape = Column(VARCHAR)

    __mapper_args__ = {"polymorphic_identity": "PLACE"}

    def __repr__(self):
        return f"PlaceTag(id: {self.id}, names: {self.names})"


class Name(Base):

    __tablename__ = "name"

    id = Column(INTEGER, primary_key=True)
    name = Column(VARCHAR)
    _guids = Column(VARCHAR)  # save as | separated values and parse on exit

    @property
    def guids(self):
        return self._guids.split("|")

    @guids.setter
    def guids(self, guid):
        if self._guids:
            raise Exception("GUIDs is already set -- do you mean to erase it?")
        self._guids = guid

    def add_guid(self, guid):
        if self._guids:
            self._guids += "|" + guid
        else:
            self._guids = "|" + guid

    def del_guid(self, guid):
        if guid not in self.guids:
            raise ValueError("That GUID isn't associated with this name")
        if len(self.guids) == 1:
            raise EmptyNameError(
                "This is the last GUID associated with this name."
                + " Please delete entire Name instead of just the GUID."
            )
        tmp = [val for val in self.guids if val != guid]
        self._guids = "|".join(tmp)

    def __repr__(self):
        return f"Name(id: {self.id}, name: {self.name}, guids: {self._guids})"


class History(Base):

    __tablename__ = "history"

    id = Column(INTEGER, primary_key=True)
    latest_event_id = Column(INTEGER, default=0)
