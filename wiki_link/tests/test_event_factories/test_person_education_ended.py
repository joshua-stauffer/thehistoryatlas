from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from wiki_service.event_factories.person_education_ended import PersonEducationEnded
from wiki_service.event_factories.event_factory import UnprocessableEventError
from wiki_service.event_factories.q_numbers import (
    EDUCATED_AT,
    END_TIME,
    ACADEMIC_DEGREE,
    DOCTORAL_ADVISOR,
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
        "Q789": "Doctor of Philosophy",
        "Q790": "Master of Science",
        "Q791": "Bachelor of Arts",
        "Q888": "Professor Einstein",
        "Q889": "Professor Bohr",
        "Q890": "Professor Planck",
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
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert not factory.entity_has_event()


def test_entity_has_event_no_end_time(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
            }
        ]
    }
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    assert not factory.entity_has_event()


def test_create_wiki_event_no_location(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
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
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
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
                    END_TIME: [
                        {
                            "property": END_TIME,
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
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary == "Test Person ended their studies at Test University in 1990."
    )
    assert len(event.people_tags) == 1
    assert event.people_tags[0].name == "Test Person"
    assert event.place_tag.name == "Test University"
    assert event.time_tag.time_definition.time == "+1990-01-01T00:00:00Z"


def test_create_wiki_event_with_degree(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                    ACADEMIC_DEGREE: [
                        {
                            "property": ACADEMIC_DEGREE,
                            "datavalue": {"value": {"id": "Q789"}},
                        }
                    ],
                },
            }
        ]
    }
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person graduated from Test University with a degree of Doctor of Philosophy in 1990."
    )


def test_create_wiki_event_with_multiple_degrees(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                    ACADEMIC_DEGREE: [
                        {
                            "property": ACADEMIC_DEGREE,
                            "datavalue": {"value": {"id": "Q790"}},
                        },
                        {
                            "property": ACADEMIC_DEGREE,
                            "datavalue": {"value": {"id": "Q791"}},
                        },
                    ],
                },
            }
        ]
    }
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person graduated from Test University with a degree of Master of Science and Bachelor of Arts in 1990."
    )


def test_create_wiki_event_with_advisor(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
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
                            "property": DOCTORAL_ADVISOR,
                            "datavalue": {"value": {"id": "Q888"}},
                        }
                    ],
                },
            }
        ]
    }
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person ended their studies at Test University, under the supervision of Professor Einstein in 1990."
    )
    assert len(event.people_tags) == 2
    assert event.people_tags[0].name == "Test Person"
    assert event.people_tags[1].name == "Professor Einstein"


def test_create_wiki_event_with_degree_and_advisor(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                    ACADEMIC_DEGREE: [
                        {
                            "property": ACADEMIC_DEGREE,
                            "datavalue": {"value": {"id": "Q789"}},
                        }
                    ],
                    DOCTORAL_ADVISOR: [
                        {
                            "property": DOCTORAL_ADVISOR,
                            "datavalue": {"value": {"id": "Q888"}},
                        }
                    ],
                },
            }
        ]
    }
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person graduated from Test University with a degree of Doctor of Philosophy, under the supervision of Professor Einstein in 1990."
    )
    assert len(event.people_tags) == 2
    assert event.people_tags[0].name == "Test Person"
    assert event.people_tags[1].name == "Professor Einstein"


def test_create_wiki_event_male_pronoun(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
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
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "Test Person ended his studies at Test University in 1990."


def test_create_wiki_event_female_pronoun(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
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
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert event.summary == "Test Person ended her studies at Test University in 1990."


def test_create_wiki_event_day_precision(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-06-15T00:00:00Z",
                                    "precision": 11,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "On June 15, 1990, Test Person ended their studies at Test University."
    )


def test_create_wiki_event_invalid_precision(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 8,  # Decade precision
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ]
                },
            }
        ]
    }
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    with pytest.raises(UnprocessableEventError) as exc_info:
        factory.create_wiki_event()
    assert "Unexpected time precision: 8" in str(exc_info.value)


def test_create_wiki_event_with_two_advisors(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
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
                            "property": DOCTORAL_ADVISOR,
                            "datavalue": {"value": {"id": "Q888"}},
                        },
                        {
                            "property": DOCTORAL_ADVISOR,
                            "datavalue": {"value": {"id": "Q889"}},
                        },
                    ],
                },
            }
        ]
    }
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person ended their studies at Test University, under the supervision of Professor Einstein and Professor Bohr in 1990."
    )
    assert len(event.people_tags) == 3
    assert event.people_tags[0].name == "Test Person"
    assert event.people_tags[1].name == "Professor Einstein"
    assert event.people_tags[2].name == "Professor Bohr"


def test_create_wiki_event_with_three_advisors(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
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
                            "property": DOCTORAL_ADVISOR,
                            "datavalue": {"value": {"id": "Q888"}},
                        },
                        {
                            "property": DOCTORAL_ADVISOR,
                            "datavalue": {"value": {"id": "Q889"}},
                        },
                        {
                            "property": DOCTORAL_ADVISOR,
                            "datavalue": {"value": {"id": "Q890"}},
                        },
                    ],
                },
            }
        ]
    }
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person ended their studies at Test University, under the supervision of Professor Einstein, Professor Bohr and Professor Planck in 1990."
    )
    assert len(event.people_tags) == 4
    assert event.people_tags[0].name == "Test Person"
    assert event.people_tags[1].name == "Professor Einstein"
    assert event.people_tags[2].name == "Professor Bohr"
    assert event.people_tags[3].name == "Professor Planck"


def test_create_wiki_event_with_multiple_advisors_and_degree(mock_entity, mock_query):
    mock_entity.claims = {
        EDUCATED_AT: [
            {
                "mainsnak": {
                    "datavalue": {"value": {"id": "Q456"}},
                },
                "qualifiers": {
                    END_TIME: [
                        {
                            "property": END_TIME,
                            "datavalue": {
                                "value": {
                                    "time": "+1990-01-01T00:00:00Z",
                                    "precision": 9,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                }
                            },
                        }
                    ],
                    ACADEMIC_DEGREE: [
                        {
                            "property": ACADEMIC_DEGREE,
                            "datavalue": {"value": {"id": "Q789"}},
                        }
                    ],
                    DOCTORAL_ADVISOR: [
                        {
                            "property": DOCTORAL_ADVISOR,
                            "datavalue": {"value": {"id": "Q888"}},
                        },
                        {
                            "property": DOCTORAL_ADVISOR,
                            "datavalue": {"value": {"id": "Q889"}},
                        },
                    ],
                },
            }
        ]
    }
    factory = PersonEducationEnded(entity=mock_entity, query=mock_query, entity_type="PERSON")
    events = factory.create_wiki_event()
    assert len(events) == 1
    event = events[0]
    assert (
        event.summary
        == "Test Person graduated from Test University with a degree of Doctor of Philosophy, under the supervision of Professor Einstein and Professor Bohr in 1990."
    )
    assert len(event.people_tags) == 3
    assert event.people_tags[0].name == "Test Person"
    assert event.people_tags[1].name == "Professor Einstein"
    assert event.people_tags[2].name == "Professor Bohr"
