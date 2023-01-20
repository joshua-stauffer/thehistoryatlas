import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from wiki_service.schema import Base, WikiQueue
from wiki_service.schema import IDLookup
from wiki_service.types import WikiType, EntityType

log = logging.getLogger(__name__)


class DatabaseError(Exception):
    ...


@dataclass
class Item:
    wiki_id: str
    wiki_type: WikiType
    entity_type: EntityType


class Database:
    def __init__(self, config):
        self._engine = create_engine(config.DB_URI, echo=config.DEBUG, future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)

    def add_wiki_entry(
        self,
        wiki_id: str,
        wiki_type: WikiType,
        last_modified_at: str,
        entity_type: Optional[EntityType] = None,
    ) -> None:
        with Session(self._engine, future=True) as session:
            row = IDLookup(
                wiki_id=wiki_id,
                wiki_type=wiki_type,
                entity_type=entity_type,
                local_id=None,
                last_modified_at=last_modified_at,
                last_checked=str(datetime.utcnow()),
            )
            session.add(row)
            session.commit()

    def wiki_id_exists(self, wiki_id: str) -> bool:
        with Session(self._engine, future=True) as session:
            row = (
                session.query(IDLookup)
                .filter(IDLookup.wiki_id == wiki_id)
                .one_or_none()
            )
            if row is None:
                return False
            return True

    def correlate_local_id_to_wiki_id(self, wiki_id: str, local_id: str) -> None:
        with Session(self._engine, future=True) as session:
            row = (
                session.query(IDLookup)
                .filter(IDLookup.wiki_id == wiki_id)
                .one_or_none()
            )
            if row is None:
                raise DatabaseError(f"Wiki ID {wiki_id} not found.")
            row.local_id = local_id
            session.add(row)
            session.commit()

    def record_wiki_id_checked(
        self, wiki_id: str, last_modified_at: Optional[str] = None
    ):
        with Session(self._engine, future=True) as session:
            row = (
                session.query(IDLookup)
                .filter(IDLookup.wiki_id == wiki_id)
                .one_or_none()
            )
            if row is None:
                raise DatabaseError(f"Wiki ID {wiki_id} not found.")
            row.last_checked = str(datetime.utcnow())
            if last_modified_at is not None:
                row.last_modified_at = last_modified_at
            session.add(row)
            session.commit()

    def add_ids_to_queue(
        self, wiki_type: WikiType, entity_type: EntityType, ids: List[str]
    ):
        with Session(self._engine, future=True) as session:
            now = str(datetime.utcnow())
            items = [
                WikiQueue(
                    wiki_id=wiki_id,
                    wiki_type=wiki_type,
                    entity_type=entity_type,
                    time_added=now,
                )
                for wiki_id in ids
            ]
            session.add_all(items)
            session.commit()

    def get_oldest_item_from_queue(self) -> Optional[Item]:
        with Session(self._engine, future=True) as session:
            row = (
                session.query(WikiQueue)
                .order_by(WikiQueue.time_added)
                .limit(1)
                .one_or_none()
            )
            if row is None:
                return None
            return Item(
                wiki_id=row.wiki_id,
                wiki_type=row.wiki_type,
                entity_type=row.entity_type,
            )

    def remove_item_from_queue(self, wiki_id: str):
        with Session(self._engine, future=True) as session:
            row = (
                session.query(WikiQueue)
                .filter(WikiQueue.wiki_id == wiki_id)
                .one_or_none()
            )
            if row is None:
                return
            session.delete(row)
            session.commit()

    def report_queue_error(self, wiki_id: str, error_time: str, errors: str):
        with Session(self._engine, future=True) as session:
            row = (
                session.query(WikiQueue)
                .filter(WikiQueue.wiki_id == wiki_id)
                .one_or_none()
            )
            if row is None:
                raise DatabaseError(f"WikiQueue row with ID `{wiki_id}` not found.")
            row.errors[error_time] = errors
            flag_modified(key="errors", instance=row)
            session.add(row)
            session.commit()
