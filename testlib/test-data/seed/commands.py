from copy import deepcopy

PUBLISH_CITATIONS = [
    {
        "user": "c4bc4280-8258-41a9-b8f4-350dc4c15031",
        "app_version": "0.0.0",
        "timestamp": "2022-08-15 21:32:28.133457",
        "type": "PUBLISH_NEW_CITATION",
        "payload": {
            "text": "In fact, for private purposes Bach had actually put down a bare outline of his professional career for a family Genealogy he was compiling around 1735: No. 24. Joh. Sebastian Bach, youngest son of Joh. Ambrosius Bach, was born in Eisenach in the year 1685 on March 21.",
            "tags": [
                {
                    "type": "PERSON",
                    "name": "Johann Sebastian Bach",
                    "start_char": 30,
                    "stop_char": 34,
                },
                {
                    "type": "PLACE",
                    "name": "Eisenach",
                    "start_char": 230,
                    "stop_char": 238,
                    "latitude": 50.9796,
                    "longitude": 10.3147,
                },
                {
                    "type": "TIME",
                    "name": "1685|3|21",
                    "start_char": 251,
                    "stop_char": 267,
                },
            ],
            "summary": "J.S. Bach was born in Eisenach on March 21st, 1685.",
            "meta": {
                "title": "Johann Sebastian Bach, The Learned Musician",
                "author": "Wolff, Christoph",
                "publisher": "W.W. Norton and Company",
                "page": 3,
            },
        },
    }
]

ADD_NEW_CITATION = deepcopy(PUBLISH_CITATIONS)

def build_add_citation_api(command):
    """
    Transform an ADM `ADD_NEW_CITATION` command into the type
    currently expected from the API service.
    """
    command = deepcopy(command)
    summary = command["payload"].pop("summary", None)
    summary_id = command["payload"].pop("summary_id", None)
    summary_dict = {}
    if summary is not None:
        summary_dict["text"] = summary
    if summary_id is not None:
        summary_dict["GUID"] = summary_id
    command["payload"]["summary"] = summary_dict
    return command


ADD_NEW_CITATION_API_OUTPUT = [
    build_add_citation_api(command)
    for command in ADD_NEW_CITATION
]
