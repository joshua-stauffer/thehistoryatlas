import random
from typing import List
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from tests.test_apps.readmodel.test_database_queries import DB_COUNT
from the_history_atlas.apps.readmodel import ReadModelApp
from the_history_atlas.apps.readmodel.database import Database
from the_history_atlas.apps.readmodel.query_handler import QueryHandler
from the_history_atlas.apps.readmodel.schema import (
    Base,
    Person,
    Place,
    Time,
    Source,
    Citation,
    Summary,
    TagInstance,
)


@pytest.fixture
def mock_db():
    return MagicMock(spec=Database)


@pytest.fixture
def readmodel_app(engine, config):
    return ReadModelApp(database_client=engine, config_app=config)


@pytest.fixture
def readmodel_db(engine):

    db = Database(database_client=engine, stm_timeout=0)

    # if we're using db, ensure its fresh
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine, future=True) as session:
        session.add_all(
            [
                # add any necessary seed data here
            ]
        )
        session.commit()

    yield db

    # cleanup
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture
def db_tuple(readmodel_db, source_title, source_author, engine):
    """
    This fixture manually creates DB_COUNT citations, and DB_COUNT // 2
    of people, places, and times (each). It then associates each citation
    with a person, place, and time, going through the list twice, so that
    each person, place, time is tagged by two different citations.

    NOTE: Because all the db additions are done manually (in order to isolate
    the tests from errors originating in the MUTATION section of the db) the
    addition of names to the Name table is a bit wonky. It's assumed that
    each entity name appears with exactly the same spelling in both citations
    in which it appears.
    """
    summaries = list()
    citations = list()
    people = list()
    places = list()
    times = list()
    cit_guids = list()
    sum_guids = list()
    person_guids = list()
    place_guids = list()
    time_guids = list()
    names = list()
    for _ in range(DB_COUNT // 2):
        person_guid = str(uuid4())
        person_guids.append(person_guid)
        person_name = f"A Person Name {_}"
        people.append(Person(guid=person_guid, names=person_name))
        place_guid = str(uuid4())
        place_guids.append(place_guid)
        place_name = f"A Place Name {_}"
        places.append(
            Place(
                guid=place_guid,
                names=place_name,
                latitude=random.random(),
                longitude=random.random(),
                geoshape="A geoshape string {_}" if random.random() > 0.7 else None,
            )
        )
        time_guid = str(uuid4())
        time_guids.append(time_guid)
        time_name = f"2{_}5{random.randint(0, 9)}|{random.randint(1, 4)}"
        times.append(Time(guid=time_guid, name=time_name))
        # add names to list
        names.extend([person_name, place_name, time_name])
    entities = [
        (person, place, time) for person, place, time in zip(people, places, times)
    ]
    sources: List[Source] = []

    for n in range(DB_COUNT):
        # create a source
        source = Source(
            id=str(uuid4()),
            title=f"{source_title} {n}",
            author=f"{source_author} {n}",
            publisher="Source Publishing Company",
            pub_date="2023-01-02",
        )
        sources.append(source)
        # create a citation
        cit_guid = f"fake-citation-guid-{n}"
        cit_guids.append(cit_guid)
        citation = Citation(
            guid=cit_guid,
            text=f"some citation text {n}",
            source=source,
            source_id=source.id,
            access_date="2022-01-01",
            page_num=11,
        )
        citations.append(citation)
        # create a summary
        sum_guid = f"fake-summary-guid-{n}"
        sum_guids.append(sum_guid)
        person, place, time = entities[n % len(entities)]
        summaries.append(
            Summary(
                guid=sum_guid,
                text=f"test text {n}",
                time_tag=time.name,
                tags=[
                    TagInstance(
                        start_char=random.randint(0, 100),
                        stop_char=random.randint(100, 200),
                        tag=entity,
                    )
                    for entity in (person, place, time)
                ],
                citations=[citation],
            )
        )

    with Session(engine, future=True) as session:
        session.add_all([*summaries, *citations, *people, *places, *times, *sources])
        # manually update names
        for person in people:
            readmodel_db._handle_name(person.names, person.guid, session)
        for place in places:
            readmodel_db._handle_name(place.names, place.guid, session)
        for time in times:
            readmodel_db._handle_name(time.name, time.guid, session)
        session.commit()
    db_dict = {
        "summary_guids": sum_guids,
        "citation_guids": cit_guids,
        "person_guids": person_guids,
        "place_guids": place_guids,
        "time_guids": time_guids,
        "names": names,
    }
    return readmodel_db, db_dict


@pytest.fixture
def source_title():
    return "Source Title"


@pytest.fixture
def source_author():
    return "Source Author"


@pytest.fixture
def query_handler(db_tuple):
    db, _ = db_tuple
    return QueryHandler(database_instance=db)
