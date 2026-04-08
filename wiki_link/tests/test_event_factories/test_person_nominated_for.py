from unittest.mock import create_autospec

import pytest

from tests.conftest import MockQuery
from wiki_service.event_factories.event_factory import Query, UnprocessableEventError
from wiki_service.event_factories.person_nominated_for import PersonNominatedFor
from wiki_service.wikidata_query_service import (
    Entity,
    GeoLocation,
    CoordinateLocation,
    Property,
    TimeDefinition,
    LocationResult,
)


class ExtendedMockQuery(MockQuery):
    def get_entity(self, id: str):
        return Entity(
            id=id,
            pageid=123,
            ns=0,
            title=id,
            lastrevid=456,
            modified="2024-04-05T00:00:00Z",
            type="item",
            labels={"en": Property(language="en", value=self.entity_lookup[id])},
            descriptions={"en": Property(language="en", value="Test description")},
            aliases={"en": []},
            claims={},
            sitelinks={},
        )

    def get_time_definition_from_claim(self, claim, time_props):
        # Extract time info from the claim's qualifiers
        for prop in time_props:
            if prop in claim.get("qualifiers", {}):
                time_data = claim["qualifiers"][prop][0]["datavalue"]["value"]
                return TimeDefinition(
                    id=f"T{hash(str(time_data))}",
                    type="statement",
                    rank="normal",
                    hash="some_hash",
                    snaktype="value",
                    property=prop,
                    time=time_data["time"],
                    timezone=time_data["timezone"],
                    before=time_data["before"],
                    after=time_data["after"],
                    precision=time_data["precision"],
                    calendarmodel=time_data["calendarmodel"],
                )
        return None

    def get_location_from_claim(self, claim, location_props):
        for prop in location_props:
            if prop in claim.get("qualifiers", {}):
                location_id = claim["qualifiers"][prop][0]["datavalue"]["value"]["id"]
                if location_id == self.expected_geo_location_id:
                    return LocationResult(
                        name=self.entity_lookup[location_id],
                        id=location_id,
                        geo_location=self.geo_location,
                    )
        return None

    def get_location_from_entity(self, entity, location_props):
        for prop in location_props:
            if prop in entity.claims:
                location_id = entity.claims[prop][0]["mainsnak"]["datavalue"]["value"][
                    "id"
                ]
                if location_id == self.expected_geo_location_id:
                    return LocationResult(
                        name=self.entity_lookup[location_id],
                        id=location_id,
                        geo_location=self.geo_location,
                    )
        return None


