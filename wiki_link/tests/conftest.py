import json
import os
import pathlib

import pytest

from wiki_service.config import WikiServiceConfig
from wiki_service.event_factories.q_numbers import DATE_OF_BIRTH
from wiki_service.wikidata_query_service import WikiDataQueryService, Entity


@pytest.fixture
def config():
    test_db_uri = os.environ.get("TEST_DB_URI", None)
    if test_db_uri is None:
        raise Exception("Env var TEST_DB_URI is required to run database tests.")
    config = WikiServiceConfig()
    config.DB_URI = test_db_uri
    return config


@pytest.fixture
def root_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent


@pytest.fixture
def einstein_json_result(root_dir):
    with open(root_dir / "data/einstein_query.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
def einstein_entity(einstein_json_result) -> Entity:
    return WikiDataQueryService.build_entity(einstein_json_result["entities"]["Q937"])


@pytest.fixture
def einstein_place_of_birth_json_result(root_dir):
    with open(root_dir / "data/einstein_place_of_birtH_query.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
def einstein_place_of_birth(einstein_place_of_birth_json_result) -> Entity:
    return WikiDataQueryService.build_entity(
        einstein_place_of_birth_json_result["entities"]["Q3012"]
    )


@pytest.fixture
def bach_json_result(root_dir):
    with open(root_dir / "data/bach_query.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
def bach_entity(bach_json_result) -> Entity:
    return WikiDataQueryService.build_entity(bach_json_result["entities"]["Q1339"])


@pytest.fixture
def bach_entity_precision_10(bach_json_result) -> Entity:
    entity = WikiDataQueryService.build_entity(bach_json_result["entities"]["Q1339"])
    time_claim = next(
        claim
        for claim in entity.claims[DATE_OF_BIRTH]
        if claim["mainsnak"]["property"] == DATE_OF_BIRTH
    )
    time_claim["mainsnak"]["datavalue"]["value"]["precision"] = 10
    return entity


@pytest.fixture
def bach_entity_precision_9(bach_json_result) -> Entity:
    entity = WikiDataQueryService.build_entity(bach_json_result["entities"]["Q1339"])
    time_claim = next(
        claim
        for claim in entity.claims[DATE_OF_BIRTH]
        if claim["mainsnak"]["property"] == DATE_OF_BIRTH
    )
    time_claim["mainsnak"]["datavalue"]["value"]["precision"] = 9
    return entity


@pytest.fixture
def bach_place_of_birth(root_dir):
    with open(root_dir / "data/bach_place_of_birth_query.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
def eisenach_entity(bach_place_of_birth) -> Entity:
    return WikiDataQueryService.build_entity(bach_place_of_birth["entities"]["Q7070"])
