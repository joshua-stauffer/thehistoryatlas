from typing import Dict, Union

from the_history_atlas.api.context import Info
from the_history_atlas.apps.domain.models.commands.annotate_citation_input import (
    AnnotateCitationInput,
    TagInput,
    MetaDataInput,
)
from the_history_atlas.apps.domain.models.commands.publish_citation import (
    PublishCitationResponse,
    PublishCitationPayload,
    Person,
    Place,
    Time,
    Meta,
    MetaKwargs,
)


def resolve_publish_new_citation(
    _, info: Info, Annotation: Dict
) -> PublishCitationResponse:
    writemodel_app = info.context.apps.writemodel_app

    publish_citation = AnnotateCitationInput.parse_obj(obj=Annotation)
    payload = transform_input_to_payload(input=publish_citation)
    command_result = writemodel_app.publish_citation(payload=payload)

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


def transform_input_to_payload(input: AnnotateCitationInput) -> PublishCitationPayload:
    return PublishCitationPayload(
        id=input.citationId,
        text=input.citation,
        summary=input.summary,
        summary_id=input.summaryId,
        token=input.token,
        meta=transform_meta(input.meta),
        tags=[transform_tag(tag) for tag in input.summaryTags],
    )


def transform_tag(input: TagInput) -> Union[Person, Place, Time]:
    if input.type == "TIME":
        return Time(
            type="TIME",
            id=input.id,
            name=input.name,
            start_char=input.startChar,
            stop_char=input.stopChar,
        )
    elif input.type == "PLACE":
        return Place(
            type="PLACE",
            id=input.id,
            name=input.name,
            start_char=input.startChar,
            stop_char=input.stopChar,
            geo_shape=input.geoshape,
            latitude=input.latitude,
            longitude=input.longitude,
        )
    elif input.type == "PERSON":
        return Person(
            type="PERSON",
            id=input.id,
            name=input.name,
            start_char=input.startChar,
            stop_char=input.stopChar,
        )
    else:
        raise ValueError(f"Unknown tag received: {input.type}")


def transform_meta(input: MetaDataInput) -> Meta:
    return Meta(
        id=input.id,
        author=input.author,
        publisher=input.publisher,
        title=input.title,
        kwargs=MetaKwargs(
            pageNum=input.pageNum, accessDate=input.accessDate, pubDate=input.pubDate
        ),
    )