class TestPersonNominatedFor:
    AWARD_ENTITY_LOOKUP = {
        "Q123": "Academy Award for Best Actor",  # Example award
        "Q456": "Los Angeles",  # Example location
        "Q789": "Academy of Motion Picture Arts and Sciences",  # Example conferrer
    }

    @pytest.fixture
    def mock_nomination_claim(self):
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
                                "time": "+1994-00-00T00:00:00Z",
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
            labels={
                "en": Property(language="en", value="Academy Award for Best Actor")
            },
            descriptions={"en": Property(language="en", value="Film award")},
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
            labels={"en": Property(language="en", value="Morgan Freeman")},
            descriptions={"en": Property(language="en", value="American actor")},
            aliases={"en": []},
            claims={
                "P1411": [  # Nominated for
                    {
                        "mainsnak": {
                            "datavalue": {
                                "value": {"id": "Q123"},
                                "type": "wikibase-entityid",
                            },
                            "property": "P1411",
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
                                            "time": "+1994-03-21T00:00:00Z",
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
                latitude=34.0522,
                longitude=-118.2437,
                altitude=None,
                precision=0.0001,
                globe="http://www.wikidata.org/entity/Q2",
            ),
            geoshape=None,
        )

    def test_entity_has_event_success(self, mock_person_entity: Entity) -> None:
        query = create_autospec(Query)
        factory = PersonNominatedFor(
            entity=mock_person_entity, query=query, entity_type="PERSON"
        )
        assert factory.entity_has_event()

    def test_entity_has_event_failure_wrong_type(
        self, mock_person_entity: Entity
    ) -> None:
        query = create_autospec(Query)
        factory = PersonNominatedFor(
            entity=mock_person_entity, query=query, entity_type="PLACE"
        )
        assert not factory.entity_has_event()

    def test_entity_has_event_failure_no_nomination(self) -> None:
        query = create_autospec(Query)
        entity = Entity(
            id="Q937",
            pageid=937,
            ns=0,
            title="Q937",
            lastrevid=123456,
            modified="2024-04-05T00:00:00Z",
            type="item",
            labels={"en": Property(language="en", value="Morgan Freeman")},
            descriptions={"en": Property(language="en", value="American actor")},
            aliases={"en": []},
            claims={},
            sitelinks={},
        )
        factory = PersonNominatedFor(entity=entity, query=query, entity_type="PERSON")
        assert not factory.entity_has_event()

    def test_create_wiki_event_basic(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        query = ExtendedMockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonNominatedFor(
            entity=mock_person_entity, query=query, entity_type="PERSON"
        )
        events = factory.create_wiki_event()
        assert len(events) == 1
        event = events[0]
        assert (
            event.summary
            == "On March 21, 1994, Morgan Freeman was nominated for the Academy Award for Best Actor by Academy of Motion Picture Arts and Sciences in Los Angeles."
        )

    def test_create_wiki_event_precision_11(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Precision 11 is already tested in test_create_wiki_event_basic
        pass

    def test_create_wiki_event_precision_10(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Modify the time precision to 10 (month)
        mock_person_entity.claims["P1411"][0]["qualifiers"]["P585"][0]["datavalue"][
            "value"
        ]["time"] = "+1994-03-00T00:00:00Z"
        mock_person_entity.claims["P1411"][0]["qualifiers"]["P585"][0]["datavalue"][
            "value"
        ]["precision"] = 10

        query = ExtendedMockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonNominatedFor(
            entity=mock_person_entity, query=query, entity_type="PERSON"
        )
        events = factory.create_wiki_event()
        assert len(events) == 1
        event = events[0]
        assert (
            event.summary
            == "Morgan Freeman was nominated for the Academy Award for Best Actor by Academy of Motion Picture Arts and Sciences in Los Angeles in March 1994."
        )

    def test_create_wiki_event_precision_9(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Modify the time precision to 9 (year)
        mock_person_entity.claims["P1411"][0]["qualifiers"]["P585"][0]["datavalue"][
            "value"
        ]["time"] = "+1994-00-00T00:00:00Z"
        mock_person_entity.claims["P1411"][0]["qualifiers"]["P585"][0]["datavalue"][
            "value"
        ]["precision"] = 9

        query = ExtendedMockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonNominatedFor(
            entity=mock_person_entity, query=query, entity_type="PERSON"
        )
        events = factory.create_wiki_event()
        assert len(events) == 1
        event = events[0]
        assert (
            event.summary
            == "Morgan Freeman was nominated for the Academy Award for Best Actor by Academy of Motion Picture Arts and Sciences in Los Angeles in 1994."
        )

    def test_create_wiki_event_no_location(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Remove location from qualifiers
        del mock_person_entity.claims["P1411"][0]["qualifiers"]["P276"]

        query = ExtendedMockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonNominatedFor(
            entity=mock_person_entity, query=query, entity_type="PERSON"
        )
        with pytest.raises(UnprocessableEventError):
            factory.create_wiki_event()

    def test_create_wiki_event_no_conferrer(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Remove conferrer from qualifiers
        del mock_person_entity.claims["P1411"][0]["qualifiers"]["P1027"]

        query = ExtendedMockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonNominatedFor(
            entity=mock_person_entity, query=query, entity_type="PERSON"
        )
        events = factory.create_wiki_event()
        assert len(events) == 1
        event = events[0]
        assert (
            event.summary
            == "On March 21, 1994, Morgan Freeman was nominated for the Academy Award for Best Actor in Los Angeles."
        )

    def test_create_wiki_event_no_time(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Remove time from qualifiers
        del mock_person_entity.claims["P1411"][0]["qualifiers"]["P585"]

        query = ExtendedMockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonNominatedFor(
            entity=mock_person_entity, query=query, entity_type="PERSON"
        )
        with pytest.raises(UnprocessableEventError):
            factory.create_wiki_event()

    def test_create_wiki_event_location_from_award(
        self,
        mock_person_entity: Entity,
        mock_location: GeoLocation,
    ) -> None:
        # Remove location from qualifiers but add it to award entity
        del mock_person_entity.claims["P1411"][0]["qualifiers"]["P276"]

        class CustomMockQuery(ExtendedMockQuery):
            def get_entity(self, id: str):
                if id == "Q123":
                    return Entity(
                        id="Q123",
                        pageid=123,
                        ns=0,
                        title="Q123",
                        lastrevid=456,
                        modified="2024-04-05T00:00:00Z",
                        type="item",
                        labels={
                            "en": Property(
                                language="en", value="Academy Award for Best Actor"
                            )
                        },
                        descriptions={
                            "en": Property(language="en", value="Film award")
                        },
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
                return super().get_entity(id)

        query = CustomMockQuery(
            entity_lookup=self.AWARD_ENTITY_LOOKUP,
            geo_location=mock_location,
            expected_geo_location_id="Q456",
        )
        factory = PersonNominatedFor(
            entity=mock_person_entity, query=query, entity_type="PERSON"
        )
        events = factory.create_wiki_event()
        assert len(events) == 1
        event = events[0]
        assert (
            event.summary
            == "On March 21, 1994, Morgan Freeman was nominated for the Academy Award for Best Actor by Academy of Motion Picture Arts and Sciences in Los Angeles."
        )
