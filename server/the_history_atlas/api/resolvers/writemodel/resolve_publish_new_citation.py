from dataclasses import asdict
from typing import Dict

from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.commands import Entity
from the_history_atlas.apps.domain.models.commands.publish_citation import (
    PublishCitationResponse,
    PublishCitation,
    PublishCitationPayload,
    Meta,
    Person,
    Place,
    Time,
)


def resolve_publish_new_citation(
    _, info: Info, annotation: Dict
) -> PublishCitationResponse:
    writemodel_app = info.context.apps.writemodel_app
    publish_citation = PublishCitationPayload.parse_obj(obj=annotation)
    command_result = writemodel_app.publish_citation(payload=publish_citation)
    if command_result.type == "COMMAND_SUCCESS":
        success = True
        message = None
    else:
        success = False
        message = command_result.payload.reason
    return PublishCitationResponse(
        success=success,
        message=message,
        token=command_result.token,
    )
