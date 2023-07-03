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
from the_history_atlas.apps.domain.models.readmodel.tables import PersonModel
from the_history_atlas.apps.domain.types import Event
from the_history_atlas.apps.readmodel.errors import (
    UnknownEventError,
    DuplicateEventError,
)

log = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, database_instance):
        self._db = database_instance
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
        self._db.update_last_event_id(event.index)
        self._event_id_set.add(event.index)

    def _map_event_handlers(self):
        """A dict of known event types and the methods which process them"""
        return {
            "SUMMARY_ADDED": self._handle_summary_added,
            "SUMMARY_TAGGED": self._handle_summary_tagged,
            "CITATION_ADDED": self._handle_citation_added,
            "PERSON_ADDED": self._handle_person_added,
            "PLACE_ADDED": self._handle_place_added,
            "TIME_ADDED": self._handle_time_added,
            "PERSON_TAGGED": self._handle_person_tagged,
            "PLACE_TAGGED": self._handle_place_tagged,
            "TIME_TAGGED": self._handle_time_tagged,
            "META_ADDED": self._handle_meta_added,
            "META_TAGGED": self._handle_meta_tagged,
        }

    def _handle_summary_added(self, event: SummaryAdded):
        id = UUID(event.payload.id)
        text = event.payload.text
        self._db.create_summary(id=id, text=text)

    def _handle_summary_tagged(self, event: SummaryTagged):
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

    def _handle_citation_added(self, event: CitationAdded):
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

    def _handle_person_added(self, event: PersonAdded):
        self._db.handle_person_update(
            person_id=UUID(event.payload.id),
            summary_id=UUID(event.payload.summary_id),
            person_name=event.payload.name,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
        )

    def _handle_person_tagged(self, event: PersonTagged):
        self._db.handle_person_update(
            person_id=UUID(event.payload.id),
            summary_id=UUID(event.payload.summary_id),
            person_name=event.payload.name,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
        )

    def _handle_place_added(self, event: PlaceAdded):
        self._db.handle_place_update(
            place_id=UUID(event.payload.id),
            summary_id=UUID(event.payload.summary_id),
            place_name=event.payload.name,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
            latitude=event.payload.latitude,
            longitude=event.payload.longitude,
            geoshape=event.payload.geo_shape,
            geonames_id=None,  # todo
        )

    def _handle_place_tagged(self, event: PlaceTagged):
        self._db.handle_place_update(
            place_id=UUID(event.payload.id),
            summary_id=UUID(event.payload.summary_id),
            place_name=event.payload.name,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
            geonames_id=None,  # todo
        )

    def _handle_time_added(self, event: TimeAdded):
        self._db.handle_time_update(
            time_id=UUID(event.payload.id),
            summary_id=UUID(event.payload.summary_id),
            time_name=event.payload.name,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
            time=datetime(year=1685, month=1, day=1, tzinfo=timezone.utc),  # todo
            calendar_model="http://www.wikidata.org/entity/Q1985727",
            precision=9,
        )

    def _handle_time_tagged(self, event: TimeTagged):
        self._db.handle_time_update(
            time_id=UUID(event.payload.id),
            summary_id=UUID(event.payload.summary_id),
            time_name=event.payload.name,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
        )

    def _handle_meta_added(self, event: MetaAdded):
        source = event.payload
        self._db.create_source(
            id=source.id,
            title=source.title,
            author=source.author,
            publisher=source.publisher,
            pub_date=source.pub_date,
            citation_id=source.citation_id,
        )

    def _handle_meta_tagged(self, event: MetaTagged):
        self._db.add_source_to_citation(
            source_id=event.payload.id, citation_id=event.payload.citation_id
        )
