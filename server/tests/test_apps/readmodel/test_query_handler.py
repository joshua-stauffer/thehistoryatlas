import random

from the_history_atlas.apps.domain.models.readmodel.queries import (
    GetCitationByID,
    GetManifest,
    Manifest,
    GetEntitySummariesByName,
    EntitySummariesByName,
    GetFuzzySearchByName,
    GetEntitySummariesByIDs,
    GetPlaceByCoords,
    PlaceByCoords,
    Citation,
)

from the_history_atlas.apps.readmodel.schema import (
    Place,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

# constants
TYPE_ENUM = set(["PERSON", "PLACE", "TIME"])
DB_COUNT = 100
FUZZ_ITERATIONS = 10


def test_get_citation_by_guid(query_handler, db_tuple):
    _, db_dict = db_tuple
    citation_id = db_dict["citation_guids"][1]
    citation = query_handler.get_citation_by_id(
        query=GetCitationByID(citation_id=citation_id)
    )

    assert isinstance(citation, Citation)


def test_get_manifest_person(query_handler, db_tuple):
    _, db_dict = db_tuple
    guid = db_dict["person_guids"][0]
    manifest = query_handler.get_manifest(
        query=GetManifest(entity_type="PERSON", id=guid)
    )
    assert isinstance(manifest, Manifest)


def test_get_manifest_place(query_handler, db_tuple):
    _, db_dict = db_tuple
    guid = db_dict["place_guids"][0]
    manifest = query_handler.get_manifest(
        query=GetManifest(entity_type="PERSON", id=guid)
    )
    assert isinstance(manifest, Manifest)


def test_get_manifest_time(query_handler, db_tuple):
    _, db_dict = db_tuple
    guid = db_dict["time_guids"][0]
    manifest = query_handler.get_manifest(
        query=GetManifest(entity_type="PERSON", id=guid)
    )
    assert isinstance(manifest, Manifest)


def test_get_guids_by_name(query_handler, db_tuple):
    _, db_dict = db_tuple
    name = db_dict["names"][0]
    entity_summaries_by_name = query_handler.get_entity_summaries_by_name(
        query=GetEntitySummariesByName(name=name)
    )
    assert isinstance(entity_summaries_by_name, EntitySummariesByName)


def test_get_fuzzy_search_by_name(query_handler):

    fuzzy_search_by_name = query_handler.get_fuzzy_search_by_name(
        query=GetFuzzySearchByName(name="a")
    )
    assert isinstance(fuzzy_search_by_name, list)


def test_get_entity_summaries_by_guid_handles_empty_list(query_handler):

    entity_summaries_by_id = query_handler.get_entity_summaries_by_ids(
        query=GetEntitySummariesByIDs(ids=[])
    )
    assert isinstance(entity_summaries_by_id, list)


def test_get_entity_summaries_by_guid_with_invalid_guids(query_handler):
    wrong_ids = [
        "c0c0ba02-b43b-4733-ac09-f35bd06b123f",
        "ee9b40e5-7066-4be6-ac6b-970b79035a22",
        "fbbee7e9-eaa8-4d15-bc0d-46a1ef459343",
    ]

    entity_summaries_by_id = query_handler.get_entity_summaries_by_ids(
        query=GetEntitySummariesByIDs(ids=wrong_ids)
    )
    assert entity_summaries_by_id == []


def test_get_entity_summaries(query_handler, db_tuple):
    _, db_dict = db_tuple

    ids = db_dict["place_guids"][20:25]
    ids.extend(db_dict["time_guids"][20:25])
    ids.extend(db_dict["person_guids"][20:25])

    entity_summaries_by_id = query_handler.get_entity_summaries_by_ids(
        query=GetEntitySummariesByIDs(ids=ids)
    )

    assert len(entity_summaries_by_id) == 15


def test_get_place_by_coords_success(query_handler, db_tuple):
    db, db_dict = db_tuple
    # find a set of coordinates to query
    place_id = db_dict["place_guids"][0]
    with Session(db._engine, future=True) as session:
        res = session.execute(select(Place).where(Place.guid == place_id)).scalar_one()
        latitude = res.latitude
        longitude = res.longitude

    place_by_coords = query_handler.get_place_by_coords(
        query=GetPlaceByCoords(latitude=latitude, longitude=longitude)
    )

    assert isinstance(place_by_coords, PlaceByCoords)
    assert place_by_coords.longitude == longitude
    assert place_by_coords.latitude == latitude
    assert place_by_coords.id == place_id


def test_get_place_by_coords_failure(query_handler, db_tuple):
    latitude = 1 + random.random()
    longitude = 1 - random.random()

    place_by_coords = query_handler.get_place_by_coords(
        query=GetPlaceByCoords(latitude=latitude, longitude=longitude)
    )

    assert isinstance(place_by_coords, PlaceByCoords)
    assert place_by_coords.longitude == longitude
    assert place_by_coords.latitude == latitude
    assert place_by_coords.id is None
