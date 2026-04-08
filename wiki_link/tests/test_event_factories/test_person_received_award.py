from unittest.mock import create_autospec

import pytest

from tests.conftest import MockQuery
from wiki_service.event_factories.event_factory import Query, UnprocessableEventError
from wiki_service.event_factories.person_received_award import PersonReceivedAward
from wiki_service.wikidata_query_service import (
    Entity,
    GeoLocation,
    CoordinateLocation,
    Property,
    TimeDefinition,
    LocationResult,
)


class TestPersonReceivedAward:
    AWARD_ENTITY_LOOKUP = {
        "Q123": "Nobel Prize in Physics",  # Example award
        "Q456": "Stockholm",  # Example location
        "Q789": "Royal Swedish Academy of Sciences",  # Example conferrer
    }

    @pytest.fixture
    def mock_award_claim(self):
        return {
            "mainsnak": {
                "datavalue": {
                    "value": {"id": "Q123"},
                    "type": "wikibase-entityid",
                },
            },
            "qualifiers": {
                "P585": [  # Point in time
                    {
                        "datavalue": {
                            "value": {
                                "time": "+1921-00-00T00:00:00Z",
                                "precision": 9,
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                            "type": "time",
                        }
                    }
                ],
                "P276": [  # Location
                    {
                        "datavalue": {
                            "value": {"id": "Q456"},
                            "type": "wikibase-entityid",
                        }
                    }
                ],
                "P1027": [  # Conferred by
                    {
                        "datavalue": {
                            "value": {"id": "Q789"},
                            "type": "wikibase-entityid",
                        }
                    }
                ],
            },
        }

    @pytest.fixture
    def mock_award_entity(self):
        return Entity(
            id="Q123",
            pageid=123,
            ns=0,
            title="Q123",
            lastrevid=456,
            modified="2024-04-05T00:00:00Z",
            type="item",
            labels={"en": Property(language="en", value="Nobel Prize in Physics")},
            descriptions={"en": Property(language="en", value="Physics award")},
            aliases={"en": []},
            claims={},
            sitelinks={},
        )

    @pytest.fixture
    def mock_person_entity(self):
        return Entity(
            id="Q937",
            pageid=937,
            ns=0,
            title="Q937",
            lastrevid=123456,
            modified="2024-04-05T00:00:00Z",
            type="item",
            labels={"en": Property(language="en", value="Albert Einstein")},
            descriptions={"en": Property(language="en", value="German physicist")},
            aliases={"en": []},
            claims={
                "P166": [  # Award received
                    {
                        "mainsnak": {
                            "datavalue": {
                                "value": {"id": "Q123"},
                                "type": "wikibase-entityid",
                            },
                            "property": "P166",
                            "snaktype": "value",
                            "hash": "some_hash",
                        },
                        "type": "statement",
                        "rank": "normal",
                        "qualifiers": {
                            "P585": [  # Point in time
                                {
                                    "datavalue": {
                                        "value": {
                                            "time": "+1921-12-10T00:00:00Z",
                                            "timezone": 0,
                                            "before": 0,
                                            "after": 0,
                                            "precision": 11,
                                            "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                        },
                                        "type": "time",
                                    },
                                    "property": "P585",
                                    "snaktype": "value",
                                    "hash": "some_hash",
                                }
                            ],
                            "P276": [  # Location
                                {
                                    "datavalue": {
                                        "value": {"id": "Q456"},
                                        "type": "wikibase-entityid",
                                    },
                                    "property": "P276",
                                    "snaktype": "value",
                                    "hash": "some_hash",
                                }
                            ],
                            "P1027": [  # Conferred by
                                {
                                    "datavalue": {
                                        "value": {"id": "Q789"},
                                        "type": "wikibase-entityid",
                                    },
                                    "property": "P1027",
                                    "snaktype": "value",
                                    "hash": "some_hash",
                                }
                            ],
                        },
                    }
                ]
            },
            sitelinks={},
        )

    @pytest.fixture
    def mock_location(self):
        return GeoLocation(
            coordinates=CoordinateLocation(
                id="Q456$COORDINATE_ID",
                rank="normal",
                type="statement",
                snaktype="value",
                property="P625",
                hash="some_hash",
                latitude=59.3293,
                longitude=18.0686,
                altitude=None,
                precision=0.0001,
                globe="http://www.wikidata.org/entity/Q2",
            ),
            geoshape=None,
        )

    def test_entity_has_event_success(self, mock_person_entity: Entity) -> None:
        query = create_autospec(Query)
        factory = PersonReceivedAward(
            entity=mock_person_entity, query=query, entity_type="PERSON"
        )
        assert factory.entity_has_event()

    def test_entity_has_event_failure_wrong_type(
        self, mock_person_entity: Entity
    ) -> None:
        query = create_autospec(Query)
        factory = PersonReceivedAward(
            entity=mock_person_entity, query=query, entity_type="PLACE"
        )
        assert not factory.entity_has_event()

    def test_entity_has_event_failure_no_award(self) -> None:
        query = create_autospec(Query)
        entity = Entity(
            id="Q937",
            pageid=937,
            ns=0,
            title="Q937",
            lastrevid=123456,
            modified="2024-04-05T00:00:00Z",
            type="item",
            labels={"en": Property(language="en", value="Albert Einstein")},
            descriptions={"en": Property(language="en", value="Physicist")},
            aliases={"en": []},
            claims={},
            sitelinks={},
        )
        factory = PersonReceivedAward(entity=entity, query=query, entity_type="PERSON")
        assert not factory.entity_has_event()

    def test_create_wiki_event_basic(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonReceivedAward(
            entity=mock_person_entity,
            query=mock_query,
            entity_type="PERSON",
        )

        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On December 10, 1921, Albert Einstein received the Nobel Prize in Physics from Royal Swedish Academy of Sciences in Stockholm."
        )

    def test_create_wiki_event_precision_11(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Modify the time precision to 11 (day)
        mock_person_entity.claims["P166"][0]["qualifiers"]["P585"][0]["datavalue"][
            "value"
        ]["time"] = "+1921-12-10T00:00:00Z"
        mock_person_entity.claims["P166"][0]["qualifiers"]["P585"][0]["datavalue"][
            "value"
        ]["precision"] = 11

        mock_query = MockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonReceivedAward(
            entity=mock_person_entity,
            query=mock_query,
            entity_type="PERSON",
        )

        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On December 10, 1921, Albert Einstein received the Nobel Prize in Physics from Royal Swedish Academy of Sciences in Stockholm."
        )

    def test_create_wiki_event_precision_10(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Modify the time precision to 10 (month)
        mock_person_entity.claims["P166"][0]["qualifiers"]["P585"][0]["datavalue"][
            "value"
        ]["time"] = "+1921-12-00T00:00:00Z"
        mock_person_entity.claims["P166"][0]["qualifiers"]["P585"][0]["datavalue"][
            "value"
        ]["precision"] = 10

        mock_query = MockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonReceivedAward(
            entity=mock_person_entity,
            query=mock_query,
            entity_type="PERSON",
        )

        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "Albert Einstein received the Nobel Prize in Physics from Royal Swedish Academy of Sciences in Stockholm in December 1921."
        )

    def test_create_wiki_event_no_location(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Remove location from qualifiers
        del mock_person_entity.claims["P166"][0]["qualifiers"]["P276"]

        mock_query = MockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonReceivedAward(
            entity=mock_person_entity,
            query=mock_query,
            entity_type="PERSON",
        )

        with pytest.raises(UnprocessableEventError):
            factory.create_wiki_event()

    def test_create_wiki_event_no_conferrer(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Remove conferrer from qualifiers
        del mock_person_entity.claims["P166"][0]["qualifiers"]["P1027"]

        mock_query = MockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonReceivedAward(
            entity=mock_person_entity,
            query=mock_query,
            entity_type="PERSON",
        )

        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On December 10, 1921, Albert Einstein received the Nobel Prize in Physics in Stockholm."
        )

    def test_create_wiki_event_no_time(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Remove time from qualifiers
        del mock_person_entity.claims["P166"][0]["qualifiers"]["P585"]

        mock_query = MockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonReceivedAward(
            entity=mock_person_entity,
            query=mock_query,
            entity_type="PERSON",
        )

        with pytest.raises(UnprocessableEventError):
            factory.create_wiki_event()

    def test_create_wiki_event_with_rationale(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Add rationale to qualifiers
        mock_person_entity.claims["P166"][0]["qualifiers"]["P1013"] = [
            {
                "datavalue": {
                    "value": {
                        "text": "his services to theoretical physics",
                        "language": "en",
                    },
                    "type": "monolingualtext",
                }
            }
        ]

        mock_query = MockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonReceivedAward(
            entity=mock_person_entity,
            query=mock_query,
            entity_type="PERSON",
        )

        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On December 10, 1921, Albert Einstein received the Nobel Prize in Physics from Royal Swedish Academy of Sciences in Stockholm."
        )

    def test_create_wiki_event_location_from_award(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Remove location from qualifiers but add it to award entity
        del mock_person_entity.claims["P166"][0]["qualifiers"]["P276"]

        # Create award entity with location
        award_entity = Entity(
            id="Q123",
            pageid=123,
            ns=0,
            title="Q123",
            lastrevid=456,
            modified="2024-04-05T00:00:00Z",
            type="item",
            labels={"en": Property(language="en", value="Nobel Prize in Physics")},
            descriptions={"en": Property(language="en", value="Physics award")},
            aliases={"en": []},
            claims={
                "P276": [  # Location
                    {
                        "mainsnak": {
                            "datavalue": {
                                "value": {"id": "Q456"},
                                "type": "wikibase-entityid",
                            }
                        }
                    }
                ]
            },
            sitelinks={},
        )

        class CustomMockQuery(MockQuery):
            def get_entity(self, id: str):
                if id == "Q123":
                    return award_entity
                return None

        mock_query = CustomMockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonReceivedAward(
            entity=mock_person_entity,
            query=mock_query,
            entity_type="PERSON",
        )

        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On December 10, 1921, Albert Einstein received the Nobel Prize in Physics from Royal Swedish Academy of Sciences in Stockholm."
        )


class MockQuery:
    def __init__(
        self,
        entity_lookup: dict[str, str],
        geo_location: GeoLocation,
        expected_geo_location_id: str,
    ):
        self.entity_lookup = entity_lookup
        self.geo_location = geo_location
        self.expected_geo_location_id = expected_geo_location_id

    def get_label(self, id: str, language: str):
        assert id in self.entity_lookup
        return self.entity_lookup[id]

    def get_geo_location(self, id: str):
        assert id == self.expected_geo_location_id
        return self.geo_location

    def get_entity(self, id: str) -> Entity:
        # Return a mock award entity
        return Entity(
            id=id,
            pageid=123,
            ns=0,
            title=id,
            lastrevid=456,
            modified="2024-04-01T00:00:00Z",
            type="item",
            labels={"en": Property(language="en", value=self.entity_lookup[id])},
            descriptions={"en": Property(language="en", value="Test description")},
            aliases={"en": []},
            claims={},
            sitelinks={},
        )

    def get_time_definition_from_claim(
        self, claim: dict, time_props: list[str]
    ) -> TimeDefinition | None:
        # Return None if no time qualifier is present
        if "P585" not in claim.get("qualifiers", {}):
            return None

        # Get the time value from the qualifier
        time_qualifier = claim["qualifiers"]["P585"][0]
        return TimeDefinition(
            id=f"Q{hash(str(claim))}",
            type="statement",
            rank="normal",
            hash="some_hash",
            snaktype="value",
            property="P585",
            time=time_qualifier["datavalue"]["value"]["time"],
            timezone=time_qualifier["datavalue"]["value"]["timezone"],
            before=time_qualifier["datavalue"]["value"]["before"],
            after=time_qualifier["datavalue"]["value"]["after"],
            precision=time_qualifier["datavalue"]["value"]["precision"],
            calendarmodel=time_qualifier["datavalue"]["value"]["calendarmodel"],
        )

    def get_location_from_claim(
        self, claim: dict, location_props: list[str]
    ) -> LocationResult | None:
        # Return None if no location qualifier is present
        if "P276" not in claim.get("qualifiers", {}):
            return None

        # Return a mock location result
        return LocationResult(
            name="Stockholm",
            id=self.expected_geo_location_id,
            geo_location=self.geo_location,
        )

    def get_location_from_entity(
        self, entity: Entity, claim_props: list[str]
    ) -> LocationResult | None:
        # Return None if no location claim is present
        for prop in claim_props:
            if prop in entity.claims:
                return LocationResult(
                    name="Stockholm",
                    id=self.expected_geo_location_id,
                    geo_location=self.geo_location,
                )
        return None
