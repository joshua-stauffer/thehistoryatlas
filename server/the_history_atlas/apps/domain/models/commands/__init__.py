from typing import Union

from the_history_atlas.apps.domain.models.commands.command_failed import (
    CommandFailed,
    CommandFailedPayload,
)
from the_history_atlas.apps.domain.models.commands.command_success import CommandSuccess
from the_history_atlas.apps.domain.models.commands.publish_citation import (
    PublishCitation,
    PublishCitationPayload,
    Person,
    Place,
    Time,
    Meta,
)

Command = Union[PublishCitation]
CommandResponse = Union[CommandSuccess, CommandFailed]
Entity = Union[Person, Place, Time]
