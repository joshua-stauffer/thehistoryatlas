from typing import Union, Literal

from the_history_atlas.apps.domain.models import (
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
from the_history_atlas.apps.domain.models.accounts import (
    Login,
    AddUser,
    GetUser,
    UpdateUser,
    IsUsernameUnique,
    DeactivateAccount,
    ConfirmAccount,
)
from the_history_atlas.apps.domain.models.accounts.get_user import GetUserResponse
from the_history_atlas.apps.domain.models.commands.publish_citation import Meta, MetaKwargs
from the_history_atlas.apps.domain.models.events.meta_tagged import MetaTagged

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

AccountEvent = Union[
    Login,
    AddUser,
    GetUser,
    GetUserResponse,
    UpdateUser,
    IsUsernameUnique,
    DeactivateAccount,
    ConfirmAccount,
]

AccountEventTypes = Literal[
    "LOGIN",
    "ADD_USER",
    "GET_USER",
    "GET_USER_RESPONSE",
    "UPDATE_USER",
    "IS_USERNAME_UNIQUE",
    "DEACTIVATE_ACCOUNT",
    "CONFIRM_ACCOUNT",
]

DomainObject = Union[
    Command,
    Event,
    AccountEvent,
]

DomainObjectTypes = Union[
    CommandTypes,
    EventTypes,
    AccountEventTypes,
]

PublishCitationType = type(
    PublishCitation(
        user_id="",
        app_version="",
        timestamp="",
        payload=PublishCitationPayload(
            id="",
            token="",
            text="",
            summary="",
            summary_id=None,
            tags=[],
            meta=Meta(author="", publisher="", id=None, title="", kwargs=MetaKwargs()),
        ),
    )
)

EntityType = Literal["PERSON", "PLACE", "TIME"]
