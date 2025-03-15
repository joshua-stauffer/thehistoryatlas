from dataclasses import asdict, dataclass
from unittest.mock import Mock, AsyncMock, patch, ANY
from uuid import uuid4
from datetime import datetime, timezone

import pytest

from wiki_service.database import Database, Item
from wiki_service.types import WikiDataItem
from wiki_service.wiki_service import WikiService
from wiki_service.wikidata_query_service import (
    WikiDataQueryService,
    Entity,
    Property,
    WikiDataQueryServiceError,
    CoordinateLocation,
    TimeDefinition,
    GeoLocation,
)
from wiki_service.config import WikiServiceConfig
from wiki_service.event_factories.event_factory import EventFactory
from wiki_service.rest_client import RestClient, RestClientError


@dataclass
class MockWikiServiceConfig:
    WIKIDATA_SEARCH_LIMIT: int


@pytest.fixture
def item():
    return Item(
        wiki_id="Q110003",
        wiki_type="WIKIDATA",
        wiki_link="http://www.wikidata.org/entity/Q110003",
        entity_type="PERSON",
    )


@pytest.fixture
def entity():
    return Entity(
        id="Q110003",
        pageid=112635,
        ns=0,
        title="Q110003",
        lastrevid=1811282860,
        modified="2023-01-14T10:43:23Z",
        type="item",
        labels={
            "de": Property(language="de", value="Fritz Müller"),
            "en": Property(language="en", value="Fritz Mueller"),
            "es": Property(language="es", value="Fritz Mueller"),
            "nl": Property(language="nl", value="Fritz Mueller"),
            "fr": Property(language="fr", value="Fritz Mueller"),
            "mg": Property(language="mg", value="Fritz Mueller"),
            "cy": Property(language="cy", value="Fritz Mueller"),
            "gl": Property(language="gl", value="Fritz Mueller"),
            "hu": Property(language="hu", value="Fritz Mueller"),
            "it": Property(language="it", value="Fritz Müller"),
            "ar": Property(language="ar", value="فريتز مولر"),
            "ru": Property(language="ru", value="Фриц Мюллер"),
            "sl": Property(language="sl", value="Fritz Mueller"),
            "ca": Property(language="ca", value="Fritz Mueller"),
            "pt": Property(language="pt", value="Fritz Mueller"),
            "da": Property(language="da", value="Fritz Mueller"),
            "fi": Property(language="fi", value="Fritz Mueller"),
            "sv": Property(language="sv", value="Fritz Mueller"),
            "nb": Property(language="nb", value="Fritz Müller"),
            "he": Property(language="he", value="פריץ מולר"),
            "pt-br": Property(language="pt-br", value="Fritz Mueller"),
            "arz": Property(language="arz", value="فريتز مولر"),
            "sq": Property(language="sq", value="Fritz Mueller"),
        },
        descriptions={
            "en": Property(language="en", value="engineer from Germany"),
            "de": Property(
                language="de",
                value="deutsch-amerikanischer Ingenieur und Raketenwissenschaftler",
            ),
            "nl": Property(language="nl", value="Duits ruimteingenieur (1907-2001)"),
            "arz": Property(language="arz", value="مهندس فضاء جوى من المانيا"),
        },
        aliases={"nb": [Property(language="nb", value="Fritz Mueller")]},
        claims={
            "P535": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P535",
                        "hash": "24214981a1a0addbfd32ea6539d04603c983f908",
                        "datavalue": {"value": "78137386", "type": "string"},
                        "datatype": "external-id",
                    },
                    "type": "statement",
                    "id": "Q110003$dabbc622-4bdd-ba5c-55cc-4a4288eef8e2",
                    "rank": "normal",
                }
            ],
            "P21": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P21",
                        "hash": "85ad4b1c7348f7a5aac521135040d74e91fb5939",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 6581097,
                                "id": "Q6581097",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "q110003$7D5301FD-1C19-4009-930C-42337BBAB3FA",
                    "rank": "normal",
                    "references": [
                        {
                            "hash": "9a24f7c0208b05d6be97077d855671d1dfdbc0dd",
                            "snaks": {
                                "P143": [
                                    {
                                        "snaktype": "value",
                                        "property": "P143",
                                        "hash": "d38375ffe6fe142663ff55cd783aa4df4301d83d",
                                        "datavalue": {
                                            "value": {
                                                "entity-type": "item",
                                                "numeric-id": 48183,
                                                "id": "Q48183",
                                            },
                                            "type": "wikibase-entityid",
                                        },
                                        "datatype": "wikibase-item",
                                    }
                                ]
                            },
                            "snaks-order": ["P143"],
                        }
                    ],
                }
            ],
            "P19": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P19",
                        "hash": "bcb70aa1d7d414bfa6f95d0f3e73bb23075c3c8b",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 535603,
                                "id": "Q535603",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "q110003$C7056326-BF4F-4203-B66D-95CF00BA1B24",
                    "rank": "normal",
                    "references": [
                        {
                            "hash": "9a24f7c0208b05d6be97077d855671d1dfdbc0dd",
                            "snaks": {
                                "P143": [
                                    {
                                        "snaktype": "value",
                                        "property": "P143",
                                        "hash": "d38375ffe6fe142663ff55cd783aa4df4301d83d",
                                        "datavalue": {
                                            "value": {
                                                "entity-type": "item",
                                                "numeric-id": 48183,
                                                "id": "Q48183",
                                            },
                                            "type": "wikibase-entityid",
                                        },
                                        "datatype": "wikibase-item",
                                    }
                                ]
                            },
                            "snaks-order": ["P143"],
                        }
                    ],
                }
            ],
            "P20": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P20",
                        "hash": "60cdd01959b7a583e58efc05597956cb2ae2f5a6",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 79860,
                                "id": "Q79860",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "q110003$26A39AC0-5881-4619-8253-0050C6C4C36C",
                    "rank": "normal",
                }
            ],
            "P27": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P27",
                        "hash": "9c05984f35ee8b2bbef4845da73ae7032d7dc7e3",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 183,
                                "id": "Q183",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "q110003$F9528D7A-AF35-4EA6-B5D2-6C48EDAD38C2",
                    "rank": "normal",
                    "references": [
                        {
                            "hash": "9a24f7c0208b05d6be97077d855671d1dfdbc0dd",
                            "snaks": {
                                "P143": [
                                    {
                                        "snaktype": "value",
                                        "property": "P143",
                                        "hash": "d38375ffe6fe142663ff55cd783aa4df4301d83d",
                                        "datavalue": {
                                            "value": {
                                                "entity-type": "item",
                                                "numeric-id": 48183,
                                                "id": "Q48183",
                                            },
                                            "type": "wikibase-entityid",
                                        },
                                        "datatype": "wikibase-item",
                                    }
                                ]
                            },
                            "snaks-order": ["P143"],
                        }
                    ],
                },
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P27",
                        "hash": "52d0408c7915122e0519a22577f0cbdcb28f749b",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 30,
                                "id": "Q30",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "q110003$4A1A081D-9C23-422E-A38E-B502E332845E",
                    "rank": "normal",
                },
            ],
            "P31": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P31",
                        "hash": "ad7d38a03cdd40cdc373de0dc4e7b7fcbccb31d9",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 5,
                                "id": "Q5",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "Q110003$FC4405AF-0A61-41B5-9FD9-1E1EC44096BC",
                    "rank": "normal",
                    "references": [
                        {
                            "hash": "fa278ebfc458360e5aed63d5058cca83c46134f1",
                            "snaks": {
                                "P143": [
                                    {
                                        "snaktype": "value",
                                        "property": "P143",
                                        "hash": "e4f6d9441d0600513c4533c672b5ab472dc73694",
                                        "datavalue": {
                                            "value": {
                                                "entity-type": "item",
                                                "numeric-id": 328,
                                                "id": "Q328",
                                            },
                                            "type": "wikibase-entityid",
                                        },
                                        "datatype": "wikibase-item",
                                    }
                                ]
                            },
                            "snaks-order": ["P143"],
                        }
                    ],
                }
            ],
            "P106": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P106",
                        "hash": "62c9b37dcc2822750f24fb07aa4eaf027140ce48",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 10497074,
                                "id": "Q10497074",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "Q110003$D1152851-C68F-47D8-9E44-2B855B150BCD",
                    "rank": "normal",
                },
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P106",
                        "hash": "a4f30786546379e76f5e06bea1c90a99f3847ded",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 81096,
                                "id": "Q81096",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "Q110003$A24C3EA7-2EA0-4E93-AADF-164E8F4B9D6B",
                    "rank": "normal",
                },
            ],
            "P569": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P569",
                        "hash": "ced4d1675ad4f1a3c9dbff9719311c2626575be9",
                        "datavalue": {
                            "value": {
                                "time": "+1907-10-27T00:00:00Z",
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                            "type": "time",
                        },
                        "datatype": "time",
                    },
                    "type": "statement",
                    "id": "Q110003$3354163A-8E18-4FD1-9A9C-EAC7E09FBFB8",
                    "rank": "normal",
                }
            ],
            "P570": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P570",
                        "hash": "5e1032ffa5114ade1208c480f8f608fe4f91ec32",
                        "datavalue": {
                            "value": {
                                "time": "+2001-05-15T00:00:00Z",
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                            "type": "time",
                        },
                        "datatype": "time",
                    },
                    "type": "statement",
                    "id": "Q110003$92C43E95-303F-44FB-B7A5-E18B54D78D73",
                    "rank": "normal",
                }
            ],
            "P735": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P735",
                        "hash": "dc559ecb5845e87eeb20532cb982df1116823ccd",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 1158596,
                                "id": "Q1158596",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "Q110003$BE953B72-7D7B-4E38-9B93-3A79248786EF",
                    "rank": "normal",
                }
            ],
            "P734": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P734",
                        "hash": "42d00f750edf26705ac71a512d7944cefe91086f",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 15042884,
                                "id": "Q15042884",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "Q110003$4F839362-519A-4661-85DE-22FC76652CE8",
                    "rank": "normal",
                }
            ],
            "P646": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P646",
                        "hash": "56542fb96f571510f488ae11bbe89498c407e187",
                        "datavalue": {"value": "/m/0cz8vln", "type": "string"},
                        "datatype": "external-id",
                    },
                    "type": "statement",
                    "id": "Q110003$44B1AE50-3C21-4C16-8903-17309C1F23E7",
                    "rank": "normal",
                }
            ],
            "P1412": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P1412",
                        "hash": "c92f42a19ff65548d3fc6d4fdca0944a825d8879",
                        "datavalue": {
                            "value": {
                                "entity-type": "item",
                                "numeric-id": 188,
                                "id": "Q188",
                            },
                            "type": "wikibase-entityid",
                        },
                        "datatype": "wikibase-item",
                    },
                    "type": "statement",
                    "id": "Q110003$ADDBE697-BEF4-4734-9DA1-801DCBC1B959",
                    "rank": "normal",
                }
            ],
            "P373": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P373",
                        "hash": "1afa07d028050db000db32c091a1a79669022ce6",
                        "datavalue": {"value": "Fritz Mueller", "type": "string"},
                        "datatype": "string",
                    },
                    "type": "statement",
                    "id": "Q110003$F6FA7DC0-8EFF-4B64-BD5D-87EBA20BFD8A",
                    "rank": "normal",
                }
            ],
            "P3368": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P3368",
                        "hash": "5e6c69e41987b5964b78d5b633e0dc7e018eb2a4",
                        "datavalue": {"value": "2452229", "type": "string"},
                        "datatype": "external-id",
                    },
                    "type": "statement",
                    "id": "Q110003$461DD796-AD62-4F6A-AA98-1981A0A93F84",
                    "rank": "normal",
                }
            ],
        },
        sitelinks={
            "arwiki": {
                "site": "arwiki",
                "title": "فريتز مولر (مهندس فضاء جوي)",
                "badges": [],
            },
            "arzwiki": {
                "site": "arzwiki",
                "title": "فريتز مولر (مهندس فضاء جوى من المانيا)",
                "badges": [],
            },
            "commonswiki": {
                "site": "commonswiki",
                "title": "Category:Fritz Mueller",
                "badges": [],
            },
            "dewiki": {
                "site": "dewiki",
                "title": "Fritz Müller (Raumfahrtingenieur)",
                "badges": [],
            },
            "enwiki": {"site": "enwiki", "title": "Fritz Mueller", "badges": []},
            "mgwiki": {"site": "mgwiki", "title": "Fritz Mueller", "badges": []},
        },
    )


