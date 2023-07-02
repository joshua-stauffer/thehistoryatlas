import logging

import random
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from the_history_atlas.apps.domain.models.readmodel import (
    DefaultEntity,
    Source as ADMSource,
)
from the_history_atlas.apps.readmodel.schema import Citation
from the_history_atlas.apps.readmodel.schema import TagInstance
from the_history_atlas.apps.readmodel.schema import Time
from the_history_atlas.apps.readmodel.schema import Person
from the_history_atlas.apps.readmodel.schema import Place
from the_history_atlas.apps.readmodel.schema import Summary
from the_history_atlas.apps.readmodel.trie import Trie

log = logging.getLogger(__name__)
log.setLevel("DEBUG")

# constants
TYPE_ENUM = set(["PERSON", "PLACE", "TIME"])
DB_COUNT = 100
FUZZ_ITERATIONS = 10


def load_db(db_tuple):
    db, db_dict = db_tuple
    assert db != None


def test_get_citation_returns_error_with_unknown_guid(db_tuple):
    db, db_dict = db_tuple
    guid = "this string isnt a guid"
    res = db.get_citation(guid)
    assert isinstance(res, dict)
    assert len(res.keys()) == 0


def test_get_summaries_returns_error_with_unknown_guid(db_tuple):
    db, db_dict = db_tuple
    guid = "this string isnt a guid"
    res = db.get_summaries([guid])
    assert len(res) == 0


def test_get_manifest_by_person_returns_empty_list(db_tuple):
    db, db_dict = db_tuple
    tags, timelines = db.get_manifest_by_person("Definitely Not a Person")
    assert isinstance(timelines, list)
    assert len(timelines) == 0
    assert isinstance(tags, list)
    assert len(tags) == 0


# test successful queries


def test_get_summary_fuzz_test(db_tuple):
    db, db_dict = db_tuple
    summary_guids = db_dict["summary_guids"]
    # ensure that there are no duplicates in summary_guids
    test = set(summary_guids)
    assert len(test) == len(summary_guids)
    # fuzz
    # NOTE: this slows down the test considerably at higher iterations
    for _ in range(FUZZ_ITERATIONS):
        c = summary_guids[:]
        guids = list()
        log.info(f"Loop {_}")
        # draw guids to get
        count = random.randint(1, DB_COUNT)
        for _ in range(count):
            guids.append(c.pop(random.randint(0, len(c) - 1)))
        log.info(f"Count: {count}")
        log.info(f"GUIDs head: {guids[:10]}")
        res = db.get_summaries(guids)
        assert isinstance(res, list)
        assert len(res) == len(guids)
        for summary in res:
            assert summary["guid"] in guids
            # describe the shape of expected properties
            assert isinstance(summary, dict)
            assert summary["text"] != None
            assert isinstance(summary["text"], str)
            assert isinstance(summary["tags"], list)
            for t in summary["tags"]:
                assert isinstance(t, dict)
                assert isinstance(t["start_char"], int)
                assert isinstance(t["stop_char"], int)
                assert t["tag_type"] in TYPE_ENUM
                if t["tag_type"] == "TIME":
                    assert isinstance(t["name"], str)
                elif t["tag_type"] == "PERSON":
                    assert isinstance(t["names"], list)
                else:
                    assert isinstance(t["names"], list)
                    assert isinstance(t["coords"], dict)
                    assert isinstance(t["coords"]["longitude"], float)
                    assert isinstance(t["coords"]["latitude"], float)
                    if g := t["coords"].get("geoshape"):
                        assert isinstance(g, str)


def test_get_manifest_by_person(db_tuple):
    db, db_dict = db_tuple
    person_guids = db_dict["person_guids"]
    for guid in person_guids:
        manifest_res, timeline_res = db.get_manifest_by_person(guid)
        assert isinstance(manifest_res, list)
        assert all(isinstance(e, str) for e in manifest_res)
        assert len(manifest_res) > 0
        assert isinstance(timeline_res, list)
        for res in timeline_res:
            assert isinstance(res, dict)
            assert isinstance(res["count"], int)
            assert isinstance(res["root_id"], str)
            assert isinstance(res["year"], int)


def test_get_manifest_by_place(db_tuple):
    db, db_dict = db_tuple
    place_guids = db_dict["place_guids"]
    for guid in place_guids:
        manifest_res, timeline_res = db.get_manifest_by_place(guid)
        assert isinstance(manifest_res, list)
        assert all(isinstance(e, str) for e in manifest_res)
        assert len(manifest_res) > 0
        assert isinstance(timeline_res, list)
        for res in timeline_res:
            assert isinstance(res, dict)
            assert isinstance(res["count"], int)
            assert isinstance(res["root_id"], str)
            assert isinstance(res["year"], int)


