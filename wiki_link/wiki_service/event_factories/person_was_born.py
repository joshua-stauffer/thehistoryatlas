from typing import Literal

from pydantic import BaseModel, Field

from wiki_service.event_factories.event_factory import (
    register_event_factory,
    EventFactory,
    WikiTag,
    UnprocessableEventError,
    WikiEvent,
    PlaceWikiTag,
    PersonWikiTag,
    TimeWikiTag, WikidataValue,
)
from wiki_service.event_factories.q_numbers import (
    PLACE_OF_BIRTH,
    DATE_OF_BIRTH,
    COORDINATE_LOCATION,
)
from wiki_service.wikidata_query_service import (
    build_time_definition_from_claim,
    TimeDefinition,
    Entity,
    build_coordinate_location,
    wikidata_time_to_text,
)


class PersonWasBornQueryResult(BaseModel):
    dob: WikidataValue
    precision: WikidataValue
    lat: WikidataValue
    lon: WikidataValue
    person: WikidataValue
    person_description: WikidataValue = Field(alias="personDescription")
    person_label: WikidataValue = Field(alias="personLabel")
    place_of_birth: WikidataValue = Field(alias="placeOfBirth")
    place_of_birth_label: WikidataValue = Field(alias="placeOfBirthLabel")

    mother: WikidataValue | None = None
    mother_description: WikidataValue | None = Field(None, alias="motherDescription")
    mother_label: WikidataValue | None = Field(None, alias="motherLabel")
    father: WikidataValue | None = None
    father_description: WikidataValue | None = Field(None, alias="fatherDescription")
    father_label: WikidataValue | None = Field(None, alias="fatherLabel")
    geo_shape: WikidataValue | None = Field(None, alias="geoShape")



@register_event_factory
class PersonWasBorn(EventFactory[PersonWasBornQueryResult]):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Person was born"

    def query(self, limit: int, offset: int) -> str:
        return f"""
        SELECT 
          ?person ?personLabel ?personDescription 
          ?placeOfBirth ?placeOfBirthLabel ?lat ?lon ?geoShape 
          ?dobStatement ?dob ?precision ?calendarModel ?before ?after 
          ?father ?fatherLabel ?fatherDescription 
          ?mother ?motherLabel ?motherDescription
        WHERE {{
          {{
            # First, restrict to humans (Q5) with a date and place of birth.
            SELECT ?person ?dob ?placeOfBirth ?precision WHERE {{
              ?person wdt:P31 wd:Q5;
                      p:P569/psv:P569 [ wikibase:timeValue ?dob; wikibase:timePrecision ?precision ];
                      wdt:P19 ?placeOfBirth.
            }}
            LIMIT {limit}
            OFFSET {offset}
          }}
          
          # Retrieve the full date-of-birth statement so that we can extract qualifiers.

          
          # For the place of birth, retrieve coordinates using the simpler truthy property.
          OPTIONAL {{
            ?placeOfBirth wdt:P625 ?coordinate.
            BIND(geof:latitude(?coordinate) AS ?lat)
            BIND(geof:longitude(?coordinate) AS ?lon)
          }}
          
          # Retrieve the geoshape if available.
          OPTIONAL {{ ?placeOfBirth wdt:P3896 ?geoShape. }}
          
          # Optionally retrieve father and mother.
          OPTIONAL {{ ?person wdt:P22 ?father. }}
          OPTIONAL {{ ?person wdt:P25 ?mother. }}
          
          # Get English labels and descriptions.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """

    @property
    def QueryResult(self) -> type[PersonWasBornQueryResult]:
        return PersonWasBornQueryResult

    def create_wiki_event(self, query_result: PersonWasBornQueryResult) -> WikiEvent:
        person_name = query_result.person_label.value
        place_name = query_result.place_of_birth.value
        time_name = wikidata_time_to_text(
            time=query_result.dob,
            precision=query_result.precision.value,
        )

        summary = self._summary(
            person=person_name,
            place=place_name,
            time=time_name,
            precision=query_result.precision.value,
        )
        person_tag = PersonWikiTag(
            name=person_name,
            wiki_id=query_result.person.value,
            start_char=summary.find(person_name),
            stop_char=summary.find(person_name) + len(person_name),
        )
        place_tag = PlaceWikiTag(
            name=place_name,
            wiki_id=place_entity.id,
            start_char=summary.find(place_name),
            stop_char=summary.find(place_name) + len(place_name),
            location=coordinate_location,
            entity=place_entity,
        )
        time_tag = TimeWikiTag(
            name=time_name,
            wiki_id=None,
            start_char=summary.find(time_name),
            stop_char=summary.find(time_name) + len(time_name),
            entity=None,
            time_definition=time_definition,
        )
        return WikiEvent(
            summary=summary,
            people_tags=[person_tag],
            place_tag=place_tag,
            time_tag=time_tag,
        )

    def _place_of_birth_id(self) -> str:
        return self._entity.claims[PLACE_OF_BIRTH][0]["mainsnak"]["datavalue"]["value"][
            "id"
        ]

    def _time_definition(self):
        return build_time_definition_from_claim(
            time_claim=next(
                claim
                for claim in self._entity.claims[DATE_OF_BIRTH]
                if claim["mainsnak"]["property"] == DATE_OF_BIRTH
            )
        )

    def _summary(
        self, person: str, place: str, time: str, precision: Literal[9, 10, 11]
    ) -> str:
        match precision:
            case 11:  # day
                return f"On {time}, {person} was born in {place}."
            case 10 | 9:  # month or year
                return f"{person} was born in {time} in {place}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
