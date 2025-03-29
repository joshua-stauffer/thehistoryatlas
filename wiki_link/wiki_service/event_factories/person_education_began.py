from typing import Literal

from wiki_service.event_factories.event_factory import (
    register_event_factory,
    EventFactory,
    UnprocessableEventError,
    WikiEvent,
    PlaceWikiTag,
    PersonWikiTag,
    TimeWikiTag,
)
from wiki_service.event_factories.q_numbers import (
    EDUCATED_AT,
    START_TIME,
    ACADEMIC_MAJOR,
)
from wiki_service.wikidata_query_service import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)
from wiki_service.wikidata_query_service import TimeDefinition


@register_event_factory
class PersonEducationBegan(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person education began"

    def entity_has_event(self) -> bool:
        if EDUCATED_AT not in self._entity.claims:
            return False

        # Check if any EDUCATED_AT claim has a START_TIME qualifier
        for claim in self._entity.claims[EDUCATED_AT]:
            if "qualifiers" in claim and START_TIME in claim["qualifiers"]:
                return True
        return False

    def create_wiki_event(self) -> list[WikiEvent]:
        person_name = self._entity.labels["en"].value
        events = []

        for claim in self._entity.claims[EDUCATED_AT]:
            if "qualifiers" not in claim or START_TIME not in claim["qualifiers"]:
                continue

            institution_id = claim["mainsnak"]["datavalue"]["value"]["id"]
            place_name = self._query.get_label(id=institution_id, language="en")
            geo_location = self._query.get_geo_location(id=institution_id)

            if not geo_location.coordinates and not geo_location.geoshape:
                continue  # Skip if no location found

            time_definition = TimeDefinition(
                id="",
                type="statement",
                rank="normal",
                hash="",
                snaktype="value",
                property=START_TIME,
                time=next(
                    qualifier["datavalue"]["value"]["time"]
                    for qualifier in claim["qualifiers"][START_TIME]
                    if qualifier["property"] == START_TIME
                ),
                timezone=0,
                before=0,
                after=0,
                precision=next(
                    qualifier["datavalue"]["value"]["precision"]
                    for qualifier in claim["qualifiers"][START_TIME]
                    if qualifier["property"] == START_TIME
                ),
                calendarmodel=next(
                    qualifier["datavalue"]["value"]["calendarmodel"]
                    for qualifier in claim["qualifiers"][START_TIME]
                    if qualifier["property"] == START_TIME
                ),
            )
            time_name = wikidata_time_to_text(time_definition)

            # Check for academic major
            academic_major_name = None
            if "qualifiers" in claim and ACADEMIC_MAJOR in claim["qualifiers"]:
                major_id = claim["qualifiers"][ACADEMIC_MAJOR][0]["datavalue"]["value"][
                    "id"
                ]
                academic_major_name = self._query.get_label(id=major_id, language="en")

            summary = self._summary(
                person=person_name,
                place=place_name,
                time=time_name,
                precision=time_definition.precision,
                academic_major=academic_major_name,
            )

            people_tags = [
                PersonWikiTag(
                    name=person_name,
                    wiki_id=self._entity.id,
                    start_char=summary.find(person_name),
                    stop_char=summary.find(person_name) + len(person_name),
                )
            ]

            place_tag = PlaceWikiTag(
                name=place_name,
                wiki_id=institution_id,
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

            events.append(
                WikiEvent(
                    summary=summary,
                    people_tags=people_tags,
                    place_tag=place_tag,
                    time_tag=time_tag,
                )
            )

        return events

    def _summary(
        self,
        person: str,
        place: str,
        time: str,
        precision: Literal[9, 10, 11],
        academic_major: str | None = None,
    ) -> str:
        if academic_major:
            match precision:
                case 11:  # day
                    return f"On {time}, {person} began their studies in {academic_major} at {place}."
                case 10 | 9:  # month or year
                    return f"{person} began their studies in {academic_major} at {place} in {time}."
                case _:
                    raise UnprocessableEventError(
                        f"Unexpected time precision: {precision}"
                    )
        else:
            match precision:
                case 11:  # day
                    return f"On {time}, {person} began their studies at {place}."
                case 10 | 9:  # month or year
                    return f"{person} began their studies at {place} in {time}."
                case _:
                    raise UnprocessableEventError(
                        f"Unexpected time precision: {precision}"
                    )
