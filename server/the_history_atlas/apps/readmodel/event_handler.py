import logging
from datetime import datetime, timezone
from typing import Union
from uuid import UUID

from sqlalchemy.exc import IntegrityError

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
from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.errors import (
    UnknownEventError,
    DuplicateEventError,
)
from the_history_atlas.apps.readmodel.trie import Trie

log = logging.getLogger(__name__)


class EventHandler:
    def __init__(
        self, database_instance: Database, source_trie: Trie, entity_trie: Trie
    ):
        self._db = database_instance
        self._source_trie = source_trie
        self._entity_trie = entity_trie
        self._event_handlers = self._map_event_handlers()
        self._event_id_set = set()

    def handle_event(self, event: Event):
        """Process an incoming event and persist it to the database"""

        if event.index in self._event_id_set:
            log.info(
                f"Discarding malformed or duplicate message with event_id {event.index}."
            )
            raise DuplicateEventError

        handler = self._event_handlers.get(event.type)
        if not handler:
            raise UnknownEventError(event.type)
        handler(event)
        # update our record of the latest handled event
        self._event_id_set.add(event.index)

    def _map_event_handlers(self):
        """A dict of known event types and the methods which process them"""
        return {
            "SUMMARY_ADDED": self.summary_added,
            "SUMMARY_TAGGED": self.summary_tagged,
            "CITATION_ADDED": self.citation_added,
            "PERSON_ADDED": self.person_added,
            "PLACE_ADDED": self.place_added,
            "TIME_ADDED": self.time_added,
            "PERSON_TAGGED": self.person_tagged,
            "PLACE_TAGGED": self.place_tagged,
            "TIME_TAGGED": self.time_tagged,
            "META_ADDED": self.meta_added,
            "META_TAGGED": self.meta_tagged,
        }

    def summary_added(self, event: SummaryAdded):
        id = UUID(event.payload.id)
        text = event.payload.text
        self._db.create_summary(id=id, text=text)

    def summary_tagged(self, event: SummaryTagged):
        session = self._db.session()
        self._db.create_citation_summary_fkey(
            session=session,
            citation_id=event.payload.citation_id,
            summary_id=event.payload.id,
        )
        try:
            session.commit()
        except IntegrityError:
            pass

    def citation_added(self, event: CitationAdded):
        id = UUID(event.payload.id)
        summary_id = UUID(event.payload.summary_id)
        text = event.payload.text
        with self._db.Session() as session:
            self._db.create_citation(
                session=session,
                id=id,
                citation_text=text,
                page_num=event.payload.page_num,
                access_date=event.payload.access_date,
            )
            session.commit()
            self._db.create_citation_summary_fkey(
                session=session, citation_id=id, summary_id=summary_id
            )
            try:
                session.commit()
            except IntegrityError:
                pass

    def person_added(self, event: PersonAdded):
        person_id = UUID(event.payload.id)
        summary_id = UUID(event.payload.summary_id)
        person_name = event.payload.name
        start_char = event.payload.citation_start
        stop_char = event.payload.citation_end

        with self._db.Session() as session:
            person = self._db.create_person(id=person_id, session=session)
            self._db.add_name_to_tag(
                name=person_name, tag_id=person.id, session=session
            )
            self._db.update_entity_trie(
                new_string=person_name, new_string_guid=str(person.id)
            )
            self._db.create_tag_instance(
                tag_id=person.id,
                summary_id=summary_id,
                start_char=start_char,
                stop_char=stop_char,
                session=session,
            )
            session.commit()

    def person_tagged(self, event: PersonTagged):
        person_id = UUID(event.payload.id)
        summary_id = UUID(event.payload.summary_id)
        person_name = event.payload.name
        start_char = event.payload.citation_start
        stop_char = event.payload.citation_end

        with self._db.Session() as session:
            person = self._db.get_person_by_id(id=person_id, session=session)
            if person is None:
                raise Exception("Tagged person does not exist.")
            self._db.add_name_to_tag(
                name=person_name, tag_id=person.id, session=session
            )
            self._db.update_entity_trie(
                new_string=person_name, new_string_guid=str(person.id)
            )
            self._db.create_tag_instance(
                tag_id=person.id,
                summary_id=summary_id,
                start_char=start_char,
                stop_char=stop_char,
                session=session,
            )
            session.commit()

    def place_added(self, event: PlaceAdded):
        place_id = UUID(event.payload.id)
        summary_id = UUID(event.payload.summary_id)
        place_name = event.payload.name
        start_char = event.payload.citation_start
        stop_char = event.payload.citation_end
        latitude = event.payload.latitude
        longitude = event.payload.longitude
        geoshape = event.payload.geo_shape
        geonames_id = None  # todo

        with self._db.Session() as session:
            place = self._db.create_place(
                session=session,
                id=place_id,
                latitude=latitude,
                longitude=longitude,
                geoshape=geoshape,
                geonames_id=geonames_id,
            )
            self._db.add_name_to_tag(name=place_name, tag_id=place.id, session=session)
            self._db.update_entity_trie(
                new_string=place_name, new_string_guid=str(place.id)
            )
            self._db.create_tag_instance(
                tag_id=place.id,
                summary_id=summary_id,
                start_char=start_char,
                stop_char=stop_char,
                session=session,
            )
            session.commit()

    def place_tagged(self, event: PlaceTagged):
        place_id = UUID(event.payload.id)
        summary_id = UUID(event.payload.summary_id)
        place_name = event.payload.name
        start_char = event.payload.citation_start
        stop_char = event.payload.citation_end

        with self._db.Session() as session:
            place = self._db.get_place_by_id(id=place_id, session=session)

            if place is None:
                raise Exception("Tagged place does not exist.")

            self._db.add_name_to_tag(name=place_name, tag_id=place.id, session=session)
            self._db.update_entity_trie(
                new_string=place_name, new_string_guid=str(place.id)
            )
            self._db.create_tag_instance(
                tag_id=place.id,
                summary_id=summary_id,
                start_char=start_char,
                stop_char=stop_char,
                session=session,
            )
            session.commit()

    def time_added(self, event: TimeAdded):
        time_id = UUID(event.payload.id)
        summary_id = UUID(event.payload.summary_id)
        time_name = event.payload.name
        start_char = event.payload.citation_start
        stop_char = event.payload.citation_end

        # todo: add to event object
        time = datetime(year=1685, month=1, day=1, tzinfo=timezone.utc)
        calendar_model = "http://www.wikidata.org/entity/Q1985727"
        precision = 9

        with self._db.Session() as session:
            time_model = self._db.create_time(
                id=time_id,
                time=time,
                calendar_model=calendar_model,
                precision=precision,
                session=session,
            )
            self._db.add_name_to_tag(
                name=time_name, tag_id=time_model.id, session=session
            )
            self._db.update_entity_trie(
                new_string=time_name, new_string_guid=str(time_model.id)
            )
            self._db.create_tag_instance(
                tag_id=time_model.id,
                summary_id=summary_id,
                start_char=start_char,
                stop_char=stop_char,
                session=session,
            )
            session.commit()

    def time_tagged(self, event: TimeTagged):
        time_id = UUID(event.payload.id)
        summary_id = UUID(event.payload.summary_id)
        time_name = event.payload.name
        start_char = event.payload.citation_start
        stop_char = event.payload.citation_end

        with self._db.Session() as session:
            time_model = self._db.get_time_by_id(id=time_id, session=session)
            if time_model is None:
                raise Exception("Tagged time does not exist.")

            self._db.add_name_to_tag(
                name=time_name, tag_id=time_model.id, session=session
            )
            self._db.update_entity_trie(
                new_string=time_name, new_string_guid=str(time_model.id)
            )
            self._db.create_tag_instance(
                tag_id=time_model.id,
                summary_id=summary_id,
                start_char=start_char,
                stop_char=stop_char,
                session=session,
            )
            session.commit()

    def meta_added(self, event: MetaAdded):
        source = event.payload
        self._db.create_source(
            id=source.id,
            title=source.title,
            author=source.author,
            publisher=source.publisher,
            pub_date=source.pub_date,
            citation_id=source.citation_id,
        )

    def meta_tagged(self, event: MetaTagged):
        with self._db.Session() as session:
            self._db.create_citation_source_fkey(
                source_id=event.payload.id,
                citation_id=event.payload.citation_id,
                session=session,
            )
            session.commit()
