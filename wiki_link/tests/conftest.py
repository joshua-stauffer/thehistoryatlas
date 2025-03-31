import json
import os
import pathlib

import pytest

from wiki_service.config import WikiServiceConfig
from wiki_service.event_factories.event_factory import Query
from wiki_service.event_factories.q_numbers import (
    DATE_OF_BIRTH,
    DATE_OF_DEATH,
    INCEPTION,
    CREATOR,
    LOCATION_OF_CREATION,
    COUNTRY_OF_ORIGIN,
    COMMISSIONED_BY,
)
from wiki_service.wikidata_query_service import (
    WikiDataQueryService,
    Entity,
    GeoLocation,
    CoordinateLocation,
)


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
    with open(root_dir / "data/einstein_place_of_birth_query.json", "r") as f:
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


@pytest.fixture
def eisenach_geo_location() -> GeoLocation:
    return GeoLocation(
        coordinates=CoordinateLocation(
            altitude=None,
            globe="http://www.wikidata.org/entity/Q2",
            hash="4c6b99762b7b08050e9500910d4cdfb87df55a2f",
            id="q7070$C57E3018-C5AF-41F9-B6B1-630539705B9F",
            latitude=50.974722222222,
            longitude=10.324444444444,
            precision=0.00027777777777778,
            property="P625",
            rank="normal",
            snaktype="value",
            type="statement",
        ),
        geoshape=None,
    )


@pytest.fixture
def leipzig_geo_location() -> GeoLocation:
    return GeoLocation(
        coordinates=CoordinateLocation(
            id="Q1022$COORDINATE_ID",
            rank="normal",
            type="statement",
            snaktype="value",
            property="P625",
            hash="some_hash",
            latitude=51.3397,
            longitude=12.3731,
            altitude=None,
            precision=0.0001,
            globe="http://www.wikidata.org/entity/Q2",
        ),
        geoshape=None,
    )


@pytest.fixture
def bach_entity_death_precision_10(bach_json_result) -> Entity:
    entity = WikiDataQueryService.build_entity(bach_json_result["entities"]["Q1339"])
    time_claim = next(
        claim
        for claim in entity.claims[DATE_OF_DEATH]
        if claim["mainsnak"]["property"] == DATE_OF_DEATH
    )
    time_claim["mainsnak"]["datavalue"]["value"]["precision"] = 10
    return entity


@pytest.fixture
def bach_entity_death_precision_9(bach_json_result) -> Entity:
    entity = WikiDataQueryService.build_entity(bach_json_result["entities"]["Q1339"])
    time_claim = next(
        claim
        for claim in entity.claims[DATE_OF_DEATH]
        if claim["mainsnak"]["property"] == DATE_OF_DEATH
    )
    time_claim["mainsnak"]["datavalue"]["value"]["precision"] = 9
    return entity


