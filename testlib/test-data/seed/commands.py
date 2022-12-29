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

bach_data = [
    {
        "updatedAnnotation": {
            "summary": "Johann Sebastian Bach was born in Eisenach in 1685.",
            "meta": {"title": "test", "author": "t", "publisher": "s"},
            "citation": "Johann Sebastian Bach was born in Eisenach, the capital of the duchy of Saxe-Eisenach, in present-day Germany, on 21 March 1685.",
            "summaryTags": [
                {
                    "type": "PERSON",
                    "id": "c0484f0e-3ddf-44bd-9ed6-7ed4acf242f2",
                    "name": "Johann Sebastian Bach",
                    "startChar": 0,
                    "stopChar": 21,
                },
                {
                    "type": "PLACE",
                    "id": "a186d3d4-8f13-4c0a-be2c-45648383dd09",
                    "name": "Eisenach",
                    "startChar": 34,
                    "stopChar": 42,
                    "latitude": 50.9807,
                    "longitude": 10.31522,
                },
                {"type": "TIME", "name": "1685", "startChar": 123, "stopChar": 127},
            ],
            "citationId": "1f817a69-0572-40cf-9777-ebdc601eb565",
            "summaryId": None,
            "token": "gAAAAABjq1CP4KGpGrC9YNREB-VIWayY9gPJXrpvfRv_UtWvF7FZxAeuUVeJ2fitzd2fgs4tvx1pSgTp1d0veBagmkv3fBxbzZFWSRTN0DoaJoaVlPcHlrTfvaWUTchCYcjCWSYj5GSuqIvNtt2tmCXXOQISjGMgiQ==",
        }
    },
    {
        "summary": "When Johann Sebastian Bach's mother and father died in 1694, he moved in with his eldest brother Johann Christoph Bach in Berlin.",
        "meta": {
            "title": "Wikipedia",
            "author": "The Universe",
            "publisher": "wikipedia.org",
            "pubDate": "2023-12-28",
        },
        "citation": "Bach's mother died in 1694, and his father died eight months later. The 10-year-old Bach moved in with his eldest brother, Johann Christoph Bach, the organist at St. Michael's Church in Ohrdruf, Saxe-Gotha-Altenburg.",
        "summaryTags": [
            {
                "type": "PERSON",
                "id": "c0484f0e-3ddf-44bd-9ed6-7ed4acf242f2",
                "name": "Johann Sebastian Bach",
                "startChar": 0,
                "stopChar": 4,
            },
            {"type": "TIME", "name": "1694", "startChar": 22, "stopChar": 26},
            {
                "type": "PERSON",
                "name": "Johann Christoph Bach",
                "startChar": 123,
                "stopChar": 144,
            },
            {
                "type": "PLACE",
                "name": "Berlin",
                "startChar": 186,
                "stopChar": 193,
                "latitude": 52.52437,
                "longitude": 13.41053,
            },
        ],
        "citationId": "582ed8d8-df6f-416a-9e71-9ae554f6a4a3",
        "summaryId": "None",
        "token": "gAAAAABjq1CP4KGpGrC9YNREB-VIWayY9gPJXrpvfRv_UtWvF7FZxAeuUVeJ2fitzd2fgs4tvx1pSgTp1d0veBagmkv3fBxbzZFWSRTN0DoaJoaVlPcHlrTfvaWUTchCYcjCWSYj5GSuqIvNtt2tmCXXOQISjGMgiQ==",
    },
    {
        "summary": "In January 1703, Bach took a job as court musician for Duke Johann Ernst III in Weimar.",
        "meta": {
            "title": "Wikipedia",
            "author": "The Universe",
            "publisher": "wikipedia.org",
            "pubDate": "2023",
        },
        "citation": "In January 1703, shortly after graduating from St. Michael's and being turned down for the post of organist at Sangerhausen, Bach was appointed court musician in the chapel of Duke Johann Ernst III in Weimar.",
        "summaryTags": [
            {"type": "TIME", "name": "1703", "startChar": 3, "stopChar": 15},
            {
                "type": "PERSON",
                "name": "Duke Johann Ernst III",
                "startChar": 176,
                "stopChar": 197,
            },
            {
                "type": "PLACE",
                "name": "Weimar",
                "startChar": 201,
                "stopChar": 207,
                "latitude": 50.9803,
                "longitude": 11.32903,
            },
        ],
        "citationId": "2b319357-421e-4c51-a8d4-aa6143ec6240",
        "summaryId": None,
        "token": "gAAAAABjq1CP4KGpGrC9YNREB-VIWayY9gPJXrpvfRv_UtWvF7FZxAeuUVeJ2fitzd2fgs4tvx1pSgTp1d0veBagmkv3fBxbzZFWSRTN0DoaJoaVlPcHlrTfvaWUTchCYcjCWSYj5GSuqIvNtt2tmCXXOQISjGMgiQ==",
    },
    {
        "updatedAnnotation": {
            "summary": "In 1703, Johann Sebastian Bach moved from Weimar to Arnstadt.",
            "meta": {
                "title": "Wikipedia",
                "author": "The Universe",
                "publisher": "wikipedia.org",
                "pubDate": "2023",
            },
            "citation": "During his seven-month tenure at Weimar, his reputation as a keyboardist spread so much that he was invited to inspect the new organ and give the inaugural recital at the New Church (now Bach Church) in Arnstadt, located about 30 kilometres (19 mi) southwest of Weimar. On 14 August 1703, he became the organist at the New Church, with light duties, a relatively generous salary, and a new organ tuned in a temperament that allowed music written in a wider range of keys to be played.",
            "summaryTags": [
                {
                    "type": "PLACE",
                    "id": "e07eeb32-ff70-47f4-ac1e-946c5584d06d",
                    "name": "Weimar",
                    "startChar": 33,
                    "stopChar": 39,
                    "latitude": 50.9803,
                    "longitude": 11.32903,
                },
                {
                    "type": "PLACE",
                    "name": "Arnstadt",
                    "startChar": 203,
                    "stopChar": 211,
                    "latitude": 50.84048,
                    "longitude": 10.95198,
                },
                {
                    "type": "PLACE",
                    "id": "e07eeb32-ff70-47f4-ac1e-946c5584d06d",
                    "name": "Weimar",
                    "startChar": 262,
                    "stopChar": 268,
                    "latitude": 50.9803,
                    "longitude": 11.32903,
                },
                {
                    "type": "TIME",
                    "id": "d9238327-ef43-4012-bb92-a18574406ae2",
                    "name": "1703",
                    "startChar": 283,
                    "stopChar": 287,
                },
                {
                    "type": "PERSON",
                    "id": "c0484f0e-3ddf-44bd-9ed6-7ed4acf242f2",
                    "name": "Johann Sebastian Bach",
                    "startChar": 289,
                    "stopChar": 291,
                },
            ],
            "citationId": "021f3501-aee9-4b77-8dae-c3d3ced8903f",
            "summaryId": None,
            "token": "gAAAAABjq1CP4KGpGrC9YNREB-VIWayY9gPJXrpvfRv_UtWvF7FZxAeuUVeJ2fitzd2fgs4tvx1pSgTp1d0veBagmkv3fBxbzZFWSRTN0DoaJoaVlPcHlrTfvaWUTchCYcjCWSYj5GSuqIvNtt2tmCXXOQISjGMgiQ==",
        }
    },
    {
        "updatedAnnotation": {
            "summary": "In 1706, Johann Sebastian Bach took the position of organist in Mühlhausen.",
            "meta": {
                "title": "Wikipedia",
                "author": "the Universe",
                "publisher": "wikipedia.org",
                "pubDate": "2023",
            },
            "citation": "In 1706, Bach applied for a post as organist at the Blasius Church in Mühlhausen. As part of his application, he had a cantata performed on Easter, 24 April 1707, likely an early version of his Christ lag in Todes Banden. A month later Bach's application was accepted and he took up the post in July.",
            "summaryTags": [
                {
                    "type": "TIME",
                    "id": "94d422c1-ad10-4c84-8d8e-c07fb06b4c9d",
                    "name": "1706",
                    "startChar": 3,
                    "stopChar": 7,
                },
                {
                    "type": "PERSON",
                    "id": "c0484f0e-3ddf-44bd-9ed6-7ed4acf242f2",
                    "name": "Johann Sebastian Bach",
                    "startChar": 9,
                    "stopChar": 13,
                },
                {
                    "type": "PLACE",
                    "name": "Mühlhausen",
                    "startChar": 70,
                    "stopChar": 80,
                    "latitude": 51.20896,
                    "longitude": 10.45275,
                },
            ],
            "citationId": "7b435ad6-a16c-4faf-9167-2639128d7276",
            "token": "gAAAAABjrds5WoIKqTShj6dHXcYWK5XBumA4kYrDAuM0whGTfgT88RWKj0EKnfJkOW-pIzpQ8HjWf1SSQUqYZLR3k6ME2NDi8SWPE2TSj4StUZbddtgEsHC3_IpjxRnoZy-7f2Obxxku_8dxtCQ35e9Jr6hmz6Mzhg==",
        }
    },
]
