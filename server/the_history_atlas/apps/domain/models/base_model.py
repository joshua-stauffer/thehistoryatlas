from pydantic import BaseModel


class ConfiguredBaseModel(BaseModel):
    extra = "forbid"