@pytest.fixture
def people():
    return {
        WikiDataItem(url="http://www.wikidata.org/entity/Q11977716", qid="Q11977716"),
        WikiDataItem(url="http://www.wikidata.org/entity/Q11977720", qid="Q1197772"),
        WikiDataItem(url="http://www.wikidata.org/entity/Q11977727", qid="Q11977727"),
        WikiDataItem(url="http://www.wikidata.org/entity/Q11977725", qid="Q11977725"),
        WikiDataItem(url="http://www.wikidata.org/entity/Q11977724", qid="Q11977724"),
        WikiDataItem(url="http://www.wikidata.org/entity/Q11977717", qid="Q11977717"),
        WikiDataItem(url="http://www.wikidata.org/entity/Q11977723", qid="Q11977723"),
        WikiDataItem(url="http://www.wikidata.org/entity/Q11977722", qid="Q11977722"),
        WikiDataItem(url="http://www.wikidata.org/entity/Q11977721", qid="Q11977721"),
        WikiDataItem(url="http://www.wikidata.org/entity/Q11977726", qid="Q11977726"),
    }


def test_wiki_service_init(config):
    wikidata_query_service = Mock()
    database = Mock()
    config = Mock()
    wiki_service = WikiService(
        wikidata_query_service_factory=wikidata_query_service,
        database_factory=database,
        config_factory=config,
    )
    assert isinstance(wiki_service, WikiService)


