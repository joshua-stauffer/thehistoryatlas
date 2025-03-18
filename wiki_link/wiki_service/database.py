import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from wiki_service.config import WikiServiceConfig
from wiki_service.schema import Base, WikiQueue
from wiki_service.schema import IDLookup
from wiki_service.schema import Config as ConfigModel
from wiki_service.schema import CreatedEvents
from wiki_service.types import EntityType, WikiDataItem

log = logging.getLogger(__name__)


class DatabaseError(Exception): ...


@dataclass
class Item:
    wiki_id: str
    entity_type: EntityType
    wiki_link: Optional[str] = None


class Database:
    def __init__(self, config):
        self._engine = create_engine(config.DB_URI, echo=config.DEBUG, future=True)
        # initialize the db
        Base.metadata.create_all(self._engine)

    def add_wiki_entry(
        self,
        wiki_id: str,
        last_modified_at: str,
        entity_type: Optional[EntityType] = None,
    ) -> None:
        with Session(self._engine, future=True) as session:
            row = IDLookup(
                wiki_id=wiki_id,
                entity_type=entity_type,
                local_id=None,  # added when entity is created
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

    def add_items_to_queue(self, entity_type: EntityType, items: List[WikiDataItem]):
        with Session(self._engine, future=True) as session:
            now = str(datetime.utcnow())
            for item in items:
                try:
                    session.add(
                        WikiQueue(
                            wiki_id=item.qid,
                            wiki_url=item.url,
                            entity_type=entity_type,
                            time_added=now,
                        )
                    )
                    session.commit()
                except Exception as e:
                    # this qid is still in the queue
                    log.debug(f"Encountered exception: {e}")
                    session.rollback()

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
                entity_type=row.entity_type,
                wiki_link=row.wiki_url,
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

    def is_wiki_id_in_queue(self, wiki_id: str) -> bool:
        with Session(self._engine, future=True) as session:
            row = (
                session.query(WikiQueue)
                .filter(WikiQueue.wiki_id == wiki_id)
                .one_or_none()
            )
            if row is None:
                return False
            return True

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

    def save_last_person_offset(self, offset: int) -> None:
        with Session(self._engine, future=True) as session:
            row = session.query(ConfigModel).one()
            row.last_person_search_offset = offset
            session.commit()

    def get_last_person_offset(self) -> int:
        with Session(self._engine, future=True) as session:
            row = session.query(ConfigModel).one_or_none()
            if row is None:
                session.add(self._get_default_config())
                session.commit()
                return 0
            return row.last_person_search_offset

    @staticmethod
    def _get_default_config() -> ConfigModel:
        return ConfigModel(id=1, last_person_search_offset=0)

    def upsert_created_event(
        self,
        wiki_id: str,
        factory_label: str,
        factory_version: int,
        errors: Optional[dict] = None,
    ) -> None:
        """
        Create or update a CreatedEvents row.
        If the row exists, update the factory_version and errors fields.
        If it doesn't exist, create a new row.

        Args:
            wiki_id: The wiki ID to create/update
            factory_label: The label of the factory that created the event
            factory_version: The version of the factory
            errors: Optional dictionary of errors encountered during creation
        """
        with Session(self._engine, future=True) as session:
            row = session.execute(
                text(
                    """
                        select factory_version, errors from created_events
                        where wiki_id = :wiki_id
                        and factory_label = :factory_label
                    """
                ),
                {"wiki_id": wiki_id, "factory_label": factory_label},
            ).one_or_none()
            if row is None:
                row = CreatedEvents(
                    wiki_id=wiki_id,
                    factory_label=factory_label,
                    factory_version=factory_version,
                    errors=errors or {},
                )
                session.add(row)
            else:
                if errors:
                    errors_dict = {"errors": json.dumps(errors)}
                else:
                    errors_dict = {}
                session.execute(
                    text(
                        """
                        update created_events
                        set (factory_version, errors, updated_at)
                        from (:factory_version, :errors, :updated_at)
                        where wiki_id = :wiki_id
                        and factory_label = :factory_label;
                    """
                    ),
                    {
                        "wiki_id": wiki_id,
                        "factory_label": factory_label,
                        "factory_version": factory_version,
                        "updated_at": datetime.now(timezone.utc),
                        **errors_dict,
                    },
                )

            session.commit()

    def event_exists(
        self, wiki_id: str, factory_label: str, factory_version: int
    ) -> bool:
        """
        Check if a CreatedEvents row exists with the given wiki_id, factory_label, and factory_version.

        Args:
            wiki_id: The wiki ID to check
            factory_label: The label of the factory
            factory_version: The version of the factory

        Returns:
            bool: True if a matching row exists, False otherwise
        """
        with Session(self._engine, future=True) as session:
            row = session.execute(
                text(
                    """
                        select * from created_events c
                        where (
                            c.wiki_id = :wiki_id
                            and c.factory_label = :factory_label
                            and c.factory_version = :factory_version
                        );
                    """
                ),
                {
                    "wiki_id": wiki_id,
                    "factory_label": factory_label,
                    "factory_version": factory_version,
                },
            ).one_or_none()
            return row is not None

    @classmethod
    def factory(cls) -> "Database":
        """
        Get a configured Database instance.
        """
        database = cls(config=WikiServiceConfig())
        return database
