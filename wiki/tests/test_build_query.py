from wiki_service.entity_builder import (
    WikiDataQueryService,
    Entity,
    CoordinateLocation,
    GeoshapeLocation, TimeDefinition,
)


def test_search():
    person = WikiDataQueryService().get_entity(id="Q937")


def test_query_place():
    ROME_ID = "Q220"
    service = WikiDataQueryService()
    place = service.get_entity(id=ROME_ID)
    coords = service.get_coordinate_location(place)
    assert isinstance(place, Entity)
    assert isinstance(coords, CoordinateLocation)


def test_query_italy():
    ITALY_ID = "Q38"
    service = WikiDataQueryService()
    place = service.get_entity(id=ITALY_ID)
    geoshape = service.get_geoshape_location(place)
    assert isinstance(place, Entity)
    assert isinstance(geoshape, GeoshapeLocation)


def test_query_time():
    BACHS_BIRTHDAY = "Q69125225"
    service = WikiDataQueryService()
    time = service.get_entity(id=BACHS_BIRTHDAY)
    time_detail = service.get_time(entity=time)
    assert isinstance(time, Entity)
    assert isinstance(time_detail, TimeDefinition)