@pytest.fixture
def einstein_place_of_death_json_result(root_dir):
    with open(root_dir / "data/einstein_place_of_death_query.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
def einstein_place_of_death(einstein_place_of_death_json_result) -> Entity:
    return WikiDataQueryService.build_entity(
        einstein_place_of_death_json_result["entities"]["Q1345"]
    )


@pytest.fixture
def mona_lisa_json_result(root_dir):
    with open(root_dir / "data/mona_lisa_query.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
def mona_lisa_entity(mona_lisa_json_result) -> Entity:
    return WikiDataQueryService.build_entity(
        mona_lisa_json_result["entities"]["Q12418"]
    )


@pytest.fixture
def mona_lisa_entity_precision_10(mona_lisa_json_result) -> Entity:
    entity = WikiDataQueryService.build_entity(
        mona_lisa_json_result["entities"]["Q12418"]
    )
    time_claim = next(
        claim
        for claim in entity.claims[INCEPTION]
        if claim["mainsnak"]["property"] == INCEPTION
    )
    time_claim["mainsnak"]["datavalue"]["value"]["precision"] = 10
    return entity


@pytest.fixture
def mona_lisa_entity_precision_9(mona_lisa_json_result) -> Entity:
    entity = WikiDataQueryService.build_entity(
        mona_lisa_json_result["entities"]["Q12418"]
    )
    time_claim = next(
        claim
        for claim in entity.claims[INCEPTION]
        if claim["mainsnak"]["property"] == INCEPTION
    )
    time_claim["mainsnak"]["datavalue"]["value"]["precision"] = 9
    return entity


@pytest.fixture
def mona_lisa_entity_no_commissioner(mona_lisa_json_result) -> Entity:
    entity = WikiDataQueryService.build_entity(
        mona_lisa_json_result["entities"]["Q12418"]
    )
    entity.claims.pop(COMMISSIONED_BY, None)
    return entity


@pytest.fixture
def mona_lisa_entity_multiple_commissioners(mona_lisa_json_result) -> Entity:
    entity = WikiDataQueryService.build_entity(
        mona_lisa_json_result["entities"]["Q12418"]
    )
    # Add a second commissioner
    entity.claims[COMMISSIONED_BY].append(
        {
            "mainsnak": {
                "snaktype": "value",
                "property": COMMISSIONED_BY,
                "datavalue": {"value": {"id": "Q123456"}, "type": "wikibase-entityid"},
            }
        }
    )
    return entity


@pytest.fixture
def mona_lisa_entity_country_only(mona_lisa_json_result) -> Entity:
    entity = WikiDataQueryService.build_entity(
        mona_lisa_json_result["entities"]["Q12418"]
    )
    entity.claims.pop(LOCATION_OF_CREATION, None)
    entity.claims.pop(COMMISSIONED_BY, None)
    entity.claims[COUNTRY_OF_ORIGIN] = [
        {
            "mainsnak": {
                "snaktype": "value",
                "property": COUNTRY_OF_ORIGIN,
                "datavalue": {"value": {"id": "Q142"}, "type": "wikibase-entityid"},
            }
        }
    ]
    return entity


@pytest.fixture
def paris_geo_location() -> GeoLocation:
    return GeoLocation(
        coordinates=CoordinateLocation(
            id="Q90$COORDINATE_ID",
            rank="normal",
            type="statement",
            snaktype="value",
            property="P625",
            hash="some_hash",
            latitude=48.8566,
            longitude=2.3522,
            altitude=None,
            precision=0.0001,
            globe="http://www.wikidata.org/entity/Q2",
        ),
        geoshape=None,
    )


@pytest.fixture
def france_geo_location() -> GeoLocation:
    return GeoLocation(
        coordinates=CoordinateLocation(
            id="Q142$COORDINATE_ID",
            rank="normal",
            type="statement",
            snaktype="value",
            property="P625",
            hash="some_hash",
            latitude=46.2276,
            longitude=2.2137,
            altitude=None,
            precision=0.0001,
            globe="http://www.wikidata.org/entity/Q2",
        ),
        geoshape=None,
    )


@pytest.fixture
def starry_night_json_result(root_dir):
    with open(root_dir / "data/starry_night_query.json", "r") as f:
        return json.loads(f.read())


@pytest.fixture
def starry_night_entity(starry_night_json_result) -> Entity:
    return WikiDataQueryService.build_entity(
        starry_night_json_result["entities"]["Q45585"]
    )


class MockQuery:
    def __init__(
        self,
        entity_lookup: dict[str, str],
        geo_location: GeoLocation,
        expected_geo_location_id: str,
    ):
        self.entity_lookup = entity_lookup
        self.geo_location = geo_location
        self.expected_geo_location_id = expected_geo_location_id

    def get_label(self, id: str, language: str):
        assert id in self.entity_lookup
        return self.entity_lookup[id]

    def get_geo_location(self, id: str):
        assert id == self.expected_geo_location_id
        return self.geo_location
