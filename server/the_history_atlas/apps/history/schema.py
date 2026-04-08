from sqlalchemy import Column, String, TIMESTAMP, Index, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql.schema import ForeignKey, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import VARCHAR, INTEGER, FLOAT, UUID, JSONB

Base = declarative_base()


class Summary(Base):
    """Model representing a user-created event summary"""

    __tablename__ = "summaries"
    id = Column(UUID(as_uuid=True), primary_key=True)
    text = Column(VARCHAR, unique=True)

    # denormalized time/place fields for spatial-temporal queries
    datetime = Column(VARCHAR, nullable=True)
    calendar_model = Column(VARCHAR, nullable=True)
    precision = Column(INTEGER, nullable=True)
    latitude = Column(FLOAT, nullable=True)
    longitude = Column(FLOAT, nullable=True)

    # When set, this summary covers the same event as the referenced canonical summary.
    # NULL = canonical (first-seen); non-NULL = duplicate, points to the canonical.
    canonical_summary_id = Column(
        UUID(as_uuid=True), ForeignKey("summaries.id"), nullable=True
    )

    # specific instances of tags anchored in the summary text
    tags = relationship("TagInstance", back_populates="summary")

    # each summary may have multiple citations
    citations = relationship("Citation", back_populates="summary")

    # Add hash index for faster text lookups
    __table_args__ = (Index("idx_summaries_text", text, postgresql_using="hash"),)


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

    # Add index for faster citation lookup by summary
    __table_args__ = (Index("idx_citations_summary_id", summary_id),)


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
    # Offset from PDF page number to printed book page number.
    # book_page = citations.page_num - pdf_page_offset
    pdf_page_offset = Column(INTEGER, nullable=False, default=0, server_default="0")


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

    story_order = Column(INTEGER, nullable=True)
    __table_args__ = (
        UniqueConstraint("story_order", "tag_id", name="uq_story_order"),
        # Add index for faster story order operations
        Index("idx_tag_instances_tag_id_story_order", tag_id, story_order),
    )
    after = Column(
        JSONB, nullable=True, default={}
    )  # semantic ordering data independent of dates


# Add index for tag_names for faster lookups
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
    Index("idx_tag_names_composite", "tag_id", "name_id"),
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
    __table_args__ = (
        # Add index for faster lookup of tags by wikidata_id
        Index(
            "idx_tags_wikidata_id",
            wikidata_id,
            postgresql_where=wikidata_id.isnot(None),
        ),
    )


class Time(Tag):

    __tablename__ = "times"
    id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True)
    datetime = Column(VARCHAR, index=True)
    calendar_model = Column(String(64))
    #  6 - millennium, 7 - century, 8 - decade, 9 - year, 10 - month, 11 - day
    precision = Column(INTEGER)

    __mapper_args__ = {"polymorphic_identity": "TIME"}
    __table_args__ = (
        # Add composite index for faster time lookups
        Index("idx_times_lookup", datetime, calendar_model, precision),
        # Add index for faster time-based story lookups
        Index("idx_times_datetime", datetime),
    )


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
    __table_args__ = (
        # Add index for faster spatial searches
        Index(
            "idx_places_coordinates",
            latitude,
            longitude,
            postgresql_where=(latitude.isnot(None) & longitude.isnot(None)),
        ),
    )


class Name(Base):
    __tablename__ = "names"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(VARCHAR, unique=True, nullable=False)
    tags = relationship("Tag", secondary=tag_names, back_populates="names")

    # Add GIN index for trigram-based fuzzy search
    __table_args__ = (
        Index(
            "idx_names_trgm_gin",
            name,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True)
    key_hash = Column(VARCHAR, nullable=False, unique=True)
    user_id = Column(VARCHAR, ForeignKey("users.id"), nullable=False)
    name = Column(VARCHAR, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    last_used_at = Column(TIMESTAMP, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (Index("idx_api_keys_key_hash", key_hash),)


class TextReaderStory(Base):
    """A curated story grouping summaries from a text source."""

    __tablename__ = "stories"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(VARCHAR, nullable=False)
    description = Column(VARCHAR, nullable=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)

    summaries = relationship("StorySummary", back_populates="story")

    __table_args__ = (Index("idx_stories_source_id", source_id),)


class StorySummary(Base):
    """Links a summary to a text-reader story with ordering."""

    __tablename__ = "story_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=False)
    summary_id = Column(UUID(as_uuid=True), ForeignKey("summaries.id"), nullable=False)
    position = Column(INTEGER, nullable=False)

    story = relationship("TextReaderStory", back_populates="summaries")

    __table_args__ = (
        UniqueConstraint("story_id", "summary_id", name="uq_story_summary"),
        UniqueConstraint("story_id", "position", name="uq_story_position"),
    )



class Theme(Base):
    """A hierarchical category for classifying historical events."""

    __tablename__ = "themes"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(VARCHAR, nullable=False, unique=True)
    slug = Column(VARCHAR, nullable=False, unique=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), nullable=True)
    display_order = Column(INTEGER, nullable=False)

    parent = relationship("Theme", remote_side="Theme.id", back_populates="children")
    children = relationship("Theme", back_populates="parent")
    summary_themes = relationship("SummaryTheme", back_populates="theme")

    __table_args__ = (Index("idx_themes_parent_id", parent_id),)


class SummaryTheme(Base):
    """Associates a theme with a summary, with optional confidence score."""

    __tablename__ = "summary_themes"

    id = Column(UUID(as_uuid=True), primary_key=True)
    summary_id = Column(UUID(as_uuid=True), ForeignKey("summaries.id"), nullable=False)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    confidence = Column(FLOAT, nullable=True)

    summary = relationship("Summary")
    theme = relationship("Theme", back_populates="summary_themes")

    __table_args__ = (
        UniqueConstraint("summary_id", "theme_id", name="uq_summary_theme"),
        Index("idx_summary_themes_summary_id", summary_id),
        Index("idx_summary_themes_theme_id", theme_id),
    )
