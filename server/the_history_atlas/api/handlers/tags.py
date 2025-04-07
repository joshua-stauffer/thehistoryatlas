from the_history_atlas.api.types.tags import (
    WikiDataPersonInput,
    WikiDataPersonOutput,
    WikiDataPlaceInput,
    WikiDataPlaceOutput,
    WikiDataTimeInput,
    WikiDataTimeOutput,
    WikiDataTagsOutput,
    WikiDataTagPointer,
    WikiDataEventInput,
    WikiDataEventOutput,
)
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.domain.core import PersonInput, PlaceInput, TimeInput


def create_person_handler(
    apps: AppManager, person: WikiDataPersonInput
) -> WikiDataPersonOutput:
    input = PersonInput.model_validate(person, from_attributes=True)
    output = apps.history_app.create_person(person=input)
    return WikiDataPersonOutput.model_validate(output, from_attributes=True)


def create_place_handler(
    apps: AppManager, place: WikiDataPlaceInput
) -> WikiDataPlaceOutput:
    input = PlaceInput.model_validate(place, from_attributes=True)
    output = apps.history_app.create_place(place=input)
    return WikiDataPlaceOutput.model_validate(output, from_attributes=True)


def create_time_handler(
    apps: AppManager, time: WikiDataTimeInput
) -> WikiDataTimeOutput:
    input = TimeInput.model_validate(time, from_attributes=True)
    output = apps.history_app.create_time(time=input)
    return WikiDataTimeOutput.model_validate(output, from_attributes=True)


def get_tags_handler(apps: AppManager, wikidata_ids: list[str]) -> WikiDataTagsOutput:
    output = apps.history_app.get_tags_by_wikidata_ids(ids=wikidata_ids)
    return WikiDataTagsOutput(
        wikidata_ids=[
            WikiDataTagPointer(id=tag.id, wikidata_id=tag.wikidata_id) for tag in output
        ]
    )


def create_event_handler(
    apps: AppManager, event: WikiDataEventInput
) -> WikiDataEventOutput:
    id = apps.history_app.create_wikidata_event(
        text=event.summary,
        tags=event.tags,
        citation=event.citation,
        after=event.after,
    )
    return WikiDataEventOutput(id=id)
