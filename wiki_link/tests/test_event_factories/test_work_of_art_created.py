from unittest.mock import create_autospec

import pytest

from tests.conftest import MockQuery
from wiki_service.event_factories.event_factory import Query, UnprocessableEventError
from wiki_service.event_factories.work_of_art_created import WorkOfArtCreated
from wiki_service.event_factories.q_numbers import (
    CREATOR,
    INCEPTION,
    LOCATION_OF_CREATION,
    COUNTRY_OF_ORIGIN,
    COMMISSIONED_BY,
)
from wiki_service.wikidata_query_service import (
    Entity,
    GeoLocation,
    CoordinateLocation,
    Property,
)


class TestWorkOfArtCreated:
    MONA_LISA_ENTITY_LOOKUP = {
        "Q762": "Leonardo da Vinci",  # Creator
        "Q90": "Paris",  # Location of creation
        "Q1128785": "Francesco del Giocondo",  # Commissioner
    }

    @pytest.fixture
    def paris_entity(self) -> Entity:
        return Entity(
            id="Q90",
            pageid=90,
            ns=0,
            title="Q90",
            lastrevid=1234567,
            modified="2024-03-30T00:00:00Z",
            type="item",
            labels={"en": Property(language="en", value="Paris")},
            descriptions={"en": Property(language="en", value="Capital of France")},
            aliases={},
            claims={},
            sitelinks={},
        )

    def test_entity_has_event_success(self, mona_lisa_entity: Entity) -> None:
        factory = WorkOfArtCreated(
            entity=mona_lisa_entity,
            query=create_autospec(Query),
            entity_type="WORK_OF_ART",
        )
        assert factory.entity_has_event()

    def test_entity_has_event_failure(self, paris_entity: Entity) -> None:
        factory = WorkOfArtCreated(
            entity=paris_entity, query=create_autospec(Query), entity_type="WORK_OF_ART"
        )
        assert not factory.entity_has_event()

    def test_summary_precision_11(
        self,
        mona_lisa_entity: Entity,
        paris_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.MONA_LISA_ENTITY_LOOKUP,
            geo_location=paris_geo_location,
            expected_geo_location_id="Q90",
        )
        factory = WorkOfArtCreated(
            entity=mona_lisa_entity, query=mock_query, entity_type="WORK_OF_ART"
        )
        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On January 1, 1503, Leonardo da Vinci created the work of art Mona Lisa in Paris, commissioned by Francesco del Giocondo."
        )

    def test_summary_precision_10(
        self,
        mona_lisa_entity_precision_10: Entity,
        paris_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.MONA_LISA_ENTITY_LOOKUP,
            geo_location=paris_geo_location,
            expected_geo_location_id="Q90",
        )
        factory = WorkOfArtCreated(
            entity=mona_lisa_entity_precision_10,
            query=mock_query,
            entity_type="WORK_OF_ART",
        )
        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "Leonardo da Vinci created the work of art Mona Lisa in Paris in January 1503, commissioned by Francesco del Giocondo."
        )

    def test_summary_precision_9(
        self,
        mona_lisa_entity_precision_9: Entity,
        paris_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup=self.MONA_LISA_ENTITY_LOOKUP,
            geo_location=paris_geo_location,
            expected_geo_location_id="Q90",
        )
        factory = WorkOfArtCreated(
            entity=mona_lisa_entity_precision_9,
            query=mock_query,
            entity_type="WORK_OF_ART",
        )
        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "Leonardo da Vinci created the work of art Mona Lisa in Paris in 1503, commissioned by Francesco del Giocondo."
        )

    def test_summary_no_commissioner(
        self,
        mona_lisa_entity_no_commissioner: Entity,
        paris_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup={
                "Q762": "Leonardo da Vinci",  # Creator
                "Q90": "Paris",  # Location of creation
            },
            geo_location=paris_geo_location,
            expected_geo_location_id="Q90",
        )
        factory = WorkOfArtCreated(
            entity=mona_lisa_entity_no_commissioner,
            query=mock_query,
            entity_type="WORK_OF_ART",
        )
        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On January 1, 1503, Leonardo da Vinci created the work of art Mona Lisa in Paris."
        )

    def test_summary_multiple_commissioners(
        self,
        mona_lisa_entity_multiple_commissioners: Entity,
        paris_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup={
                "Q762": "Leonardo da Vinci",  # Creator
                "Q90": "Paris",  # Location of creation
                "Q1128785": "Francesco del Giocondo",  # First commissioner
                "Q123456": "Isabella d'Este",  # Second commissioner
            },
            geo_location=paris_geo_location,
            expected_geo_location_id="Q90",
        )
        factory = WorkOfArtCreated(
            entity=mona_lisa_entity_multiple_commissioners,
            query=mock_query,
            entity_type="WORK_OF_ART",
        )
        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On January 1, 1503, Leonardo da Vinci created the work of art Mona Lisa in Paris, commissioned by Francesco del Giocondo and Isabella d'Este."
        )

    def test_country_of_origin_fallback(
        self,
        mona_lisa_entity_country_only: Entity,
        france_geo_location: GeoLocation,
    ) -> None:
        mock_query = MockQuery(
            entity_lookup={
                "Q762": "Leonardo da Vinci",  # Creator
                "Q142": "France",  # Country of origin
            },
            geo_location=france_geo_location,
            expected_geo_location_id="Q142",
        )
        factory = WorkOfArtCreated(
            entity=mona_lisa_entity_country_only,
            query=mock_query,
            entity_type="WORK_OF_ART",
        )
        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "On January 1, 1503, Leonardo da Vinci created the work of art Mona Lisa in France."
        )

    def test_starry_night(self, starry_night_entity: Entity) -> None:
        mock_query = MockQuery(
            entity_lookup={
                "Q5582": "Vincent van Gogh",  # Creator
                "Q273561": "Saint-Rémy-de-Provence",  # Location of creation
            },
            geo_location=GeoLocation(
                coordinates=CoordinateLocation(
                    id="Q273561$COORDINATE_ID",
                    rank="normal",
                    type="statement",
                    snaktype="value",
                    property="P625",
                    hash="some_hash",
                    latitude=43.7892,
                    longitude=4.8313,
                    altitude=None,
                    precision=0.0001,
                    globe="http://www.wikidata.org/entity/Q2",
                ),
                geoshape=None,
            ),
            expected_geo_location_id="Q273561",
        )
        factory = WorkOfArtCreated(
            entity=starry_night_entity, query=mock_query, entity_type="WORK_OF_ART"
        )
        wiki_events = factory.create_wiki_event()
        assert len(wiki_events) == 1
        wiki_event = wiki_events[0]
        assert (
            wiki_event.summary
            == "Vincent van Gogh created the work of art The Starry Night in Saint-Rémy-de-Provence in June 1889."
        )
