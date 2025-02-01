from typing import List

from sqlalchemy import text

from the_history_atlas.apps.domain.models.history.tables import (
    CitationModel,
    SourceModel,
    SummaryModel,
    PersonModel,
    PlaceModel,
    TimeModel,
    NameModel,
    TagNameAssocModel,
    TagInstanceModel,
)


class DBBuilder:
    def __init__(self, session):
        self._session = session

    def insert_citations(self, citations: list[CitationModel]):
        stmt = """
            insert into citations (id, text,  page_num, access_date, summary_id, source_id)
            values (:id, :text,  :page_num, :access_date, :summary_id, :source_id);
        """
        self._session.execute(text(stmt), [citation.dict() for citation in citations])

    def insert_summaries(self, summaries: list[SummaryModel]):
        stmt = """
            insert into summaries 
            (id, text)
            values 
            (:id, :text);
        """
        self._session.execute(text(stmt), [summary.dict() for summary in summaries])

    def insert_people(self, people: list[PersonModel]):
        stmt = """
            insert into tags (id, type)
            values (:id, :type);
            insert into people (id)
            values (:id);
        """
        self._session.execute(text(stmt), [person.dict() for person in people])

    def insert_places(self, places: list[PlaceModel]):
        stmt = """
            insert into tags (id, type)
            values (:id, :type);
            insert into places (id, latitude, longitude, geoshape, geonames_id)
            values (:id, :latitude, :longitude, :geoshape, :geonames_id);
        """
        self._session.execute(text(stmt), [place.dict() for place in places])

    def insert_times(self, times: list[TimeModel]):
        stmt = """
            insert into tags (id, type)
            values (:id, :type);
            insert into times (id, time, calendar_model, precision)
            values (:id, :time, :calendar_model, :precision)
        """
        self._session.execute(text(stmt), [time.dict() for time in times])

    def insert_sources(self, sources: list[SourceModel]):
        stmt = """
            insert into sources 
            (id, title, author, publisher, pub_date, kwargs)
            values 
            (:id, :title, :author, :publisher, :pub_date, :kwargs);
        """
        self._session.execute(text(stmt), [source.dict() for source in sources])

    def insert_names(self, names: list[NameModel]):
        stmt = """
            insert into names (id, name)
            values (:id, :name);
        """
        self._session.execute(text(stmt), [name.dict() for name in names])

    def insert_tag_names(self, tag_names: list[TagNameAssocModel]):
        stmt = """
            insert into tag_names (tag_id, name_id)
            values (:tag_id, :name_id);
        """
        self._session.execute(text(stmt), [tag_name.dict() for tag_name in tag_names])

    def insert_tag_instances(self, tag_instances: list[TagInstanceModel]):
        stmt = """
            insert into tag_instances (id, start_char, stop_char, summary_id, tag_id)
            values (:id, :start_char, :stop_char, :summary_id, :tag_id);
        """
        self._session.execute(
            text(stmt), [tag_instance.dict() for tag_instance in tag_instances]
        )
