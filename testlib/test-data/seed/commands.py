from abstract_domain_model.models import PublishCitation, PublishCitationPayload
from abstract_domain_model.models.commands import Person, Place, Time, Meta

PUBLISH_CITATIONS = [
    PublishCitation(
        user_id="c4bc4280-8258-41a9-b8f4-350dc4c15031",
        app_version="0.0.0",
        timestamp="2022-08-15 21:32:28.133457",
        payload=PublishCitationPayload(
            id="21d1e9cc-af4c-444b-abef-2f9ee851b89b",
            text="In fact, for private purposes Bach had actually put down a bare outline of his professional career for a family Genealogy he was compiling around 1735: No. 24. Joh. Sebastian Bach, youngest son of Joh. Ambrosius Bach, was born in Eisenach in the year 1685 on March 21.",
            summary="J.S. Bach was born in Eisenach on March 21st, 1685.",
            summary_id=None,
            tags=[
                Person(
                    id=None,
                    type="PERSON",
                    name="Johann Sebastian Bach",
                    start_char=30,
                    stop_char=34,
                ),
                Place(
                    type="PLACE",
                    id=None,
                    name="Eisenach",
                    start_char=230,
                    stop_char=230,
                    latitude=50.9796,
                    longitude=10.3147,
                    geo_shape=None,
                ),
                Time(
                    id=None,
                    type="TIME",
                    name="1685|3|21",
                    start_char=251,
                    stop_char=267,
                ),
            ],
            meta=Meta(
                id=None,
                title="Johann Sebastian Bach, The Learned Musician",
                author="Wolff, Christoph",
                publisher="W.W. Norton and Company",
                kwargs={"pageNumber": 3},
            ),
        ),
    )
]
