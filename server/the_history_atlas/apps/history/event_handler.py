import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from the_history_atlas.apps.domain.core import (
    PersonInput,
    Person,
    PlaceInput,
    Place,
    TimeInput,
    Time,
    TagInstance,
    CitationInput,
    StoryName,
)
from the_history_atlas.apps.domain.models import (
    SummaryAdded,
    SummaryTagged,
    CitationAdded,
    PersonAdded,
    PersonTagged,
    PlaceAdded,
    PlaceTagged,
    TimeAdded,
    TimeTagged,
    MetaAdded,
)
from the_history_atlas.apps.domain.models.events.meta_tagged import MetaTagged
from the_history_atlas.apps.domain.types import Event
from the_history_atlas.apps.history.database import Database
from the_history_atlas.apps.history.errors import (
    UnknownEventError,
    DuplicateEventError,
    TagExistsError,
)
from the_history_atlas.apps.history.trie import Trie

log = logging.getLogger(__name__)


class EventHandler:
    def __init__(
        self, database_instance: Database, source_trie: Trie, entity_trie: Trie
    ):
        self._db = database_instance
        self._source_trie = source_trie
        self._entity_trie = entity_trie

    def create_wikidata_event(
        self,
        text: str,
        tags: list[TagInstance],
        citation: CitationInput,
    ) -> UUID:
        source = self._db.get_source_by_title(title="Wikidata")
        if source:
            source_id = UUID(source.id)
        else:
            source_id = uuid4()
            self._db.create_source(
                id=source_id,
                title="Wikidata",
                author="Wikidata Contributors",
                publisher="Wikimedia Foundation",
                pub_date=str(datetime.now(timezone.utc)),
            )
        summary_id = uuid4()

        with self._db.Session() as session:
            self._db.create_summary(
                id=summary_id,
                text=text,
            )
            citation_text = f"Wikidata. ({citation.access_date}). {citation.wikidata_item_title} ({citation.wikidata_item_id}). Wikimedia Foundation. {citation.wikidata_item_url}"
            citation_id = uuid4()
            self._db.create_citation(
                id=citation_id,
                session=session,
                citation_text=citation_text,
                access_date=str(citation.access_date),
            )
            self._db.create_citation_source_fkey(
                session=session,
                citation_id=citation_id,
                source_id=source_id,
            )
            self._db.create_citation_summary_fkey(
                session=session,
                citation_id=citation_id,
                summary_id=summary_id,
            )
            tag_instance_time, precision = self._db.get_time_and_precision_by_tags(
                session=session,
                tag_ids=[tag.id for tag in tags],
            )
            for tag in tags:
                self._db.create_tag_instance(
                    start_char=tag.start_char,
                    stop_char=tag.stop_char,
                    summary_id=summary_id,
                    tag_id=tag.id,
                    tag_instance_time=tag_instance_time,
                    time_precision=precision,
                    session=session,
                )
            session.commit()
        return summary_id

    def create_person(self, person: PersonInput) -> Person:
        if self._db.get_tag_id_by_wikidata_id(wikidata_id=person.wikidata_id):
            raise TagExistsError(
                f"Person with wikidata id {person.wikidata_id} already exists."
            )
        id = uuid4()
        with self._db.Session() as session:
            self._db.create_person(
                id=id,
                session=session,
                wikidata_id=person.wikidata_id,
                wikidata_url=person.wikidata_url,
            )
            self._db.add_name_to_tag(name=person.name, tag_id=id, session=session)
            self._db.update_entity_trie(new_string=person.name, new_string_guid=str(id))
            self._db.add_story_names(
                tag_id=id,
                session=session,
                story_names=self.get_available_person_story_names(name=person.name),
            )
            session.commit()
        return Person(id=id, **person.model_dump())

    def get_available_person_story_names(self, name: str) -> list[StoryName]:
        return [
            StoryName(lang="en", name=f"The Life of {name}"),
        ]

    def create_place(self, place: PlaceInput) -> Place:
        if self._db.get_tag_id_by_wikidata_id(wikidata_id=place.wikidata_id):
            raise TagExistsError(
                f"Place with wikidata id {place.wikidata_id} already exists."
            )
        id = uuid4()
        with self._db.Session() as session:
            self._db.create_place(
                id=id,
                session=session,
                wikidata_id=place.wikidata_id,
                wikidata_url=place.wikidata_url,
                latitude=place.latitude,
                longitude=place.longitude,
            )
            self._db.add_name_to_tag(name=place.name, tag_id=id, session=session)
            self._db.update_entity_trie(new_string=place.name, new_string_guid=str(id))
            self._db.add_story_names(
                tag_id=id,
                session=session,
                story_names=self.get_available_place_story_names(name=place.name),
            )
            session.commit()
        return Place(id=id, **place.model_dump())

    def get_available_place_story_names(self, name: str) -> list[StoryName]:
        return [
            StoryName(lang="en", name=f"The History of {name}"),
        ]

    def create_time(self, time: TimeInput) -> Time:
        if self._db.get_tag_id_by_wikidata_id(wikidata_id=time.wikidata_id):
            raise TagExistsError(
                f"Place with wikidata id {time.wikidata_id} already exists."
            )
        id = uuid4()
        with self._db.Session() as session:
            self._db.create_time(
                id=id,
                session=session,
                wikidata_id=time.wikidata_id,
                wikidata_url=time.wikidata_url,
                time=time.date,
                calendar_model=time.calendar_model,
                precision=time.precision,
            )
            self._db.add_name_to_tag(name=time.name, tag_id=id, session=session)
            self._db.update_entity_trie(new_string=time.name, new_string_guid=str(id))
            self._db.add_story_names(
                tag_id=id,
                session=session,
                story_names=self.get_available_time_story_names(name=time.name),
            )
            session.commit()
        return Time(id=id, **time.model_dump())

    def get_available_time_story_names(self, name: str) -> list[StoryName]:
        return [
            StoryName(lang="en", name=f"Events of {name}"),
        ]
