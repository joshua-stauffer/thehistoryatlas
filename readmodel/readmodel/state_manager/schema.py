"""SQLAlchemy database schema for the Read Model service.

May 3rd 2021
"""

from sqlalchemy import Column, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER, FLOAT, UUID, JSONB, BOOLEAN
from readmodel.errors import EmptyNameError

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
    source_id = Column(UUID(as_uuid=False), ForeignKey("sources.id"))
    source = relationship("Source", back_populates="citations")
    summary_id = Column(INTEGER, ForeignKey("summaries.id"))
    summary = relationship("Summary", back_populates="citations")
    page_num = Column(INTEGER)
    access_date = Column(VARCHAR)

    def __repr__(self):
        return f"Citation(id: {self.id}, text: {self.text}, meta: {self.meta.id})"


class Source(Base):
    """
    Source meta data.
    """

    __tablename__ = "sources"

    id = Column(UUID(as_uuid=False), primary_key=True, unique=True)
    citations = relationship("Citation", back_populates="source")
    title = Column(VARCHAR, nullable=False)
    author = Column(VARCHAR, nullable=False)
    publisher = Column(VARCHAR, nullable=False)
    pub_date = Column(VARCHAR, nullable=False)
    kwargs = Column(JSONB, nullable=False, default={})


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
    tag_id = Column(UUID(as_uuid=False), ForeignKey("tags.id"))
    tag = relationship("Tag", back_populates="tag_instances")

    def __repr__(self):
        return f"{self.tag.type}"


tags_to_names = Table(
    "tags_to_names",
    Base.metadata,
    Column("tag_id", UUID(as_uuid=False), ForeignKey("tags.id")),
    Column("name_id", UUID(as_uuid=False), ForeignKey("names.id")),
)


class Tag(Base):
    """Base class for time, person, and place tags"""

    __tablename__ = "tags"
    id = Column(UUID(as_uuid=False), primary_key=True)
    type = Column(VARCHAR)  # 'TIME' | 'PERSON' | 'PLACE'
    tag_instances = relationship("TagInstance", back_populates="tag")
    names = relationship("Name", secondary=tags_to_names, back_populates="tags")
    descriptions = relationship("Description", back_populates="tag")

    __mapper_args__ = {"polymorphic_identity": "TAG", "polymorphic_on": type}


class Time(Tag):

    __tablename__ = "times"

    id = Column(UUID(as_uuid=False), ForeignKey("tags.id"), primary_key=True)
    timestamp = Column(VARCHAR)
    precision = Column(INTEGER)
    calendar_type = Column(VARCHAR)
    circa = Column(BOOLEAN)
    latest = Column(BOOLEAN)
    earliest = Column(BOOLEAN)

    __mapper_args__ = {"polymorphic_identity": "TIME"}

    def __repr__(self):
        return f"TimeTag(id: {self.id}, name: {self.name})"


class Person(Tag):

    __tablename__ = "people"

    id = Column(UUID(as_uuid=False), ForeignKey("tags.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "PERSON"}

    def __repr__(self):
        return f"PersonTag(id: {self.id}, names: {self.names})"


class Place(Tag):

    __tablename__ = "places"

    id = Column(UUID(as_uuid=False), ForeignKey("tags.id"), primary_key=True)
    latitude = Column(FLOAT, nullable=False)
    longitude = Column(FLOAT, nullable=False)
    geoshape = Column(VARCHAR)
    population = Column(INTEGER)
    feature_class = Column(VARCHAR)
    feature_code = Column(VARCHAR)
    country_code = Column(VARCHAR)

    __mapper_args__ = {"polymorphic_identity": "PLACE"}

    def __repr__(self):
        return f"PlaceTag(id: {self.id}, names: {self.names})"


class Name(Base):
    """
    map entity IDs to known names.
    """

    __tablename__ = "names"

    id = Column(UUID(as_uuid=False), primary_key=True)
    tags = relationship("Tag", secondary=tags_to_names, back_populates="names")
    name = Column(VARCHAR, unique=True)
    lang = Column(VARCHAR)
    is_default = Column(BOOLEAN)
    is_historic = Column(BOOLEAN)
    start_time = Column(VARCHAR)  # historic
    end_time = Column(VARCHAR)  # historic


class Description(Base):
    """
    store tag descriptions
    """

    __tablename__ = "descriptions"

    id = Column(UUID(as_uuid=False), primary_key=True)
    text = Column(VARCHAR)
    tag_id = Column(UUID(as_uuid=False), ForeignKey("tags.id"))
    tag = relationship("Tag", back_populates="descriptions")
    lang = Column(VARCHAR)
    source_last_updated = Column(VARCHAR)
    wiki_link = Column(VARCHAR)
    wiki_data_id = Column(VARCHAR)


class History(Base):

    __tablename__ = "history"

    id = Column(INTEGER, primary_key=True)
    latest_event_id = Column(INTEGER, default=0)
