from the_history_atlas.apps.domain.models.base_model import ConfiguredBaseModel


class Credentials(ConfiguredBaseModel):
    username: str
    password: str
