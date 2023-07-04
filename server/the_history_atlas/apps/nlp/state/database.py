from collections import namedtuple
import logging
from typing import Union, get_args, Literal
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.nlp.state.schema import AnnotatedCitation
from the_history_atlas.apps.nlp.state.schema import Base
from the_history_atlas.apps.nlp.state.schema import Entity

from the_history_atlas.apps.domain.models import (
    CitationAdded,
    PersonAdded,
    PersonTagged,
    PlaceAdded,
    PlaceTagged,
    TimeAdded,
    TimeTagged,
)
from the_history_atlas.apps.domain.types import Event


log = logging.getLogger(__name__)

CitationEntry = namedtuple("AnnotatedCitation", ["text", "entities"])
TaggedEntity = Union[
    PersonAdded, PersonTagged, PlaceAdded, PlaceTagged, TimeAdded, TimeTagged
]


class Database:
    def __init__(self, client: DatabaseClient):
        # initialize the db
        self._engine = client
        Base.metadata.create_all(self._engine)
        self.Session = sessionmaker(bind=self._engine)

    def get_training_corpus(self):
        """"""
        # might make sense to make this into a generator at some point
        res = list()
        with self.Session() as session:
            citations = session.execute(select(AnnotatedCitation)).scalars()
            for citation in citations:
                text = citation.text
                entities = [
                    (e.start_char, e.stop_char, e.type) for e in citation.entities
                ]
                res.append(CitationEntry(text, entities))
        return res

    def handle_event(self, event: Event):
        """Process an emitted event and save it to the database"""

        if isinstance(event, CitationAdded):
            self._handle_citation_added(event)
        elif type(event) in get_args(TaggedEntity):
            self._handle_entity_tagged(event)
        else:
            pass

    def _handle_citation_added(self, event: CitationAdded) -> None:
        """Persist citation text"""
        citation_id = UUID(event.payload.id)
        with self.Session() as session:
            stmt = text(
                """
                insert into annotated_citations (id, text)
                values (:id, :text)
            """
            )
            session.execute(stmt, {"id": citation_id, "text": event.payload.text})
            session.commit()

    def _handle_entity_tagged(self, event: TaggedEntity) -> None:
        """Persist a tag"""
        type_: Literal["PERSON", "PLACE", "TIME"]
        if type(event) in (PersonAdded, PersonTagged):
            type_ = "PERSON"
        elif type(event) in (PlaceAdded, PlaceTagged):
            type_ = "PLACE"
        elif type(event) in (TimeAdded, TimeTagged):
            type_ = "TIME"
        else:
            raise Exception(f"Cannot handle unknown event type: {type(event)}")
        entity_id = UUID(event.payload.id)

        with self.Session() as session:
            entity = {
                "id": entity_id,
                "type": type_,
                "start_char": event.payload.citation_start,
                "stop_char": event.payload.citation_end,
                "annotated_citation_id": UUID(event.payload.citation_id),
            }
            stmt = text(
                """
                insert into entities (id, type, start_char, stop_char, annotated_citation_id)
                    values (:id, :type, :start_char, :stop_char, :annotated_citation_id)
            """
            )

            # NOTE: if events have been received out of order, it's possible
            #       that the citation doesn't yet exist, and this will error.
            #       Not mission critical to have all the data, so allowing.
            try:
                session.execute(stmt, entity)
                session.commit()
            except IntegrityError as e:
                log.error(f"Encountered error while persisting Entity: {e}")
