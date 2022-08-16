from typing import Union
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

Event = Union[
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
]

Command = Union[PublishCitation]

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
