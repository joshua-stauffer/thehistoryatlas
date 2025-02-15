import pytest

from wiki_service.wikidata_query_service import (
    WikiDataQueryService,
    Entity,
    CoordinateLocation,
    GeoshapeLocation,
    TimeDefinition,
    Property,
)
from wiki_service.types import WikiDataItem


def test_query_person(config):
    EINSTEIN = "Q937"
    service = WikiDataQueryService(config)
    person = service.get_entity(id=EINSTEIN)
    for lang, prop in person.descriptions.items():
        assert isinstance(prop, Property)
    for lang, prop in person.labels.items():
        assert isinstance(prop, Property)
    for key, prop_list in person.aliases.items():
        assert all([isinstance(prop, Property) for prop in prop_list])

def test_query_entities(config):
    EINSTEIN = "Q937"
    BACH = "Q1339"
    service = WikiDataQueryService(config)
    entities = service.get_entities(ids=[EINSTEIN, BACH])
    assert len(entities) == 2
    for entity in entities:
        assert isinstance(entity, Entity)


def test_query_point(config):
    ROME_ID = "Q220"
    service = WikiDataQueryService(config)
    place = service.get_entity(id=ROME_ID)
    coords = service.get_coordinate_location(place)
    assert isinstance(place, Entity)
    assert isinstance(coords, CoordinateLocation)


def test_query_geoshape(config):
    ITALY_ID = "Q38"
    service = WikiDataQueryService(config)
    place = service.get_entity(id=ITALY_ID)
    geoshape = service.get_geoshape_location(place)
    assert isinstance(place, Entity)
    assert isinstance(geoshape, GeoshapeLocation)


def test_query_time(config):
    BACHS_BIRTHDAY = "Q69125225"
    service = WikiDataQueryService(config)
    time = service.get_entity(id=BACHS_BIRTHDAY)
    time_detail = service.get_time(entity=time)
    assert isinstance(time, Entity)
    assert isinstance(time_detail, TimeDefinition)


def test_make_sparql_query(config):
    service = WikiDataQueryService(config)
    url = "https://query.wikidata.org/sparql"
    query = """
    SELECT ?item
    WHERE 
    {
      ?item wdt:P31 wd:Q5 .
    }
    LIMIT 10
    """
    result = service.make_sparql_query(query=query, url=url)
    assert isinstance(result, dict)


def test_query(config):
    service = WikiDataQueryService(config)
    query = """
    SELECT 
          ?person ?personLabel ?personDescription 
          ?placeOfBirth ?placeOfBirthLabel ?lat ?lon ?geoShape 
          ?dobStatement ?dob ?precision ?calendarModel ?before ?after 
          ?father ?fatherLabel ?fatherDescription 
          ?mother ?motherLabel ?motherDescription
        WHERE {
          {
            # First, restrict to humans (Q5) with a date and place of birth.
            SELECT ?person ?dob ?placeOfBirth WHERE {
              ?person wdt:P31 wd:Q5;
                      wdt:P569 ?dob;
                      wdt:P19 ?placeOfBirth.
            }
            LIMIT 100
            OFFSET 0
          }
          
          # Retrieve the full date-of-birth statement so that we can extract qualifiers.
          OPTIONAL {
            ?person p:P569 ?dobStatement.
            ?dobStatement ps:P569 ?dob.
            OPTIONAL { ?dobStatement wikibase:timePrecision ?precision. }
            OPTIONAL { ?dobStatement wikibase:calendarmodel ?calendarModel. }
            OPTIONAL { ?dobStatement wikibase:beforeTolerance ?before. }
            OPTIONAL { ?dobStatement wikibase:afterTolerance ?after. }
          }
          
          # For the place of birth, retrieve coordinates using the simpler truthy property.
          OPTIONAL {
            ?placeOfBirth wdt:P625 ?coordinate.
            BIND(geof:latitude(?coordinate) AS ?lat)
            BIND(geof:longitude(?coordinate) AS ?lon)
          }
          
          # Retrieve the geoshape if available.
          OPTIONAL { ?placeOfBirth wdt:P3896 ?geoShape. }
          
          # Optionally retrieve father and mother.
          OPTIONAL { ?person wdt:P22 ?father. }
          OPTIONAL { ?person wdt:P25 ?mother. }
          
          # Get English labels and descriptions.
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
    """
    url = "https://query.wikidata.org/sparql"
    result = service.make_sparql_query(query=query, url=url)
    assert len(result["bindings"]) == 100


def test_get_qid_from_uri(config):
    service = WikiDataQueryService(config)
    uri = "http://www.wikidata.org/entity/Q23"

    res = service.get_qid_from_uri(uri)
    assert res == "Q23"


def test_find_people(config):
    service = WikiDataQueryService(config)
    people = service.find_people(limit=100, offset=0)
    assert len(people) == 100
    for person in people:
        assert isinstance(person, WikiDataItem)


def test_get_wikidata_people_count(config):
    service = WikiDataQueryService(config=config)

    count = service.get_wikidata_people_count()
    assert isinstance(count, int)
    assert count > 11_000_000
