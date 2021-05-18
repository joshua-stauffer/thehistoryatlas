"""Class tasked with resolving processed entities into known GUIDs 

May 14th, 2021"""

from collections.abc import Callable

ENTITY_TYPES = ['PERSON', 'PLACE', 'TIME']
TextMap = dict[str, list[dict]]

class Resolver:
    """Class corresponding to the lifetime of an API request. 
    Resolver.has_resolved flag indicates if component lifecycle has completed.
    """

    def __init__(self,
        text: str,
        text_map: dict,
        corr_id: str,
        pub_func: Callable,
        query_geo: Callable,
        query_readmodel: Callable
        ) -> None:
        """Create a session to manage the state of an API query between 
        receipt of request and returning the response."""
        # unique identifier for this instance of the class
        self._corr_id = corr_id
        # data
        self._text = text
        self._text_map = text_map
        self._tag_view = list()     # utility view to work with all tags at once
        [self._tag_view.extend(tag_list) for tag_list in text_map.values()]
        # methods and properties for interacting with other services
        self._pub_func = pub_func
        self._query_geo = query_geo
        self._geo_complete = False
        self._query_rm = query_readmodel
        self._rm_complete = False

    @property
    def has_resolved(self):
        """Flag to alert main application that component lifecycle is over."""
        return all([self._geo_complete, self._rm_complete])

    async def open_queries(self) -> None:
        """Call when a new query session is created. Opens query requests to
        the ReadModel and the GeoService."""
        all_names = self._get_names(self.text_map)
        geo_names = self._get_names(self.text_map, key='PLACES')
        rm_query = {
            'type': 'GET_COORDS_FROM_NAME_BATCH',
            'payload': { 'names': all_names }
        }
        geo_query = {
            'type': 'GET_GUIDS_BY_NAME_BATCH',
            'payload': { 'names': geo_names }
        }
        await self._query_rm(
            query=rm_query,
            corr_id=self.corr_id)
        await self._query_geo(
            query=geo_query,
            corr_id=self.corr_id)

    async def handle_response(self,
        response: dict
        ) -> None:
        """Handles an incoming query response and updates session state accordingly.
        If incoming query response is the last we were waiting for, publishes the
        results back to the original requester based on reply_to field they provided."""

        resp_type = response.get('type')
        if resp_type == 'COORDS_FROM_NAME_BATCH':
            if self.geo_complete == True:
                return  # this query has already been resolved
            self._text_map['coords'] = response['payload']['names']
            self._geo_complete = True
        elif resp_type == 'GUIDS_BY_NAME_BATCH':
            if self._rm_complete == True:
                return  # this query has already been resolved
            name_map = response['payload']['names']
            self._add_guids(name_map)
            self._rm_complete = True
        else:
            raise Exception(f'Unknown response type {resp_type}')

        if self.has_resolved:
            # send result back to service that requested this query
            await self._pub_func({
                'type': 'TEXT_PROCESSED',
                'payload': {
                    'text_map': self._text_map,
                    'text': self._text
                }})

    @staticmethod
    def _get_names(
        entities: TextMap,
        key: str=None
        ) -> TextMap:
        """Returns a single list of all names found within entities: TextMap[key]['text']
        If no key is passed returns results for keys defined in ENTITY_TYPES"""
        names = list()
        if not key:
            keys = ENTITY_TYPES
        else:
            keys = [key]
        for k in keys:
            names.extend(entity['text'] for entity in entities[k])
        return names

    def _add_guids(self,
        name_map: dict
        ) -> None:
        """Add GUIDs received from a service to the current text_map"""
        for tag in self._tag_view:
            tag_name = tag['text']
            # we need every tag to have a guids list, whether or not we found results
            tag['guids'] = name_map.get(tag_name)

    def _add_coords(self,
        coord_map: dict
        ) -> None:
        """Add coordinates received from GeoService to the current text_map.
        If no geo name was found, the coordinate field will not be added."""
        for tag in self._tag_view:
            tag_name = tag['text']
            if coords := coord_map.get(tag_name):
                tag['coords'] = coords