def test_search_for_people_success(config, people):
    """
    Given:
        WikiDataQueryService returns a set of people
        WikiID doesn't exist
        WikiID is not in the queue
    Expect:
        all people are added to the queue
        the last person offset is updated
    """
    limit = 10
    offset = 0
    config.WIKIDATA_SEARCH_LIMIT = limit

    wdqs = Mock()
    wdqs.find_people.return_value = people

    database = Mock()
    database.is_wiki_id_in_queue.return_value = False
    database.wiki_id_exists.return_value = False
    database.get_last_person_offset.return_value = offset

    wiki_service = WikiService(
        wikidata_query_service_factory=lambda: wdqs,
        database_factory=lambda: database,
        config_factory=lambda: config,
    )

    wiki_service.search_for_people()

    database.add_items_to_queue.assert_called_with(
        entity_type="PERSON", wiki_type="WIKIDATA", items=list(people)
    )
    database.save_last_person_offset.assert_called_with(offset=limit + offset)


def test_search_for_people_ignores_ids_that_already_exist(config, people):
    """
    Given:
        WikiDataQueryService returns a set of people
        WikiID exists
        WikiID is not in the queue
    Expect:
        no people are added to the queue
        the last person offset is updated
    """
    limit = 10
    offset = 0
    config.WIKIDATA_SEARCH_LIMIT = limit

    wdqs = Mock()
    wdqs.find_people.return_value = people

    database = Mock()
    database.is_wiki_id_in_queue.return_value = False
    database.wiki_id_exists.return_value = True
    database.get_last_person_offset.return_value = offset

    wiki_service = WikiService(
        wikidata_query_service_factory=lambda: wdqs,
        database_factory=lambda: database,
        config_factory=lambda: config,
    )

    wiki_service.search_for_people()

    database.add_items_to_queue.assert_called_with(
        entity_type="PERSON", wiki_type="WIKIDATA", items=[]
    )
    database.save_last_person_offset.assert_called_with(offset=limit + offset)


