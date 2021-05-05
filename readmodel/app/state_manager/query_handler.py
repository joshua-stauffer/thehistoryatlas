"""Component responsible for fielding queries on the read database.

Tuesday, May 4th 2021
"""

import logging
from .errors import UnknownQueryError

log = logging.getLogger(__name__)

class QueryHandler:

    def __init__(self, database_instance):
        self._db = database_instance
        self._query_handlers = self._map_query_handlers()

    def _map_event_handlers(self):
        """A dict of known query types and the methods which process them"""
        return {
            'GET_CITATIONS_BY_GUID': self._handle_get_citations_by_guid,

        }

    def _handle_get_citations_by_guid(self, query):
        """Fetch a series of citations and their associated data by guid"""
        citation_guids = query['payload']['citation_guids']
        res = self._db.get_citations(citation_guids)
        return {
            'type': 'CITATIONS_BY_GUID',
            'payload': {
                'citations': res
            }
        }