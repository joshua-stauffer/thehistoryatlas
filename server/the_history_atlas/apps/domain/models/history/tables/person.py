from typing import Literal
from uuid import UUID

from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class PersonModel(ConfiguredBaseModel):

    id: UUID
    type: Literal["PERSON"] = "PERSON"
