from the_history_atlas.api.types.tags import (
    WikiDataPersonInput,
    WikiDataPersonOutput,
    WikiDataPlaceInput,
    WikiDataPlaceOutput,
    WikiDataTimeInput,
    WikiDataTimeOutput,
)
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.domain.core import PersonInput, PlaceInput, TimeInput


def create_person(
    apps: AppManager, person: WikiDataPersonInput
) -> WikiDataPersonOutput:
    input = PersonInput.model_validate(person, from_attributes=True)
    output = apps.readmodel_app.create_person(person=input)
    return WikiDataPersonOutput.model_validate(output, from_attributes=True)


def create_place(apps: AppManager, place: WikiDataPlaceInput) -> WikiDataPlaceOutput:
    input = PlaceInput.model_validate(place, from_attributes=True)
    output = apps.readmodel_app.create_place(place=input)
    return WikiDataPlaceOutput.model_validate(output, from_attributes=True)


def create_time(apps: AppManager, time: WikiDataTimeInput) -> WikiDataTimeOutput:
    input = TimeInput.model_validate(time, from_attributes=True)
    output = apps.readmodel_app.create_time(time=input)
    return WikiDataTimeOutput.model_validate(output, from_attributes=True)
