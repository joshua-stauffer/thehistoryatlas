from fastapi import Depends, FastAPI, HTTPException, Path
from typing import Dict
from pydantic import BaseModel

from wikidata.repository import Repository, Config
from wikidata.wikidata_app import WikiDataApp

app = FastAPI(
    title="WikiData API", description="API for accessing WikiData information"
)


# Dependency for Config
def get_config() -> Config:
    return Config()


repository = Repository(config=Config())


# Dependency for Repository, which depends on Config
def get_repository(config: Config = Depends(get_config)) -> Repository:
    return repository


# Dependency for WikiDataApp, which depends on Repository
def get_wikidata_app(repository: Repository = Depends(get_repository)) -> WikiDataApp:
    return WikiDataApp(repository)


# Response models for better documentation
class LabelResponse(BaseModel):
    language: str
    value: str


class DescriptionResponse(BaseModel):
    language: str
    value: str


class EntityResponse(BaseModel):
    id: str
    labels: Dict[str, Dict[str, str]] = {}
    descriptions: Dict[str, Dict[str, str]] = {}
    # Additional fields would be defined here


@app.get("/v1/entities/items/{id}/labels/{language}", response_model=LabelResponse)
def get_label(
    id: str = Path(..., description="Entity ID"),
    language: str = Path(..., description="Language code"),
    wikidata_app: WikiDataApp = Depends(get_wikidata_app),
):
    """
    Get the label for an entity in the specified language.
    """
    try:
        label = wikidata_app.get_label(id, language)
        return {"language": language, "value": label}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/v1/entities/items/{id}/descriptions/{language}",
    response_model=DescriptionResponse,
)
def get_description(
    id: str = Path(..., description="Entity ID"),
    language: str = Path(..., description="Language code"),
    wikidata_app: WikiDataApp = Depends(get_wikidata_app),
):
    """
    Get the description for an entity in the specified language.
    """
    try:
        description = wikidata_app.get_description(id, language)
        return {"language": language, "value": description}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/v1/entities/items/{id}", response_model=EntityResponse)
def get_entity(
    id: str = Path(..., description="Entity ID"),
    wikidata_app: WikiDataApp = Depends(get_wikidata_app),
):
    """
    Get the full entity data.
    """
    try:
        entity = wikidata_app.get_entity(id)
        return entity
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8020)