def test_search_for_people_ignores_id_already_in_queue(config, people):
    """
    Given:
        WikiDataQueryService returns a set of people
        WikiID doesn't exist
        WikiID is already in the queue
    Expect:
        no people are added to the queue
        the last person offset is updated
    """
    limit = 10
    offset = 0
    config.WIKIDATA_SEARCH_LIMIT = limit

    wdqs = Mock()
    wdqs.find_people.return_value = people

    database = Mock()
    database.is_wiki_id_in_queue.return_value = True
    database.wiki_id_exists.return_value = False
    database.get_last_person_offset.return_value = offset

    wiki_service = WikiService(
        wikidata_query_service_factory=lambda: wdqs,
        database_factory=lambda: database,
        config_factory=lambda: config,
    )

    wiki_service.search_for_people()

    database.add_items_to_queue.assert_called_with(
        entity_type="PERSON", wiki_type="WIKIDATA", items=[]
    )
    database.save_last_person_offset.assert_called_with(offset=limit + offset)


def test_search_for_people_handles_wiki_service_error(config):
    """
    Given:
        WikiDataQueryService raises an error
    Expect:
        no people are added to the queue
        the last person offset is not updated
    """
    limit = 10
    offset = 0
    config.WIKIDATA_SEARCH_LIMIT = limit

    wdqs = Mock()
    wdqs.find_people.side_effect = WikiDataQueryServiceError

    database = Mock()
    database.is_wiki_id_in_queue.return_value = False
    database.wiki_id_exists.return_value = False
    database.get_last_person_offset.return_value = offset

    wiki_service = WikiService(
        wikidata_query_service_factory=lambda: wdqs,
        database_factory=lambda: database,
        config_factory=lambda: config,
    )

    wiki_service.search_for_people()

    database.add_items_to_queue.assert_not_called()
    database.save_last_person_offset.assert_not_called()


