from typing import Union, Literal
from abstract_domain_model.models import (
    TimeAdded,
    TimeTagged,
    PlaceTagged,
    PlaceAdded,
    PersonTagged,
    PersonAdded,
    CitationAdded,
    MetaAdded,
    SummaryAdded,
    SummaryTagged,
    PublishCitation,
    PublishCitationPayload,
)
from abstract_domain_model.models.commands.publish_citation import Meta
from abstract_domain_model.models.events.meta_tagged import MetaTagged

Event = Union[
    TimeAdded,
    TimeTagged,
    PlaceTagged,
    PlaceAdded,
    PersonTagged,
    PersonAdded,
    CitationAdded,
    MetaAdded,
    MetaTagged,
    SummaryAdded,
    SummaryTagged,
]

EventTypes = Literal[
    "TIME_ADDED",
    "TIME_TAGGED",
    "PLACE_TAGGED",
    "PLACE_ADDED",
    "PERSON_TAGGED",
    "PERSON_ADDED",
    "CITATION_ADDED",
    "META_ADDED",
    "META_TAGGED",
    "SUMMARY_ADDED",
    "SUMMARY_TAGGED",
]

Command = Union[PublishCitation]

CommandTypes = Literal["PUBLISH_CITATION"]

# Query = Union[None]

# QueryTypes = Literal[]

DomainObject = Union[
    Command,
    Event,
    # Query,
]

DomainObjectTypes = Union[
    CommandTypes,
    EventTypes,
    # QueryTypes,
]

PublishCitationType = type(
    PublishCitation(
        user_id="",
        app_version="",
        timestamp="",
        payload=PublishCitationPayload(
            id="",
            text="",
            summary="",
            summary_id=None,
            tags=[],
            meta=Meta(author="", publisher="", id=None, title="", kwargs={}),
        ),
    )
)
