"""SQLAlchemy integration for the History Atlas NLP service.
Stores annotations for training model.
"""
from collections import namedtuple
import logging
import json
import os
from typing import Union, get_args, Literal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from nlp_service.state.schema import AnnotatedCitation
from nlp_service.state.schema import Base
from nlp_service.state.schema import Entity

from abstract_domain_model.models import (
    CitationAdded,
    PersonAdded,
    PersonTagged,
    PlaceAdded,
    PlaceTagged,
    TimeAdded,
    TimeTagged,
)
from abstract_domain_model.types import Event


log = logging.getLogger(__name__)

CitationEntry = namedtuple("AnnotatedCitation", ["text", "entities"])
TaggedEntity = Union[
    PersonAdded, PersonTagged, PlaceAdded, PlaceTagged, TimeAdded, TimeTagged
]


class Database:
    def __init__(self, config):
        self._config = config
        self._engine = create_engine(config.DB_URI, echo=config.DEBUG, future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)

    def get_training_corpus(self):
        """"""
        # might make sense to make this into a generator at some point
        res = list()
        with Session(self._engine, future=True) as session:
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
        citation = AnnotatedCitation(id=event.payload.id, text=event.payload.text)
        with Session(self._engine, future=True) as session:
            session.add(citation)
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
        entity = Entity(
            id=event.payload.id,
            type=type_,
            start_char=event.payload.citation_start,
            stop_char=event.payload.citation_end,
            annotated_citation_id=event.payload.citation_id,
        )
        with Session(self._engine, future=True) as session:
            # NOTE: if events have been received out of order, it's possible
            #       that the citation doesn't yet exist, and this will error.
            #       Not mission critical to have all the data, so allowing.
            try:
                session.add(entity)
                session.commit()
            except IntegrityError as e:
                log.error(f"Encountered error while persisting Entity: {e}")