@pytest.fixture
def mock_database():
    return Mock(spec=Database)


@pytest.fixture
def mock_wikidata_service():
    return Mock(spec=WikiDataQueryService)


@pytest.fixture
def mock_rest_client():
    return Mock(spec=RestClient)


@pytest.fixture
def mock_config():
    config = WikiServiceConfig()
    config.username = "test_user"
    config.password = "test_pass"
    return config


@pytest.fixture
def wiki_service(mock_database, mock_wikidata_service, mock_rest_client, mock_config):
    with patch("wiki_service.wiki_service.RestClient") as mock_rest_client_class:
        mock_rest_client_class.return_value = mock_rest_client
        service = WikiService(
            wikidata_query_service_factory=lambda: mock_wikidata_service,
            config_factory=lambda: mock_config,
            database_factory=lambda: mock_database,
        )
        return service


def test_build_events_from_person_empty_queue(wiki_service, mock_database):
    # Arrange
    mock_database.get_oldest_item_from_queue.return_value = None

    # Act
    wiki_service.build_events_from_person()

    # Assert
    mock_database.get_oldest_item_from_queue.assert_called_once()


def test_build_events_from_person_wrong_entity_type(wiki_service, mock_database):
    # Arrange
    mock_database.get_oldest_item_from_queue.return_value = Mock(
        wiki_id="Q123", entity_type="PLACE"
    )

    # Act
    wiki_service.build_events_from_person()

    # Assert
    mock_database.report_queue_error.assert_called_once_with(
        wiki_id="Q123", error_time=ANY, errors="Unknown entity type field: PLACE"
    )


