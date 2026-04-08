from uuid import UUID

from the_history_atlas.apps.domain.models.history.tables import NameModel

NAMES: list[NameModel] = [
    NameModel(
        id=UUID("640fe3e0-3728-4314-9dc9-2ef22a927457"),
        name="Johann Sebastian Bach",
    ),
    NameModel(id=UUID("0117b6da-f1c7-4082-9b99-e862c6361c08"), name="Eisenach"),
    NameModel(
        id=UUID("b58bbd41-871d-497d-a03e-306c9438d6e9"),
        name="the year 1685 on March 21",
    ),
]
