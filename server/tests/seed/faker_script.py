import os
from datetime import datetime, timedelta
from uuid import uuid4

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from the_history_atlas.apps.readmodel.schema import (
    Base,
    Summary,
    Story,
    StoryNames,
    StorySummary,
    Citation,
    Source,
    Tag,
    TagInstance,
    Time,
    Person,
    Place,
    Name,
)

# Initialize Faker and database
faker = Faker()
Faker.seed(42)

# Configure database engine
DATABASE_URL = os.environ.get("DEV_DB_URI")
if not DATABASE_URL:
    raise RuntimeError("DEV_DB_URI environment variable is not set")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def create_fake_data():
    # Create fake sources
    sources = []
    for _ in range(5):
        source = Source(
            id=uuid4(),
            title=faker.sentence(),
            author=faker.name(),
            publisher=faker.company(),
            pub_date=faker.date(),
            kwargs={"isbn": faker.isbn13()},
        )
        sources.append(source)
        session.add(source)
    session.commit()

    # Create fake stories
    stories = []
    for _ in range(3):
        story = Story(id=uuid4())
        stories.append(story)
        session.add(story)
    session.commit()

    # Create fake summaries
    summaries = []
    for _ in range(10):
        summary = Summary(
            id=uuid4(),
            text=faker.paragraph(),
            time_tag=faker.date(),
        )
        summaries.append(summary)
        session.add(summary)
    session.commit()

    # Link stories and summaries
    for i, summary in enumerate(summaries):
        story_summary = StorySummary(
            id=uuid4(),
            story_id=stories[i % len(stories)].id,
            summary_id=summary.id,
            order=i + 1,
        )
        session.add(story_summary)
    session.commit()

    # Create fake citations
    for summary in summaries:
        for _ in range(2):
            citation = Citation(
                id=uuid4(),
                text=faker.text(),
                source_id=sources[faker.random_int(0, len(sources) - 1)].id,
                summary_id=summary.id,
                page_num=faker.random_int(1, 500),
                access_date=faker.date(),
            )
            session.add(citation)
    session.commit()

    # Create fake tags
    tags = []
    for _ in range(10):
        type = faker.random_element(["TIME", "PERSON", "PLACE"])
        if type == "TIME":
            tag = Time(
                id=uuid4(),
                time=faker.date_time_between(start_date="-10y", end_date="now"),
                calendar_model="Gregorian",
                precision=faker.random_int(6, 11),
            )
        elif type == "PERSON":
            tag = Person(id=uuid4())
        elif type == "PLACE":
            tag = Place(
                id=uuid4(),
                latitude=faker.latitude(),
                longitude=faker.longitude(),
                geoshape="Polygon",
                geonames_id=faker.random_int(100000, 999999),
            )
        else:
            raise RuntimeError(f"Unknown type {type}")
        tags.append(tag)
        session.add(tag)
    session.commit()

    # Create fake tag instances
    for summary in summaries:
        for _ in range(3):
            tag_instance = TagInstance(
                id=uuid4(),
                start_char=faker.random_int(0, 50),
                stop_char=faker.random_int(51, 100),
                summary_id=summary.id,
                tag_id=tags[faker.random_int(0, len(tags) - 1)].id,
            )
            session.add(tag_instance)
    session.commit()



    # Create fake names and associate them with tags
    for _ in range(20):
        name = Name(
            id=uuid4(),
            name=faker.name(),
        )
        session.add(name)
        for tag in tags[:5]:
            name.tags.append(tag)
    session.commit()

if __name__ == "__main__":
    # Drop all tables and recreate them
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Insert fake data
    create_fake_data()
    print("Fake data inserted successfully!")