def test_build_events_from_person_success(
    wiki_service, mock_database, mock_wikidata_service, mock_rest_client
):
    # Arrange
    mock_database.get_oldest_item_from_queue.return_value = Mock(
        wiki_id="Q123", entity_type="PERSON"
    )

    # Mock entity data
    entity = Entity(
        id="Q123",
        labels={"en": {"language": "en", "value": "Test Person"}},
        claims={
            "P19": [
                {"mainsnak": {"datavalue": {"value": {"id": "Q456"}}}}
            ],  # birthplace
            "P569": [{"mainsnak": {"property": "P569"}}],  # birthdate
        },
    )
    mock_wikidata_service.get_entity.return_value = entity

    # Mock event factory
    mock_event = Mock(
        summary="Test Person was born in Test Place",
        people_tags=[
            Mock(name="Test Person", wiki_id="Q123", start_char=0, stop_char=10)
        ],
        place_tag=Mock(
            name="Test Place",
            wiki_id="Q456",
            start_char=23,
            stop_char=33,
            location=GeoLocation(
                coordinates=CoordinateLocation(latitude=51.5074, longitude=-0.1278),
                geoshape=None,
            ),
        ),
        time_tag=Mock(
            name="1900",
            wiki_id="Q789",
            start_char=11,
            stop_char=15,
            time_definition=TimeDefinition(
                datetime=datetime(1900, 1, 1, tzinfo=timezone.utc),
                calendar_model="Q1985727",
                precision=9,
            ),
        ),
    )
    mock_event_factory = Mock(spec=EventFactory)
    mock_event_factory.entity_has_event.return_value = True
    mock_event_factory.create_wiki_event.return_value = mock_event
    mock_event_factory.label = "Test Factory"
    mock_event_factory.version = 1

    with patch("wiki_service.wiki_service.get_event_factories") as mock_get_factories:
        mock_get_factories.return_value = [mock_event_factory]

        # Mock REST responses
        mock_rest_client.get_tags.return_value = {
            "wikidata_ids": [
                {"wikidata_id": "Q123", "id": None},
                {"wikidata_id": "Q456", "id": None},
                {"wikidata_id": "Q789", "id": None},
            ]
        }
        mock_rest_client.create_person.return_value = {"id": "uuid-1"}
        mock_rest_client.create_place.return_value = {"id": "uuid-2"}
        mock_rest_client.create_time.return_value = {"id": "uuid-3"}
        mock_rest_client.create_event.return_value = {"id": "uuid-4"}

        # Act
        wiki_service.build_events_from_person()

        # Assert
        mock_database.get_oldest_item_from_queue.assert_called_once()
        mock_wikidata_service.get_entity.assert_called_once_with(id="Q123")
        mock_get_factories.assert_called_once_with(
            entity=entity, query=mock_wikidata_service
        )
        mock_event_factory.entity_has_event.assert_called_once()
        mock_event_factory.create_wiki_event.assert_called_once()

        # Verify REST calls
        mock_rest_client.get_tags.assert_called_once_with(
            wikidata_ids=["Q123", "Q456", "Q789"]
        )
        mock_rest_client.create_person.assert_called_once_with(
            name="Test Person",
            wikidata_id="Q123",
            wikidata_url="https://www.wikidata.org/wiki/Q123",
        )
        mock_rest_client.create_place.assert_called_once_with(
            name="Test Place",
            wikidata_id="Q456",
            wikidata_url="https://www.wikidata.org/wiki/Q456",
            latitude=51.5074,
            longitude=-0.1278,
        )
        mock_rest_client.create_time.assert_called_once_with(
            name="1900",
            wikidata_id="Q789",
            wikidata_url="https://www.wikidata.org/wiki/Q789",
            date=datetime(1900, 1, 1, tzinfo=timezone.utc),
            calendar_model="Q1985727",
            precision=9,
        )

        mock_rest_client.create_event.assert_called_once_with(
            summary="Test Person was born in Test Place",
            tags=[
                {
                    "id": "uuid-1",
                    "name": "Test Person",
                    "start_char": 0,
                    "stop_char": 10,
                },
                {
                    "id": "uuid-2",
                    "name": "Test Place",
                    "start_char": 23,
                    "stop_char": 33,
                },
                {"id": "uuid-3", "name": "1900", "start_char": 11, "stop_char": 15},
            ],
            citation={
                "access_date": ANY,
                "wikidata_item_id": "Q123",
                "wikidata_item_title": "Test Person",
                "wikidata_item_url": "https://www.wikidata.org/wiki/Q123",
            },
        )

        mock_database.upsert_created_event.assert_called_once_with(
            wiki_id="Q123", factory_label="Test Factory", factory_version=1
        )
        mock_database.remove_item_from_queue.assert_called_once_with(wiki_id="Q123")


