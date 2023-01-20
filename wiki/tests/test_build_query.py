from wiki_service.entity_builder import (
    WikiDataQueryService,
    Entity,
    CoordinateLocation,
    GeoshapeLocation,
    TimeDefinition,
    Property,
)


def test_query_person():
    EINSTEIN = "Q937"
    service = WikiDataQueryService()
    person = service.get_entity(id=EINSTEIN)
    for lang, prop in person.descriptions.items():
        assert isinstance(prop, Property)
    for lang, prop in person.labels.items():
        assert isinstance(prop, Property)
    for key, prop_list in person.aliases.items():
        assert all([isinstance(prop, Property) for prop in prop_list])


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
