from collections import deque
import logging

log = logging.getLogger(__name__)


class EventComposer:
    
    def __init__(self,
        transaction_guid: str,
        app_version: str,
        user: str,
        timestamp: str
    ) -> None:
        """A class to manage the composition of synthetic events while handling 
        a single event."""
        self.events = deque()
        self.__meta = {
            'transaction_guid': transaction_guid,
            'app_version': app_version,
            'user': user,
            'timestamp': timestamp
        }
        log.debug(f'Created new logger for transaction {transaction_guid} by user {user}')

    def make_CITATION_ADDED(self,
        text: str,
        tags: list[str],
        meta: str,
    ) -> None:
        """Add a CITATION_ADDED event"""
        self.events.appendleft({
            'type': 'CITATION_ADDED',
            **self.__meta,
            'payload': {
                'text': text,
                'tags': tags,
                'meta': meta
            }
        })

    def make_PERSON_ADDED(self,
        citation_guid: str,
        person_guid: str,
        person_name: str,
        citation_start: int,
        citation_end: int
    ) -> None:
        """Add a PERSON_ADDED event"""
        self.events.append({
            'type': 'PERSON_ADDED',
            **self.__meta,
            'payload': {
                'citation_guid': citation_guid,
                'person_guid': person_guid,
                'person_name': person_name,
                'citation_start': citation_start,
                'citation_end': citation_end
            }
        })

    def make_PLACE_ADDED(self,
        citation_guid: str,
        place_guid: str,
        place_name: str,
        citation_start: int,
        citation_end: int,
        latitude: float,
        longitude: float
    ) -> None:
        """Add a PLACE_ADDED event"""
        self.events.append({
            'type': 'PLACE_ADDED',
            **self.__meta,
            'payload': {
                'citation_guid': citation_guid,
                'place_guid': place_guid,
                'place_name': place_name,
                'citation_start': citation_start,
                'citation_end': citation_end,
                'longitude': longitude,
                'latitude': latitude
            }
        })

    def make_TIME_ADDED(self,
        citation_guid: str,
        time_guid: str,
        time_name: str,
        citation_start: int,
        citation_end: int
    ) -> None:
        """Add a TIME_ADDED event"""
        self.events.append({
            'type': 'TIME_ADDED',
            **self.__meta,
            'payload': {
                'citation_guid': citation_guid,
                'time_guid': time_guid,
                'time_name': time_name,
                'citation_start': citation_start,
                'citation_end': citation_end
            }
        })

    def make_PERSON_TAGGED(self,
        citation_guid: str,
        person_guid: str,
        person_name: str,
        citation_start: int,
        citation_end: int
    ) -> None:
        """Add a PERSON_TAGGED event"""
        self.events.append({
            'type': 'PERSON_TAGGED',
            **self.__meta,
            'payload': {
                'citation_guid': citation_guid,
                'person_guid': person_guid,
                'person_name': person_name,
                'citation_start': citation_start,
                'citation_end': citation_end
            }
        })

    def make_PLACE_TAGGED(self,
        citation_guid: str,
        place_guid: str,
        place_name: str,
        citation_start: int,
        citation_end: int,
    ) -> None:
        """Add a PLACE_TAGGED event"""
        self.events.append({
            'type': 'PLACE_TAGGED',
            **self.__meta,
            'payload': {
                'citation_guid': citation_guid,
                'place_guid': place_guid,
                'place_name': place_name,
                'citation_start': citation_start,
                'citation_end': citation_end
            }
        })
    def make_TIME_TAGGED(self,
        citation_guid: str,
        time_guid: str,
        time_name: str,
        citation_start: int,
        citation_end: int
    ) -> None:
        """Add a TIME_TAGGED event"""
        self.events.append({
            'type': 'TIME_TAGGED',
            **self.__meta,
            'payload': {
                'citation_guid': citation_guid,
                'time_guid': time_guid,
                'time_name': time_name,
                'citation_start': citation_start,
                'citation_end': citation_end
            }
        })

    def make_META_ADDED(self,
        citation_guid: str,
        meta_guid: str,
        title: str,
        author: str,
        publisher: str,
        **kwargs
    ) -> None:
        """Add a META_ADDED event. Allows for passing arbitrary fields for
        maximum flexibility in describing sources."""
        self.events.append({
            'type': 'META_ADDED',
            **self.__meta,
            'payload': {
                'citation_guid': citation_guid,
                'meta_guid': meta_guid,
                'author': author,
                'publisher': publisher,
                'title': title,
                **kwargs
            }
        })