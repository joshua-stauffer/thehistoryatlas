from unittest.mock import create_autospec

import pytest

from tests.conftest import MockQuery
from wiki_service.event_factories.event_factory import Query, UnprocessableEventError
from wiki_service.event_factories.person_started_working_for import (
    PersonStartedWorkingFor,
)
from wiki_service.event_factories.q_numbers import (
    EMPLOYER,
    START_TIME,
    SUBJECT_HAS_ROLE,
    POSITION_HELD,
)
from wiki_service.wikidata_query_service import (
    Entity,
    GeoLocation,
    CoordinateLocation,
    Property,
)


@pytest.fixture
def employer_geo_location() -> GeoLocation:
    return GeoLocation(
        coordinates=CoordinateLocation(
            id="Q12345$COORDINATE_ID",
            rank="normal",
            type="statement",
            snaktype="value",
            property="P625",
            hash="some_hash",
            latitude=40.7128,
            longitude=-74.0060,
            altitude=None,
            precision=0.0001,
            globe="http://www.wikidata.org/entity/Q2",
        ),
        geoshape=None,
    )


def create_time_claim(time: str, precision: int) -> dict:
    return {
        "id": f"Q54321$time-{time}",
        "type": "statement",
        "rank": "normal",
        "mainsnak": {
            "snaktype": "value",
            "property": START_TIME,
            "hash": "some_hash",
            "datavalue": {
                "value": {
                    "time": time,
                    "timezone": 0,
                    "before": 0,
                    "after": 0,
                    "precision": precision,
                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                },
                "type": "time",
            },
            "datatype": "time",
        },
    }


@pytest.fixture
def mock_entity_with_employer() -> Entity:
    return Entity(
        id="Q54321",
        pageid=54321,
        ns=0,
        title="Q54321",
        lastrevid=1234567,
        modified="2024-03-30T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="John Doe")},
        descriptions={"en": Property(language="en", value="Test person")},
        aliases={"en": [Property(language="en", value="J. Doe")]},
        claims={
            EMPLOYER: [
                {
                    "id": "Q54321$employer",
                    "type": "statement",
                    "rank": "normal",
                    "mainsnak": {
                        "snaktype": "value",
                        "property": EMPLOYER,
                        "hash": "some_hash",
                        "datavalue": {
                            "value": {"id": "Q12345"},
                            "type": "wikibase-entityid",
                        },
                    },
                    "qualifiers": {
                        START_TIME: [create_time_claim("+1990-01-01T00:00:00Z", 11)]
                    },
                }
            ]
        },
        sitelinks={},
    )


@pytest.fixture
def mock_entity_with_employer_and_role() -> Entity:
    return Entity(
        id="Q54321",
        pageid=54321,
        ns=0,
        title="Q54321",
        lastrevid=1234567,
        modified="2024-03-30T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="John Doe")},
        descriptions={"en": Property(language="en", value="Test person")},
        aliases={"en": [Property(language="en", value="J. Doe")]},
        claims={
            EMPLOYER: [
                {
                    "id": "Q54321$employer",
                    "type": "statement",
                    "rank": "normal",
                    "mainsnak": {
                        "snaktype": "value",
                        "property": EMPLOYER,
                        "hash": "some_hash",
                        "datavalue": {
                            "value": {"id": "Q12345"},
                            "type": "wikibase-entityid",
                        },
                    },
                    "qualifiers": {
                        START_TIME: [create_time_claim("+1990-01-01T00:00:00Z", 11)],
                        SUBJECT_HAS_ROLE: [
                            {
                                "snaktype": "value",
                                "property": SUBJECT_HAS_ROLE,
                                "hash": "some_hash",
                                "datavalue": {
                                    "value": {"id": "Q67890"},
                                    "type": "wikibase-entityid",
                                },
                            }
                        ],
                    },
                }
            ]
        },
        sitelinks={},
    )


@pytest.fixture
def mock_entity_with_employer_and_position() -> Entity:
    return Entity(
        id="Q54321",
        pageid=54321,
        ns=0,
        title="Q54321",
        lastrevid=1234567,
        modified="2024-03-30T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="John Doe")},
        descriptions={"en": Property(language="en", value="Test person")},
        aliases={"en": [Property(language="en", value="J. Doe")]},
        claims={
            EMPLOYER: [
                {
                    "id": "Q54321$employer",
                    "type": "statement",
                    "rank": "normal",
                    "mainsnak": {
                        "snaktype": "value",
                        "property": EMPLOYER,
                        "hash": "some_hash",
                        "datavalue": {
                            "value": {"id": "Q12345"},
                            "type": "wikibase-entityid",
                        },
                    },
                    "qualifiers": {
                        START_TIME: [create_time_claim("+1990-01-01T00:00:00Z", 10)],
                        POSITION_HELD: [
                            {
                                "snaktype": "value",
                                "property": POSITION_HELD,
                                "hash": "some_hash",
                                "datavalue": {
                                    "value": {"id": "Q67890"},
                                    "type": "wikibase-entityid",
                                },
                            }
                        ],
                    },
                }
            ]
        },
        sitelinks={},
    )


