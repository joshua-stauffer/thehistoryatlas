from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from wiki_service.event_factories.person_education_began import PersonEducationBegan
from wiki_service.event_factories.event_factory import UnprocessableEventError
from wiki_service.event_factories.q_numbers import (
    EDUCATED_AT,
    START_TIME,
    ACADEMIC_MAJOR,
    SEX_OR_GENDER,
    MALE,
    FEMALE,
)
from wiki_service.wikidata_query_service import GeoLocation, CoordinateLocation


@pytest.fixture
def mock_entity():
    entity = Mock()
    entity.id = "Q123"
    entity.labels = {"en": Mock(value="Test Person")}
    return entity


@pytest.fixture
def mock_query():
    query = Mock()
    query.get_label.side_effect = lambda id, language: {
        "Q456": "Test University",
        "Q789": "Computer Science",
        "Q790": "Mathematics",
        "Q791": "Physics",
    }.get(id, "Unknown")

    # Create a proper GeoLocation instance
    coordinates = CoordinateLocation(
        id="",
        type="statement",
        rank="normal",
        hash="",
        snaktype="value",
        property="P625",
        latitude=0,
        longitude=0,
        altitude=None,
        precision=0.0001,
        globe="http://www.wikidata.org/entity/Q2",
    )
    geo_location = GeoLocation(coordinates=coordinates, geoshape=None)
    query.get_geo_location.return_value = geo_location
    return query


def test_entity_has_event_no_educated_at(mock_entity, mock_query):
    mock_entity.claims = {}
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert not factory.entity_has_event()


def test_entity_has_event_no_start_time(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
            }
        ]
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert not factory.entity_has_event()


def test_entity_has_event_with_start_time(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert factory.entity_has_event()


def test_create_wiki_event_no_location(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    mock_query.get_geo_location.return_value = Mock(coordinates=None, geoshape=None)
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 0


def test_create_wiki_event_basic(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary == "Test Person began their studies at Test University in 1990."
    )
    assert len(event.people_tags) == 1
    assert event.people_tags[0].name == "Test Person"
    assert event.place_tag.name == "Test University"
    assert event.time_tag.time_definition.time == "+1990-01-01T00:00:00Z"


def test_create_wiki_event_with_major(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                    ACADEMIC_MAJOR: [
                        {
                            "property": ACADEMIC_MAJOR,
                            "datavalue": {"value": {"id": "Q789"}},
                        }
                    ],
                },
            }
        ]
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person began their studies in Computer Science at Test University in 1990."
    )


def test_create_wiki_event_male_pronoun(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ]
                },
            }
        ],
        SEX_OR_GENDER: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": MALE}},
                },
            }
        ],
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "Test Person began his studies at Test University in 1990."


def test_create_wiki_event_female_pronoun(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ]
                },
            }
        ],
        SEX_OR_GENDER: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": FEMALE}},
                },
            }
        ],
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "Test Person began her studies at Test University in 1990."


def test_create_wiki_event_unknown_gender_pronoun(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ]
                },
            }
        ],
        SEX_OR_GENDER: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q123"}},  # Unknown gender
                },
            }
        ],
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary == "Test Person began their studies at Test University in 1990."
    )


def test_create_wiki_event_multiple_schools(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                },
            },
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q457"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1995-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                },
            },
        ]
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 2
    assert (
        events[0].summary
        == "Test Person began their studies at Test University in 1990."
    )
    assert events[1].summary == "Test Person began their studies at Unknown in 1995."


def test_create_wiki_event_invalid_precision(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 8,  # Invalid precision
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                },
            }
        ]
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    with pytest.raises(UnprocessableEventError, match="Unexpected time precision: 8"):
        factory.create_wiki_event()


def test_create_wiki_event_with_two_majors(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                    ACADEMIC_MAJOR: [
                        {
                            "property": ACADEMIC_MAJOR,
                            "datavalue": {"value": {"id": "Q789"}},
                        },
                        {
                            "property": ACADEMIC_MAJOR,
                            "datavalue": {"value": {"id": "Q790"}},
                        },
                    ],
                },
            }
        ]
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person began their studies in Computer Science and Mathematics at Test University in 1990."
    )


def test_create_wiki_event_with_three_majors(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    START_TIME: [
                        {
                            "property": START_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                    ACADEMIC_MAJOR: [
                        {
                            "property": ACADEMIC_MAJOR,
                            "datavalue": {"value": {"id": "Q789"}},
                        },
                        {
                            "property": ACADEMIC_MAJOR,
                            "datavalue": {"value": {"id": "Q790"}},
                        },
                        {
                            "property": ACADEMIC_MAJOR,
                            "datavalue": {"value": {"id": "Q791"}},
                        },
                    ],
                },
            }
        ]
    }
    factory = PersonEducationBegan(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person began their studies in Computer Science, Mathematics and Physics at Test University in 1990."
    )
