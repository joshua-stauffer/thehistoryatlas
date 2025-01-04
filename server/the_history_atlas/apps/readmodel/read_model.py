import logging
from typing import List
from uuid import uuid4

from spacy import lang
from sqlalchemy import text

from the_history_atlas.apps.database import DatabaseClient
from the_history_atlas.apps.domain.models import CoordsByName
from the_history_atlas.apps.domain.models.core import (
    SourceInput,
    PersonInput,
    TimeInput,
    PlaceInput,
)
from the_history_atlas.apps.domain.models.readmodel import DefaultEntity, Source
from the_history_atlas.apps.domain.models.readmodel.queries import (
    GetSummariesByIDs,
    Summary,
    GetCitationByID,
    Citation,
    GetManifest,
    Manifest,
    GetEntitySummariesByName,
    EntitySummary,
    GetEntityIDsByNames,
    EntityIDsByNames,
    GetFuzzySearchByName,
    FuzzySearchByName,
    GetEntitySummariesByIDs,
    GetPlaceByCoords,
    PlaceByCoords,
    EntitySummariesByName,
)
from the_history_atlas.apps.config import Config
from the_history_atlas.apps.domain.models.readmodel.tables.source import (
    SourceModelInput,
    SourceModel,
)
from the_history_atlas.apps.domain.types import Event
from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.event_handler import EventHandler
from the_history_atlas.apps.readmodel.query_handler import QueryHandler
from the_history_atlas.apps.readmodel.trie import Trie

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class ReadModelApp:
    def __init__(self, config_app: Config, database_client: DatabaseClient):
        self.config = config_app
        source_trie = Trie()
        entity_trie = Trie()
        self._db = database_client

        database = Database(
            database_client=database_client,
            source_trie=source_trie,
            entity_trie=entity_trie,
        )
        source_trie.build(entity_tuples=database.get_all_source_titles_and_authors())
        entity_trie.build(entity_tuples=database.get_all_entity_names())
        self._query_handler = QueryHandler(
            database_instance=database, source_trie=source_trie, entity_trie=entity_trie
        )
        self._event_handler = EventHandler(
            database_instance=database, source_trie=source_trie, entity_trie=entity_trie
        )

    def handle_event(self, event: Event):
        self._event_handler.handle_event(event=event)

    def get_summaries_by_ids(self, query: GetSummariesByIDs) -> List[Summary]:
        return self._query_handler.get_summaries_by_id(query)

    def get_citation_by_id(self, query: GetCitationByID) -> Citation:
        return self._query_handler.get_citation_by_id(query)

    def get_manifest(self, query: GetManifest) -> Manifest:
        return self._query_handler.get_manifest(query)

    def get_entity_summaries_by_name(
        self, query: GetEntitySummariesByName
    ) -> EntitySummariesByName:
        return self._query_handler.get_entity_summaries_by_name(query)

    def get_entity_ids_by_names(self, query: GetEntityIDsByNames) -> EntityIDsByNames:
        return self._query_handler.get_entity_ids_by_names(query)

    def get_fuzzy_search_by_name(
        self, query: GetFuzzySearchByName
    ) -> List[FuzzySearchByName]:
        return self._query_handler.get_fuzzy_search_by_name(query)

    def get_entity_summaries_by_ids(
        self, query: GetEntitySummariesByIDs
    ) -> List[EntitySummary]:
        return self._query_handler.get_entity_summaries_by_ids(query)

    def get_place_by_coords(self, query: GetPlaceByCoords) -> PlaceByCoords:
        return self._query_handler.get_place_by_coords(query)

    def get_default_entity(self) -> DefaultEntity:
        return self._query_handler.get_default_entity()

    def get_sources_by_search_term(self, search_term: str) -> List[Source]:
        return self._query_handler.get_sources_by_search_term(search_term=search_term)

    def get_coords_by_names(self, names: list[str]) -> CoordsByName:
        return self._query_handler.get_coords_by_names(names=names)

    def get_story(
        self,
        story_id: UUID,
        event_id: UUID,
        direction: Literal["prev", "next"] | None = None,
    ) -> Story:
        event_query = text(
            """
                WITH story_info AS (
                    SELECT
                        s.id AS story_id,
                        sn.name AS story_name
                    FROM
                        stories s
                    INNER JOIN
                        story_names sn
                    ON
                        s.id = sn.story_id
                    WHERE
                        s.id = :story_id AND sn.lang = :lang
                ),
                ordered_summaries AS (
                    SELECT
                        ss.*,
                        ROW_NUMBER() OVER (ORDER BY ss."order" ASC) AS row_num
                    FROM
                        story_summaries ss
                    WHERE
                        ss.story_id = :story_id
                ),
                selected_summaries AS (
                    SELECT
                        os.*
                    FROM
                        ordered_summaries os
                    WHERE
                        os.summary_id = :event_id
                    UNION ALL
                    SELECT
                        os.*
                    FROM
                        ordered_summaries os
                    WHERE
                        os.row_num > (
                            SELECT row_num FROM ordered_summaries WHERE summary_id = :event_id
                        )
                    AND
                        :direction = 'next'
                    ORDER BY
                        os."order" ASC
                    LIMIT :limit
                    UNION ALL
                    SELECT
                        os.*
                    FROM
                        ordered_summaries os
                    WHERE
                        os.row_num < (
                            SELECT row_num FROM ordered_summaries WHERE summary_id = :event_id
                        )
                    AND
                        :direction = 'prev'
                    ORDER BY
                        os."order" DESC
                    LIMIT :limit
                ),
                summary_details AS (
                    SELECT
                        sm.id AS summary_id,
                        sm.text AS summary_text,
                        c.id AS citation_id,
                        c.text AS citation_text,
                        so.*
                    FROM
                        summaries sm
                    LEFT JOIN
                        citations c
                    ON
                        sm.id = c.summary_id
                    LEFT JOIN
                        sources so
                    ON
                        c.source_id = so.id
                    WHERE
                        sm.id IN (SELECT summary_id FROM selected_summaries)
                ),
                tag_details AS (
                    SELECT
                        ti.summary_id,
                        ti.id AS tag_instance_id,
                        ti.start_char,
                        ti.stop_char,
                        t.*,
                        COALESCE(ti_tag.type, '') AS tag_type,
                        CASE
                            WHEN t.type = 'TIME' THEN (
                                SELECT jsonb_agg(to_jsonb(tt)) FROM time tt WHERE tt.id = t.id
                            )
                            WHEN t.type = 'PERSON' THEN (
                                SELECT jsonb_agg(to_jsonb(pt)) FROM person pt WHERE pt.id = t.id
                            )
                            WHEN t.type = 'PLACE' THEN (
                                SELECT jsonb_agg(to_jsonb(pl)) FROM place pl WHERE pl.id = t.id
                            )
                            ELSE NULL
                        END AS tag_specific_data,
                        (SELECT array_agg(n.name) FROM names n WHERE n.id = t.id AND n.lang = :lang)
                    FROM
                        taginstances ti
                    JOIN
                        tags t
                    WHERE
                        PRIMARY BY ENTITY. A!
                      }
            """
        )
        rows = self._db.execute(
            event_query,
            {
                "story_id": story_id,
                "event_id": event_id,
                "lang": lang,
                "direction": direction,
            },
        ).all()
        print()

    def add_source(self, source: SourceModelInput) -> SourceModel:
        id = uuid4()
        self._db.execute(
            text(
                """
                INSERT INTO sources 
                    (id, title, author, publisher, pub_date, kwargs)
                VALUES 
                    (:source_id, :title, :author, :publisher, :pub_date, :kwargs)
            """
            ),
            {
                **source.model_dump(),
                "source_id": id,
            },
        )

    def add_tag(self, tag: PersonInput | PlaceInput | TimeInput):
        ...