@pytest.fixture
def mock_entity_without_employer() -> Entity:
    return Entity(
        id="Q54321",
        pageid=54321,
        ns=0,
        title="Q54321",
        lastrevid=1234567,
        modified="2024-03-30T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="John Doe")},
        descriptions={"en": Property(language="en", value="Test person")},
        aliases={"en": [Property(language="en", value="J. Doe")]},
        claims={},
        sitelinks={},
    )


@pytest.fixture
def mock_entity_with_employer_no_start_time() -> Entity:
    return Entity(
        id="Q54321",
        pageid=54321,
        ns=0,
        title="Q54321",
        lastrevid=1234567,
        modified="2024-03-30T00:00:00Z",
        type="item",
        labels={"en": Property(language="en", value="John Doe")},
        descriptions={"en": Property(language="en", value="Test person")},
        aliases={"en": [Property(language="en", value="J. Doe")]},
        claims={
            EMPLOYER: [
                {
                    "id": "Q54321$employer",
                    "type": "statement",
                    "rank": "normal",
                    "mainsnak": {
                        "snaktype": "value",
                        "property": EMPLOYER,
                        "hash": "some_hash",
                        "datavalue": {
                            "value": {"id": "Q12345"},
                            "type": "wikibase-entityid",
                        },
                    },
                }
            ]
        },
        sitelinks={},
    )


class TestPersonStartedWorkingFor:
    ENTITY_LOOKUP = {
        "Q12345": "ACME Corporation",
        "Q67890": "Software Engineer",
    }

    def test_entity_has_event_success(self, mock_entity_with_employer: Entity) -> None:
        query = create_autospec(Query)
        factory = PersonStartedWorkingFor(entity=mock_entity_with_employer, query=query)
        assert factory.entity_has_event()

    def test_entity_has_event_no_employer(
        self, mock_entity_without_employer: Entity
    ) -> None:
        query = create_autospec(Query)
        factory = PersonStartedWorkingFor(
            entity=mock_entity_without_employer, query=query
        )
        assert not factory.entity_has_event()

    def test_entity_has_event_no_start_time(
        self, mock_entity_with_employer_no_start_time: Entity
    ) -> None:
        query = create_autospec(Query)
        factory = PersonStartedWorkingFor(
            entity=mock_entity_with_employer_no_start_time, query=query
        )
        assert not factory.entity_has_event()

    def test_create_wiki_event_basic(
        self,
        mock_entity_with_employer: Entity,
        employer_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.ENTITY_LOOKUP,
            geo_location=employer_geo_location,
            expected_geo_location_id="Q12345",
        )
        factory = PersonStartedWorkingFor(
            entity=mock_entity_with_employer, query=mock_query
        )

        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On January 1, 1990, John Doe started working for ACME Corporation."
        )

    def test_create_wiki_event_with_role(
        self,
        mock_entity_with_employer_and_role: Entity,
        employer_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.ENTITY_LOOKUP,
            geo_location=employer_geo_location,
            expected_geo_location_id="Q12345",
        )
        factory = PersonStartedWorkingFor(
            entity=mock_entity_with_employer_and_role, query=mock_query
        )

        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On January 1, 1990, John Doe started working for ACME Corporation as Software Engineer."
        )

    def test_create_wiki_event_with_position(
        self,
        mock_entity_with_employer_and_position: Entity,
        employer_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.ENTITY_LOOKUP,
            geo_location=employer_geo_location,
            expected_geo_location_id="Q12345",
        )
        factory = PersonStartedWorkingFor(
            entity=mock_entity_with_employer_and_position, query=mock_query
        )

        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "John Doe started working for ACME Corporation as Software Engineer in January 1990."
        )

    def test_create_wiki_event_no_location(
        self,
        mock_entity_with_employer: Entity,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.ENTITY_LOOKUP,
            geo_location=GeoLocation(coordinates=None, geoshape=None),
            expected_geo_location_id="Q12345",
        )
        factory = PersonStartedWorkingFor(
            entity=mock_entity_with_employer, query=mock_query
        )

        with pytest.raises(UnprocessableEventError):
            factory.create_wiki_event()

    def test_create_wiki_event_no_events(
        self,
        mock_entity_without_employer: Entity,
    ) -> None:
        query = create_autospec(Query)
        factory = PersonStartedWorkingFor(
            entity=mock_entity_without_employer, query=query
        )

        with pytest.raises(UnprocessableEventError):
            factory.create_wiki_event()
