"""Event factory for tracking when a work of art was created."""

from typing import Literal

from wiki_service.event_factories.event_factory import (
    EventFactory,
    UnprocessableEventError,
    register_event_factory,
)
from wiki_service.types import (
    WikiEvent,
    PersonWikiTag,
    PlaceWikiTag,
    TimeWikiTag,
)
from wiki_service.event_factories.q_numbers import (
    CREATOR,
    INCEPTION,
    LOCATION_OF_CREATION,
    COUNTRY_OF_ORIGIN,
    COMMISSIONED_BY,
)
from wiki_service.event_factories.utils import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)


@register_event_factory
class WorkOfArtCreated(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Work of art created"

    def entity_has_event(self) -> bool:
        if self._entity_type != "WORK_OF_ART":
            return False

        # Must have a creator
        if CREATOR not in self._entity.claims:
            return False

        # Must have inception date
        if INCEPTION not in self._entity.claims:
            return False

        # Must have either location of creation or country of origin
        if (
            LOCATION_OF_CREATION not in self._entity.claims
            and COUNTRY_OF_ORIGIN not in self._entity.claims
        ):
            return False

        return True

    def _create_events(self) -> list[WikiEvent]:
        artwork_name = self._entity.labels["en"].value
        time_definition = self._time_definition()
        time_name = wikidata_time_to_text(time_definition)

        # Get creator information
        creator_id = self._creator_id()
        creator_name = self._query.get_label(id=creator_id, language="en")

        # Get location information - prefer location of creation over country of origin
        location_id = None
        if LOCATION_OF_CREATION in self._entity.claims:
            location_id = self._location_of_creation_id()
        else:
            location_id = self._country_of_origin_id()

        place_name = self._query.get_label(id=location_id, language="en")
        geo_location = self._query.get_geo_location(id=location_id)

        if not geo_location.coordinates and not geo_location.geoshape:
            raise UnprocessableEventError("Location not found")

        # Get commissioner information if available
        commissioner_tuples = []
        if (
            COMMISSIONED_BY in self._entity.claims
            and self._entity.claims[COMMISSIONED_BY]
        ):
            for claim in self._entity.claims[COMMISSIONED_BY]:
                commissioner_id = claim["mainsnak"]["datavalue"]["value"]["id"]
                commissioner_name = self._query.get_label(
                    id=commissioner_id, language="en"
                )
                commissioner_tuples.append((commissioner_id, commissioner_name))

        # Create summary
        summary = self._summary(
            creator=creator_name,
            artwork=artwork_name,
            place=place_name,
            time=time_name,
            precision=time_definition.precision,
            commissioners=commissioner_tuples if commissioner_tuples else None,
        )

        # Create people tags
        people_tags = [
            PersonWikiTag(
                name=creator_name,
                wiki_id=creator_id,
                start_char=summary.find(creator_name),
                stop_char=summary.find(creator_name) + len(creator_name),
            )
        ]

        if commissioner_tuples:
            for commissioner_id, commissioner_name in commissioner_tuples:
                people_tags.append(
                    PersonWikiTag(
                        name=commissioner_name,
                        wiki_id=commissioner_id,
                        start_char=summary.find(commissioner_name),
                        stop_char=summary.find(commissioner_name)
                        + len(commissioner_name),
                    )
                )

        place_tag = PlaceWikiTag(
            name=place_name,
            wiki_id=location_id,
            start_char=summary.find(place_name),
            stop_char=summary.find(place_name) + len(place_name),
            location=geo_location,
        )

        time_tag = TimeWikiTag(
            name=time_name,
            wiki_id=None,
            start_char=summary.find(time_name),
            stop_char=summary.find(time_name) + len(time_name),
            time_definition=time_definition,
        )

        events = [
            WikiEvent(
                summary=summary,
                people_tags=people_tags,
                place_tag=place_tag,
                time_tag=time_tag,
                entity_id=self._entity_id,
                secondary_entity_id=None,
                context={
                    **self._create_base_context(),
                    "artwork_name": artwork_name,
                    "creator": {"id": creator_id, "name": creator_name},
                    "location": {"id": location_id, "name": place_name},
                    "commissioners": (
                        [{"id": id, "name": name} for id, name in commissioner_tuples]
                        if commissioner_tuples
                        else None
                    ),
                    "creation_date": time_definition.model_dump(),
                    "is_location_of_creation": LOCATION_OF_CREATION
                    in self._entity.claims,
                },
            )
        ]

        return events

    def _creator_id(self) -> str:
        return self._entity.claims[CREATOR][0]["mainsnak"]["datavalue"]["value"]["id"]

    def _location_of_creation_id(self) -> str:
        return self._entity.claims[LOCATION_OF_CREATION][0]["mainsnak"]["datavalue"][
            "value"
        ]["id"]

    def _country_of_origin_id(self) -> str:
        return self._entity.claims[COUNTRY_OF_ORIGIN][0]["mainsnak"]["datavalue"][
            "value"
        ]["id"]

    def _time_definition(self):
        return build_time_definition_from_claim(
            time_claim=next(
                claim
                for claim in self._entity.claims[INCEPTION]
                if claim["mainsnak"]["property"] == INCEPTION
            )
        )

    def _summary(
        self,
        creator: str,
        artwork: str,
        place: str,
        time: str,
        precision: Literal[9, 10, 11],
        commissioners: list[tuple[str, str]] = None,
    ) -> str:
        # Build commissioner string if present
        commissioner_str = ""
        if commissioners:
            commissioner_names = [name for _, name in commissioners]
            if len(commissioner_names) == 1:
                commissioner_str = f", commissioned by {commissioner_names[0]}"
            else:
                commissioner_str = (
                    f", commissioned by {' and '.join(commissioner_names)}"
                )

        # Build summary based on time precision
        match precision:
            case 11:  # day
                return f"On {time}, {creator} created the work of art {artwork} in {place}{commissioner_str}."
            case 10 | 9:  # month or year
                return f"{creator} created the work of art {artwork} in {place} in {time}{commissioner_str}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