def test_build_events_from_person_rest_error(
    wiki_service, mock_database, mock_wikidata_service, mock_rest_client
):
    # Arrange
    mock_database.get_oldest_item_from_queue.return_value = Mock(
        wiki_id="Q123", entity_type="PERSON"
    )

    entity = Entity(
        id="Q123",
        labels={"en": Label(language="en", value="Test Person")},
        claims={
            "P19": [{"mainsnak": {"datavalue": {"value": {"id": "Q456"}}}}],
            "P569": [{"mainsnak": {"property": "P569"}}],
        },
    )
    mock_wikidata_service.get_entity.return_value = entity

    mock_event = Mock(
        summary="Test Person was born in Test Place",
        people_tags=[
            Mock(name="Test Person", wiki_id="Q123", start_char=0, stop_char=10)
        ],
        place_tag=Mock(
            name="Test Place",
            wiki_id="Q456",
            start_char=23,
            stop_char=33,
            location=GeoLocation(coordinates=None, geoshape=None),
        ),
        time_tag=Mock(
            name="1900",
            wiki_id=None,
            start_char=11,
            stop_char=15,
            time_definition=TimeDefinition(
                datetime=datetime(1900, 1, 1, tzinfo=timezone.utc),
                calendar_model="Q1985727",
                precision=9,
            ),
        ),
    )
    mock_event_factory = Mock(spec=EventFactory)
    mock_event_factory.entity_has_event.return_value = True
    mock_event_factory.create_wiki_event.return_value = mock_event
    mock_event_factory.label = "Test Factory"
    mock_event_factory.version = 1

    with patch("wiki_service.wiki_service.get_event_factories") as mock_get_factories:
        mock_get_factories.return_value = [mock_event_factory]

        # Mock REST error
        mock_rest_client.get_tags.side_effect = RestClientError("Failed to get tags")

        # Act
        wiki_service.build_events_from_person()

        # Assert
        mock_database.upsert_created_event.assert_called_once_with(
            wiki_id="Q123",
            factory_label="Test Factory",
            factory_version=1,
            errors={"error": "Failed to get tags"},
        )
        mock_database.remove_item_from_queue.assert_not_called()


def test_build_events_from_person_wikidata_error(
    wiki_service, mock_database, mock_wikidata_service
):
    # Arrange
    mock_database.get_oldest_item_from_queue.return_value = Mock(
        wiki_id="Q123", entity_type="PERSON"
    )
    mock_wikidata_service.get_entity.side_effect = WikiDataQueryServiceError(
        "API error"
    )

    # Act
    wiki_service.build_events_from_person()

    # Assert
    mock_database.report_queue_error.assert_called_once_with(
        wiki_id="Q123", error_time=ANY, errors="WikiData query had an error: API error"
    )
    mock_database.remove_item_from_queue.assert_not_called()
