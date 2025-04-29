from fastapi import Depends, FastAPI, HTTPException, Path, Response
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


_repository: Repository | None = None


# Dependency for Repository, which depends on Config
def get_repository(config: Config = Depends(get_config)) -> Repository:
    global _repository
    if _repository is None:
        _repository = Repository(config=config)
    return _repository


# Dependency for WikiDataApp, which depends on Repository
def get_wikidata_app(repository: Repository = Depends(get_repository)) -> WikiDataApp:
    return WikiDataApp(repository)


class Property(BaseModel):
    language: str
    value: str


class WikiDataEntity(BaseModel):
    model_config = {"extra": "allow"}
    id: str
    pageid: int
    ns: int
    title: str
    lastrevid: int
    modified: str
    type: str
    labels: Dict[str, Property]
    descriptions: Dict[str, Property]
    aliases: Dict[str, list[Property]]
    claims: Dict[str, list[dict]]
    sitelinks: Dict[str, dict]


class EntityResponse(BaseModel):
    entities: dict[str, WikiDataEntity]


@app.get("/v1/entities/items/{id}/labels/{language}", response_model=str)
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
        return Response(content=label, media_type="text/plain")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/v1/entities/items/{id}/descriptions/{language}",
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
        return Response(content=description, media_type="text/plain")
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
        return EntityResponse(entities={id: entity})
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8020)
