from sqlalchemy import Column, String, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER, FLOAT, UUID, JSONB

Base = declarative_base()


class Summary(Base):
    """Model representing a user-created event summary"""

    __tablename__ = "summaries"
    id = Column(UUID(as_uuid=True), primary_key=True)
    text = Column(VARCHAR, unique=True)

    # specific instances of tags anchored in the summary text
    tags = relationship("TagInstance", back_populates="summary")

    # each summary may have multiple citations
    citations = relationship("Citation", back_populates="summary")


class StoryName(Base):
    __tablename__ = "story_names"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False)
    name = Column(VARCHAR, nullable=False)
    lang = Column(VARCHAR, nullable=False)
    description = Column(VARCHAR, nullable=True)


class Citation(Base):
    """Model representing citations and their metadata, with links to
    their tags"""

    __tablename__ = "citations"
    id = Column(UUID(as_uuid=True), primary_key=True)
    text = Column(VARCHAR)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"))
    source = relationship("Source", back_populates="citations")
    summary_id = Column(UUID(as_uuid=True), ForeignKey("summaries.id"))
    summary = relationship("Summary", back_populates="citations")
    page_num = Column(INTEGER)
    access_date = Column(VARCHAR)
    wikidata_item_id = Column(VARCHAR)
    wikidata_item_title = Column(VARCHAR)
    wikidata_item_url = Column(VARCHAR)


class Source(Base):
    """
    Source meta data.
    """

    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    citations = relationship("Citation", back_populates="source")
    title = Column(VARCHAR, nullable=False)
    author = Column(VARCHAR, nullable=False)
    publisher = Column(VARCHAR, nullable=False)
    pub_date = Column(VARCHAR, nullable=True)
    kwargs = Column(JSONB, nullable=False, default={})


class TagInstance(Base):
    """Model representing the connection point between a summary slice and
    a tag."""

    __tablename__ = "tag_instances"
    id = Column(UUID(as_uuid=True), primary_key=True)
    start_char = Column(INTEGER)
    stop_char = Column(INTEGER)
    # parent summary
    summary_id = Column(UUID(as_uuid=True), ForeignKey("summaries.id"))
    summary = relationship("Summary", back_populates="tags")
    # parent tag
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), index=True)
    tag = relationship("Tag", back_populates="tag_instances")

    story_order = Column(INTEGER, nullable=False)
    __table_args__ = (UniqueConstraint("story_order", "tag_id", name="uq_story_order"),)


tag_names = Table(
    "tag_names",
    Base.metadata,
    Column(
        "tag_id", UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False, index=True
    ),
    Column(
        "name_id",
        UUID(as_uuid=True),
        ForeignKey("names.id"),
        nullable=False,
        index=True,
    ),
    UniqueConstraint("tag_id", "name_id"),
)


class Tag(Base):
    """Base class for time, person, and place tags"""

    __tablename__ = "tags"
    id = Column(UUID(as_uuid=True), primary_key=True)
    type = Column(VARCHAR)  # 'TIME' | 'PERSON' | 'PLACE'
    wikidata_id = Column(VARCHAR, nullable=True, unique=True)
    wikidata_url = Column(VARCHAR, nullable=True, unique=True)
    tag_instances = relationship("TagInstance", back_populates="tag")
    names = relationship("Name", secondary=tag_names, back_populates="tags")

    __mapper_args__ = {"polymorphic_identity": "TAG", "polymorphic_on": type}


class Time(Tag):

    __tablename__ = "times"
    id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True)
    datetime = Column(VARCHAR, index=True)
    calendar_model = Column(String(64))
    #  6 - millennium, 7 - century, 8 - decade, 9 - year, 10 - month, 11 - day
    precision = Column(INTEGER)

    __mapper_args__ = {"polymorphic_identity": "TIME"}


class Person(Tag):

    __tablename__ = "people"
    id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "PERSON"}


class Place(Tag):

    __tablename__ = "places"

    id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True)
    latitude = Column(FLOAT, index=True)
    longitude = Column(FLOAT, index=True)
    geoshape = Column(VARCHAR)
    geonames_id = Column(INTEGER)

    __mapper_args__ = {"polymorphic_identity": "PLACE"}


class Name(Base):
    __tablename__ = "names"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(VARCHAR, unique=True, nullable=False)
    tags = relationship("Tag", secondary=tag_names, back_populates="names")