def test_get_manifest_by_time(db_tuple):
    db, db_dict = db_tuple
    time_guids = db_dict["time_guids"]
    for guid in time_guids:
        manifest_res, timeline_res = db.get_manifest_by_time(guid)
        assert isinstance(manifest_res, list)
        assert all(isinstance(e, str) for e in manifest_res)
        assert len(manifest_res) > 0
        assert isinstance(timeline_res, list)
        for res in timeline_res:
            assert isinstance(res, dict)
            assert isinstance(res["count"], int)
            assert isinstance(res["root_id"], str)
            assert isinstance(res["year"], int)


def test_get_guids_by_name(db_tuple):
    db, db_dict = db_tuple
    names = db_dict["names"]
    guids = [*db_dict["person_guids"], *db_dict["place_guids"], *db_dict["time_guids"]]
    for name in names:
        res = db.get_guids_by_name(name)
        assert len(res) == 1


def test_get_guids_by_name_returns_empty(db_tuple):
    db, db_dict = db_tuple
    res = db.get_guids_by_name("This name doesnt exist")
    assert isinstance(res, list)
    assert len(res) == 0


def test_tag_instances(db_tuple, engine):
    db, db_dict = db_tuple
    with Session(engine, future=True) as session:
        res = session.execute(select(TagInstance)).scalars()
        count = [1 for _ in res]
        assert len(count) == 300


def test_get_entity_summary_by_guid_batch_returns_empty(db_tuple):
    db, db_dict = db_tuple
    res = db.get_entity_summary_by_guid_batch([])
    assert isinstance(res, list)
    assert len(res) == 0


def test_get_entity_summary_by_guid_batch(db_tuple):
    db, db_dict = db_tuple
    time_guids = db_dict["time_guids"][:10]
    place_guids = db_dict["place_guids"][:10]
    person_guids = db_dict["person_guids"][:10]
    combined_guids = [*time_guids, *place_guids, *person_guids]
    assert len(combined_guids) == 30
    res = db.get_entity_summary_by_guid_batch(combined_guids)
    assert isinstance(res, list)
    assert len(res) == 30
    for summary in res:
        assert isinstance(summary, dict)
        guid = summary["id"]
        assert isinstance(guid, str)
        if summary["type"] == "TIME":
            assert guid in time_guids
        elif summary["type"] == "PLACE":
            assert guid in place_guids
        elif summary["type"] == "PERSON":
            assert guid in person_guids
        else:
            assert False  # Summary type had an unexpected value
        assert summary["citation_count"] > 0
        assert isinstance(summary["names"], list)
        for name in summary["names"]:
            assert isinstance(name, str)
        assert isinstance(summary["first_citation_date"], str)
        assert isinstance(summary["last_citation_date"], str)
        assert summary["first_citation_date"] <= summary["last_citation_date"]


def test_get_all_entity_names(db_tuple):
    db, _ = db_tuple
    res = db.get_all_entity_names()
    assert len(res) > 0
    assert isinstance(res, list)
    for tup in res:
        assert isinstance(tup, tuple)
        name, guid = tup
        assert isinstance(name, str)
        assert isinstance(guid, str)
        assert UUID(guid)


def test_get_name_by_fuzzy_search(db_tuple):
    db, _ = db_tuple
    res1 = db.get_name_by_fuzzy_search("A person name")
    assert isinstance(res1, list)
    assert len(res1) <= 10


def test_get_sources_by_search_term_title(db_tuple, source_title):
    db, _ = db_tuple

    # ensure data is fresh
    db._source_trie = Trie(db.get_all_source_titles_and_authors())

    sources = db.get_sources_by_search_term(source_title)
    assert isinstance(sources, list)
    assert len(sources) == 10
    for source in sources:
        assert isinstance(source, ADMSource)
        assert isinstance(source.id, str)
        assert isinstance(source.title, str)
        assert isinstance(source.publisher, str)
        assert isinstance(source.author, str)
        assert isinstance(source.pub_date, str)


def test_get_place_by_coords(db_tuple, engine):
    """Cover successful path - coordinates are found"""
    db, db_dict = db_tuple
    # find a set of coordinates to query
    place_guid = db_dict["place_guids"][0]
    with Session(engine, future=True) as session:
        res = session.execute(
            select(Place).where(Place.guid == place_guid)
        ).scalar_one()
        latitude = res.latitude
        longitude = res.longitude

    guid = db.get_place_by_coords(latitude=latitude, longitude=longitude)
    assert guid == place_guid


def test_get_place_by_coords_with_new_coords(db_tuple):
    """Cover failed path -- no coordinates are found"""
    db, _ = db_tuple
    # coords are set by random.random(), which is less than one.
    latitude = 1 + random.random()
    longitude = 1 - random.random()

    guid = db.get_place_by_coords(latitude=latitude, longitude=longitude)
    assert guid == None


def test_get_default_entity(db_tuple):
    db, _ = db_tuple
    entity = db.get_default_entity()
    assert isinstance(entity, DefaultEntity)
