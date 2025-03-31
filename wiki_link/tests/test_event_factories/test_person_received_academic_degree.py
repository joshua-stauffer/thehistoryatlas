from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from wiki_service.event_factories.person_received_academic_degree import (
    PersonReceivedAcademicDegree,
)
from wiki_service.event_factories.event_factory import UnprocessableEventError
from wiki_service.event_factories.q_numbers import (
    ACADEMIC_DEGREE,
    EDUCATED_AT,
    ACADEMIC_MAJOR,
    DOCTORAL_ADVISOR,
    SEX_OR_GENDER,
    MALE,
    FEMALE,
    ACADEMIC_MINOR,
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
        "Q792": "PhD",
        "Q793": "Master's degree",
        "Q794": "Bachelor's degree",
        "Q795": "Dr. Advisor",
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


def test_entity_has_event_no_academic_degree(mock_entity, mock_query):
    mock_entity.claims = {}
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    assert not factory.entity_has_event()


def test_create_wiki_event_no_location(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
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
            }
        ]
    }
    mock_query.get_geo_location.return_value = Mock(coordinates=None, geoshape=None)
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 0


def test_create_wiki_event_basic(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
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
            }
        ]
    }
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary == "Test Person received their PhD from Test University in 1990."
    )
    assert len(event.people_tags) == 1
    assert event.people_tags[0].name == "Test Person"
    assert event.place_tag.name == "Test University"
    assert event.time_tag.time_definition.time == "+1990-01-01T00:00:00Z"


def test_create_wiki_event_with_major(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
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
                            "datavalue": {"value": {"id": "Q789"}},  # Computer Science
                        }
                    ],
                },
            }
        ]
    }
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person received their PhD in Computer Science from Test University in 1990."
    )


def test_create_wiki_event_with_advisor(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                    DOCTORAL_ADVISOR: [
                        {
                            "datavalue": {"value": {"id": "Q795"}},  # Dr. Advisor
                        }
                    ],
                },
            }
        ]
    }
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person received their PhD from Test University, under the supervision of Dr. Advisor in 1990."
    )
    assert len(event.people_tags) == 2
    assert event.people_tags[0].name == "Test Person"
    assert event.people_tags[1].name == "Dr. Advisor"


def test_create_wiki_event_male_pronoun(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
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
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "Test Person received his PhD from Test University in 1990."


def test_create_wiki_event_female_pronoun(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
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
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "Test Person received her PhD from Test University in 1990."


def test_create_wiki_event_multiple_degrees(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
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
                    "datavalue": {"value": {"id": "Q793"}},  # Master's degree
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
                            "datavalue": {
                                "value": {
                                    "time": "+1988-01-01T00:00:00Z",
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
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 2
    assert (
        events[0].summary
        == "Test Person received their PhD from Test University in 1990."
    )
    assert (
        events[1].summary
        == "Test Person received their Master's degree from Test University in 1988."
    )


def test_create_wiki_event_invalid_precision(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
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
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    with pytest.raises(UnprocessableEventError):
        factory.create_wiki_event()


def test_create_wiki_event_with_multiple_majors(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
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
                            "datavalue": {"value": {"id": "Q789"}},  # Computer Science
                        },
                        {
                            "datavalue": {"value": {"id": "Q790"}},  # Mathematics
                        },
                    ],
                },
            }
        ]
    }
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person received their PhD in Computer Science and Mathematics from Test University in 1990."
    )


def test_create_wiki_event_with_minor(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                    ACADEMIC_MINOR: [
                        {
                            "datavalue": {"value": {"id": "Q789"}},  # Computer Science
                        }
                    ],
                },
            }
        ]
    }
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person received their PhD with a minor in Computer Science from Test University in 1990."
    )


def test_create_wiki_event_with_major_and_minor(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
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
                            "datavalue": {"value": {"id": "Q789"}},  # Computer Science
                        }
                    ],
                    ACADEMIC_MINOR: [
                        {
                            "datavalue": {"value": {"id": "Q790"}},  # Mathematics
                        }
                    ],
                },
            }
        ]
    }
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person received their PhD in Computer Science with a minor in Mathematics from Test University in 1990."
    )


def test_create_wiki_event_with_multiple_minors(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                    "P585": [  # point in time
                        {
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                    ACADEMIC_MINOR: [
                        {
                            "datavalue": {"value": {"id": "Q789"}},  # Computer Science
                        },
                        {
                            "datavalue": {"value": {"id": "Q790"}},  # Mathematics
                        },
                    ],
                },
            }
        ]
    }
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person received their PhD with a minor in Computer Science and Mathematics from Test University in 1990."
    )


def test_create_wiki_event_no_time(mock_entity, mock_query):
    mock_entity.claims = {
        ACADEMIC_DEGREE: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q792"}},  # PhD
                },
                "qualifiers": {
                    EDUCATED_AT: [
                        {
                            "datavalue": {"value": {"id": "Q456"}},
                        }
                    ],
                },
            }
        ]
    }
    factory = PersonReceivedAcademicDegree(
        entity=mock_entity, query=mock_query, entity_type="PERSON"
    )
    events = factory.create_wiki_event()
    assert len(events) == 0
