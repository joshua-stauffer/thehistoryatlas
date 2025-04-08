import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from wiki_service.config import WikiServiceConfig
from wiki_service.schema import Base, WikiQueue, CreatedEvent
from wiki_service.schema import IDLookup
from wiki_service.schema import Config as ConfigModel
from wiki_service.schema import FactoryResult
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

    def save_last_works_of_art_offset(self, offset: int) -> None:
        with Session(self._engine, future=True) as session:
            row = session.query(ConfigModel).one()
            row.last_works_of_art_search_offset = offset
            session.commit()

    def get_last_works_of_art_offset(self) -> int:
        with Session(self._engine, future=True) as session:
            row = session.query(ConfigModel).one_or_none()
            if row is None:
                session.add(self._get_default_config())
                session.commit()
                return 0
            return row.last_works_of_art_search_offset

    def save_last_books_offset(self, offset: int) -> None:
        with Session(self._engine, future=True) as session:
            row = session.query(ConfigModel).one()
            row.last_books_search_offset = offset
            session.commit()

    def get_last_books_offset(self) -> int:
        with Session(self._engine, future=True) as session:
            row = session.query(ConfigModel).one_or_none()
            if row is None:
                session.add(self._get_default_config())
                session.commit()
                return 0
            return row.last_books_search_offset

    def save_last_orations_offset(self, offset: int) -> None:
        with Session(self._engine, future=True) as session:
            row = session.query(ConfigModel).one()
            row.last_orations_search_offset = offset
            session.commit()

    def get_last_orations_offset(self) -> int:
        with Session(self._engine, future=True) as session:
            row = session.query(ConfigModel).one_or_none()
            if row is None:
                session.add(self._get_default_config())
                session.commit()
                return 0
            return row.last_orations_search_offset

    @staticmethod
    def _get_default_config() -> ConfigModel:
        return ConfigModel(
            id=1,
            last_person_search_offset=0,
            last_works_of_art_search_offset=0,
            last_books_search_offset=0,
            last_orations_search_offset=0,
        )

    def upsert_created_event(
        self,
        wiki_id: str,
        factory_label: str,
        factory_version: int,
        errors: Optional[dict] = None,
        server_id: Optional[UUID] = None,
        secondary_wiki_id: str | None = None,
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
            server_id: Optional UUID of the server that created the event
            secondary_wiki_id: Optional secondary wiki ID for events involving two entities
        """
        with Session(self._engine, future=True) as session:
            # First find or create the factory result
            factory_result = session.execute(
                text(
                    """
                    select id, factory_version, errors from factory_results
                    where wiki_id = :wiki_id
                    and factory_label = :factory_label
                    """
                ),
                {"wiki_id": wiki_id, "factory_label": factory_label},
            ).one_or_none()

            if factory_result is None:
                # Create new factory result
                factory_result_id = uuid4()
                session.execute(
                    text(
                        """
                        insert into factory_results (id, wiki_id, factory_label, factory_version, errors, updated_at)
                        values (:id, :wiki_id, :factory_label, :factory_version, :errors, :updated_at)
                        """
                    ),
                    {
                        "id": factory_result_id,
                        "wiki_id": wiki_id,
                        "factory_label": factory_label,
                        "factory_version": factory_version,
                        "errors": json.dumps(errors if errors is not None else {}),
                        "updated_at": datetime.now(timezone.utc),
                    },
                )
            else:
                factory_result_id = factory_result[0]
                # Update existing factory result
                session.execute(
                    text(
                        """
                        update factory_results
                        set factory_version = :factory_version,
                            errors = :errors,
                            updated_at = :updated_at
                        where id = :id
                        """
                    ),
                    {
                        "id": factory_result_id,
                        "factory_version": factory_version,
                        "errors": json.dumps(errors if errors is not None else {}),
                        "updated_at": datetime.now(timezone.utc),
                    },
                )

            # Now create the created event
            session.execute(
                text(
                    """
                    insert into created_events (id, factory_result_id, primary_entity_id, secondary_entity_id, server_id)
                    values (:id, :factory_result_id, :primary_entity_id, :secondary_entity_id, :server_id)
                    """
                ),
                {
                    "id": uuid4(),
                    "factory_result_id": factory_result_id,
                    "primary_entity_id": wiki_id,
                    "secondary_entity_id": secondary_wiki_id,
                    "server_id": server_id,
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
            result = session.execute(
                text(
                    """
                    select 1 from factory_results
                    where wiki_id = :wiki_id
                    and factory_label = :factory_label
                    and factory_version = :factory_version;
                    """
                ),
                {
                    "wiki_id": wiki_id,
                    "factory_label": factory_label,
                    "factory_version": factory_version,
                },
            ).one_or_none()
            return result is not None

    @classmethod
    def factory(cls) -> "Database":
        """
        Get a configured Database instance.
        """
        database = cls(config=WikiServiceConfig())
        return database

    def get_server_id_by_event_label(
        self,
        event_label: list[str],
        primary_entity_id: str,
        secondary_entity_id: str | None = None,
    ) -> list[UUID]:
        """
        Query server_ids from created_events based on event labels and entity IDs.

        Args:
            event_label: List of factory labels to filter by
            primary_entity_id: Primary entity ID to filter by
            secondary_entity_id: Optional secondary entity ID to filter by

        Returns:
            list[UUID]: List of server IDs found in matching rows
        """
        with Session(self._engine, future=True) as session:
            query = text(
                """
                SELECT DISTINCT ce.server_id
                FROM created_events ce
                JOIN factory_results fr ON fr.id = ce.factory_result_id
                WHERE fr.factory_label = ANY(:event_label)
                AND ce.primary_entity_id = :primary_entity_id
                AND (
                    :secondary_entity_id IS NULL 
                    OR ce.secondary_entity_id = :secondary_entity_id
                )
                AND ce.server_id IS NOT NULL
            """
            )

            result = session.execute(
                query,
                {
                    "event_label": event_label,
                    "primary_entity_id": primary_entity_id,
                    "secondary_entity_id": secondary_entity_id,
                },
            )

            return [row[0] for row in result]
