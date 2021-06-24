"""Component responsible for fielding queries on the read database.

Tuesday, May 4th 2021
"""

import logging
from .errors import UnknownQueryError, UnknownManifestTypeError

log = logging.getLogger(__name__)

class QueryHandler:

    def __init__(self, database_instance):
        self._db = database_instance
        self._query_handlers = self._map_query_handlers()

    def handle_query(self, query) -> dict:
        """Process incoming queries and return results"""
        log.info(f'Handling a query: {query}')
        query_type = query.get('type')
        handler = self._query_handlers.get(query_type)
        if not handler:
            raise UnknownQueryError(query_type)
        return handler(query)       

    def _map_query_handlers(self):
        """A dict of known query types and the methods which process them"""
        return {
            'GET_SUMMARIES_BY_GUID': self._handle_get_summaries_by_guid,
            'GET_CITATION_BY_GUID': self._handle_get_citation_by_guid,
            'GET_MANIFEST': self._handle_get_manifest, 
            'GET_GUIDS_BY_NAME': self._handle_get_guids_by_name,
            'GET_GUIDS_BY_NAME_BATCH': self._handle_get_guids_by_name_batch,
        }

    def _handle_get_summaries_by_guid(self, query):
        """Fetch a series of summaries by a list of guids"""

        summary_guids = query['payload']['summary_guids']
        res = self._db.get_summaries(summary_guids=summary_guids)
        return {
            'type': 'SUMMARIES_BY_GUID',
            'payload': {
                'summaries': res
            }
        }

    def _handle_get_citation_by_guid(self, query):
        """Fetch a citation and its associated data by guid"""
        citation_guid = query['payload']['citation_guid']
        res = self._db.get_citation(citation_guid)
        return {
            'type': 'CITATION_BY_GUID',
            # NOTE: refactored for issue 11 on 6.14.21
            'payload': { 'citation': res}
        }
    
    def _handle_get_manifest(self, query):
        """Fetch a list of citation guids for a given focus"""
        entity_type = query['payload']['type']
        guid = query['payload']['guid']
        if entity_type == 'TIME':
            manifest, timeline = self._db.get_manifest_by_time(guid)
        elif entity_type == 'PLACE':
            manifest, timeline = self._db.get_manifest_by_place(guid)
        elif entity_type == 'PERSON':
            manifest, timeline = self._db.get_manifest_by_person(guid)
        else:
            raise UnknownManifestTypeError(entity_type)
        print('in handle query, timeline is ', timeline)
        return {
            'type': 'MANIFEST',
            'payload': {
                'guid': guid,
                'citation_guids': manifest,
                'timeline': timeline
            }
        }

    def _handle_get_guids_by_name(self, query):
        """Fetch a list of guids associated with a given name"""
        name = query['payload']['name']
        res = self._db.get_guids_by_name(name)
        entity_summaries = self._db.get_entity_summary_by_guid_batch(res)
        return {
            'type': 'GUIDS_BY_NAME',
            'payload': {
                'guids': res,
                'summaries': entity_summaries
            }
        }

    def _handle_get_guids_by_name_batch(self, query):
        """Fetch GUIDs for a series of names."""
        name_list = query['payload']['names']
        res = dict()
        for name in name_list:
            r = self._db.get_guids_by_name(name)
            res[name] = r
        return {
            'type': 'GUIDS_BY_NAME_BATCH',
            'payload': {
                'names': res
            }
        }