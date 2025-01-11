from the_history_atlas.api.types.tags import WikiDataPersonInput, WikiDataPersonOutput
from the_history_atlas.apps.app_manager import AppManager
from the_history_atlas.apps.domain.core import PersonInput


def create_person(
    apps: AppManager, person: WikiDataPersonInput
) -> WikiDataPersonOutput:
    input = PersonInput.model_validate(person, from_attributes=True)
    output = apps.readmodel_app.create_person(person=input)
    return WikiDataPersonOutput.model_validate(output, from_attributes=True)
