from typing import Union

from abstract_domain_model.models.commands.command_failed import (
    CommandFailed,
    CommandFailedPayload,
)
from abstract_domain_model.models.commands.command_success import CommandSuccess
from abstract_domain_model.models.commands.publish_citation import (
    PublishCitation,
    PublishCitationPayload,
    Person,
    Place,
    LegacyTime,
    Meta,
)

Command = Union[PublishCitation]
CommandResponse = Union[CommandSuccess, CommandFailed]
Entity = Union[Person, Place, LegacyTime]
