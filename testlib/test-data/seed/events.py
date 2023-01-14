from abstract_domain_model.models import PersonAdded, PersonAddedPayload
from abstract_domain_model.models.core import Name, Description
from .synthetic_events import SYNTHETIC_EVENTS
from .util import get_version

EVENTS = [event for events in SYNTHETIC_EVENTS for event in events]

PEOPLE_ADDED = [
    PersonAdded(
        transaction_id="89be0615-0804-44f8-9e29-3ee4082f1290",
        app_version=get_version(),
        timestamp="2023-01-14 05:00:57.383971",
        user_id="9ee62665-5037-441b-86bc-09514c17ab6b",
        payload=PersonAddedPayload(
            id="d4720213-9d88-4c0e-a02c-ea3cfb229944",
            names=[
                Name(
                    id="7f0c5242-3e28-4ae2-9f1d-96ec515aafc5",
                    name="Bach",
                    lang="en",
                    is_default=False,
                ),
                Name(
                    id="7ad8f316-98a1-4182-8656-67e85526c0ba",
                    name="Johann Sebastian Bach",
                    lang="en",
                    is_default=False,
                ),
                Name(
                    id="86d4af61-bd42-41c1-b17b-458f771127d3",
                    name="J.S. Bach",
                    lang="en",
                    is_default=False,
                ),
            ],
            desc=[
                Description(
                    id="ac4019d5-c028-4d83-849c-38ece8e2c48a",
                    text="German composer (1685–1750)",
                    lang="en",
                    source_updated_at="2023-01-14 05:00:57.383971",
                )
            ],
            wiki_link="https://www.wikidata.org/wiki/Q1339",
            wiki_data_id="Q1339",
        ),
        type="PERSON_ADDED",
        index=1,
    )
]
