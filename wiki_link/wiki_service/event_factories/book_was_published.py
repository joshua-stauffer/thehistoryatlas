"""Event factory for tracking when a book was published."""

from typing import Literal, List

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
    AUTHOR,
    PUBLICATION_DATE,
    COUNTRY_OF_ORIGIN,
    PUBLISHER,
)
from wiki_service.event_factories.utils import (
    build_time_definition_from_claim,
    wikidata_time_to_text,
)


@register_event_factory
class BookWasPublished(EventFactory):
    @property
    def version(self):
        return 0

    @property
    def label(self):
        return "Book was published"

    def entity_has_event(self) -> bool:
        if self._entity_type != "BOOK":
            return False

        # Must have an author
        if AUTHOR not in self._entity.claims:
            return False

        # Must have publication date
        if PUBLICATION_DATE not in self._entity.claims:
            return False

        # Must have country of origin
        if COUNTRY_OF_ORIGIN not in self._entity.claims:
            return False

        return True

    def create_wiki_event(self) -> List[WikiEvent]:
        book_name = self._entity.labels["en"].value
        time_definition = self._time_definition()
        time_name = wikidata_time_to_text(time_definition)

        # Get author information
        author_tags = []
        author_names = []
        for claim in self._entity.claims[AUTHOR]:
            author_id = claim["mainsnak"]["datavalue"]["value"]["id"]
            author_name = self._query.get_label(id=author_id, language="en")
            author_tags.append((author_id, author_name))
            author_names.append(author_name)

        # Get country information
        country_id = self._country_of_origin_id()
        country_name = self._query.get_label(id=country_id, language="en")
        geo_location = self._query.get_geo_location(id=country_id)

        if not geo_location.coordinates and not geo_location.geoshape:
            raise UnprocessableEventError("Location not found")

        # Get publisher information if available
        publisher_name = None
        publisher_id = None
        if PUBLISHER in self._entity.claims and self._entity.claims[PUBLISHER]:
            publisher_id = self._entity.claims[PUBLISHER][0]["mainsnak"]["datavalue"][
                "value"
            ]["id"]
            publisher_name = self._query.get_label(id=publisher_id, language="en")

        # Create summary
        summary = self._summary(
            authors=author_names,
            book=book_name,
            country=country_name,
            time=time_name,
            precision=time_definition.precision,
            publisher=publisher_name,
        )

        # Create people tags
        people_tags = []
        for author_id, author_name in author_tags:
            people_tags.append(
                PersonWikiTag(
                    name=author_name,
                    wiki_id=author_id,
                    start_char=summary.find(author_name),
                    stop_char=summary.find(author_name) + len(author_name),
                )
            )

        place_tag = PlaceWikiTag(
            name=country_name,
            wiki_id=country_id,
            start_char=summary.find(country_name),
            stop_char=summary.find(country_name) + len(country_name),
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
                    "book_name": book_name,
                    "authors": [{"id": id, "name": name} for id, name in author_tags],
                    "publisher": (
                        {"id": publisher_id, "name": publisher_name}
                        if publisher_id
                        else None
                    ),
                    "country": {"id": country_id, "name": country_name},
                    "publication_date": time_definition.model_dump(),
                },
            )
        ]

        return events

    def _country_of_origin_id(self) -> str:
        return self._entity.claims[COUNTRY_OF_ORIGIN][0]["mainsnak"]["datavalue"][
            "value"
        ]["id"]

    def _time_definition(self):
        return build_time_definition_from_claim(
            time_claim=next(
                claim
                for claim in self._entity.claims[PUBLICATION_DATE]
                if claim["mainsnak"]["property"] == PUBLICATION_DATE
            )
        )

    def _summary(
        self,
        authors: List[str],
        book: str,
        country: str,
        time: str,
        precision: Literal[9, 10, 11],
        publisher: str = None,
    ) -> str:
        # Format authors
        if len(authors) == 1:
            author_str = authors[0]
        elif len(authors) == 2:
            author_str = f"{authors[0]} and {authors[1]}"
        else:
            author_str = ", ".join(authors[:-1]) + f", and {authors[-1]}"

        # Add publisher info if available
        publisher_str = f" by {publisher}" if publisher else ""

        # Build summary based on time precision
        match precision:
            case 11:  # day
                return f"On {time}, the book {book} by {author_str} was published{publisher_str} in {country}."
            case 10:  # month
                return f"In {time}, the book {book} by {author_str} was published{publisher_str} in {country}."
            case 9:  # year
                return f"In {time}, the book {book} by {author_str} was published{publisher_str} in {country}."
            case _:
                raise UnprocessableEventError(f"Unexpected time precision: {precision}")
