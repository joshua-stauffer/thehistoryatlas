import os
import uuid
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from the_history_atlas.apps.readmodel.schema import (
    Base,
    Tag,
    Person,
    Place,
    Time,
    Name,
    Source,
    Story,
    StoryName,
    Summary,
    TagInstance,
    Citation,
    StorySummary,
    TagNameAssoc,
)
from faker import Faker

# Initialize Faker
fake = Faker()

# Database setup
DATABASE_URL = os.environ.get("DEV_DB_URI")
if not DATABASE_URL:
    raise RuntimeError("DEV_DB_URI environment variable is not set")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
with session.no_autoflush:

    # Create all tables
    Base.metadata.create_all(engine)

    def create_seed_data():
        # Helper functions
        def random_uuid():
            return str(uuid.uuid4())

        # Seed Tags, People, Places, and Times
        tags = []

        def create_name_variations_and_associate(base_name, variations, tag_id):
            for name in variations:
                name_obj = Name(id=random_uuid(), name=name)
                # Add the association to tag_name_assoc
                names.append(name_obj)
                tag_name_associations.append(
                    TagNameAssoc(tag_id=tag_id, name_id=name_obj.id)
                )

        for i in range(300):
            tag_id = random_uuid()
            tag_type = "PERSON" if i < 100 else "PLACE" if i < 200 else "TIME"
            if tag_type == "PERSON":
                tags.append(
                    Person(
                        id=tag_id,
                        names=[
                            Name(id=random_uuid(), name=name)
                            for name in [
                                f"Person {i+1}",
                                f"P{i+1}",
                                f"Individual {i+1}",
                            ]
                        ],
                    ),
                )

            elif tag_type == "PLACE":
                tags.append(
                    Place(
                        id=tag_id,
                        names=[
                            Name(id=random_uuid(), name=name)
                            for name in [f"Place {i+1}", f"P{i+1}", f"Location {i+1}"]
                        ],
                    )
                )
            elif tag_type == "TIME":
                precision = random.choice([7, 8, 9, 10, 11])
                time_value = fake.date()
                translations = {
                    "en": f"The Year {time_value}",
                    "it": f"L'Anno {time_value}",
                    "de": f"Das Jahr {time_value}",
                    "fr": f"L'Année {time_value}",
                    "es": f"El Año {time_value}",
                }
                tags.append(
                    Time(
                        id=tag_id,
                        time=time_value,
                        precision=precision,
                        names=[
                            Name(id=random_uuid(), name=name, lang=lang)
                            for lang, name in translations.items()
                        ],
                    )
                )

        session.add_all(tags)
        session.flush()

        # Seed Sources
        sources = []
        for i in range(100):
            source_id = random_uuid()
            source_title = fake.sentence(nb_words=5)  # Generate a realistic title
            source_author = fake.name()  # Generate an author name
            source_published_date = (
                fake.date_this_century()
            )  # Generate a realistic date

            sources.append(
                Source(
                    id=source_id,
                    title=source_title,
                    author=source_author,
                    pub_date=source_published_date,
                    publisher=source_author,
                )
            )
            session.add(sources[-1])

        # Seed Stories and Story Names
        for tag in tags:
            story_id = random_uuid()
            story = Story(id=story_id, tag_id=tag.id)
            session.add(story)

            translations = {
                "en": f"The history of {tag.type} {tag.id[:8]}",
                "it": f"La storia di {tag.type} {tag.id[:8]}",
                "de": f"Die Geschichte von {tag.type} {tag.id[:8]}",
                "fr": f"L'histoire de {tag.type} {tag.id[:8]}",
                "es": f"La historia de {tag.type} {tag.id[:8]}",
            }
            for lang, name in translations.items():
                session.add(
                    StoryName(id=random_uuid(), story_id=story_id, name=name, lang=lang)
                )

        # Seed Summaries and Tag Instances
        for i in range(1000):
            summary_id = random_uuid()
            person_tag = tags[i % 100]
            place_tag = tags[100 + (i % 100)]
            time_tag = tags[200 + (i % 100)]

            summary_text = fake.paragraph(
                nb_sentences=5
            )  # Generate realistic summary text
            summary = Summary(id=summary_id, text=summary_text)
            session.add(summary)

            for tag in [person_tag, place_tag, time_tag]:
                tag_name = (
                    fake.word()
                )  # Placeholder for tag-specific text to simulate realism
                start_char = summary_text.find(tag_name)
                stop_char = start_char + len(tag_name)
                session.add(
                    TagInstance(
                        id=random_uuid(),
                        tag_id=tag.id,
                        summary_id=summary_id,
                        start_char=start_char,
                        stop_char=stop_char,
                    )
                )

            source = random.choice(sources)
            session.add(
                Citation(id=random_uuid(), summary_id=summary_id, source_id=source.id)
            )

            for story in session.query(Story).filter(
                Story.tag_id.in_([person_tag.id, place_tag.id, time_tag.id])
            ):
                session.add(
                    StorySummary(
                        id=random_uuid(),
                        story_id=story.id,
                        summary_id=summary_id,
                        order=i,
                    )
                )

        session.commit()


# Run the seed script
if __name__ == "__main__":
    # Drop all tables and recreate them
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    create_seed_data()
