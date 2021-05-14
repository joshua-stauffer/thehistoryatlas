"""Class tasked with resolving processed entities into known GUIDs 

May 14th, 2021"""

import asyncio
from uuid import uuid4

ENTITY_TYPES = ['PERSON', 'PLACE', 'TIME']
EntityDict = dict[str, list[dict]]

class Resolver:

    def __init__(self, query_geo, query_readmodel):
        self._query_geo = query_geo
        self._query_readmodel = query_readmodel

    async def query(self,
        entities: EntityDict
        ) -> EntityDict:
        """Accepts a dict with keys PERSON, PLACE, TIME corresponding to lists 
        of entities. Returns the entity dict with any known GUIDs added to 
        each entity"""
        # Query against the ReadModel's known entities
        names = self._get_names(entities, key=None)
        rm_query = {
            'type': 'GET_GUIDS_BY_NAME_BATCH',
            'payload': { 'names': names }
        }
        readmodel_res = await self._query_readmodel(rm_query)
        name_map = readmodel_res['payload']['names']
        # update our entity dict with the results
        entities_with_guids = self._add_guids(
                                        entities=entities,
                                        name_map=name_map)

        # if any places haven't resolved to a known place, look them up
        # with the geo service
        place_names_to_resolve = \
            [e['text'] for e in entities_with_guids['PLACES'] if len(e['guids']) == 0]
        if len(place_names_to_resolve):
            geo_query = {
                'type': 'GET_COORDS_FROM_NAME_BATCH',
                'payload': { 'names' : place_names_to_resolve }
            }
            geo_res = self._query_geo(geo_query)
            geo_map = geo_res['payload']['names']
            entities_with_coords = self._add_guids(
                                        entities=entities_with_guids,
                                        val_map=geo_map,
                                        val_key='coords',
                                        entity_key='PLACES')
        else:
            entities_with_coords = entities_with_guids
        return entities_with_coords

    @staticmethod
    def _get_names(
        entities: EntityDict,
        key: str=None
        ) -> EntityDict:
        """Returns a single list of all names found within entities: EntityDict[key]['text']
        If no key is passed returns results for keys defined in ENTITY_TYPES"""
        names = list()
        if not key:
            keys = ENTITY_TYPES
        else:
            keys = [key]
        for k in keys:
            names.extend(entity['text'] for entity in entities[k])
        return names

    @staticmethod
    def _add_guids(
        entities: EntityDict,
        val_map: dict[str, list[str]],
        val_key: str,
        entity_key: str=None,
        ) -> EntityDict:
        """Adds values from val_map[x] to entities[entity_key][x][val_key]

        entities: EntityDict:
            key: ENTITY_TYPE
            val: list[dict]
                    (dict includes the field 'text', which is the name
                    we're interested in resolving)

        val_map:
            key: str (name)
            val: list[str]
        """
        if entity_key:
            keys = [entity_key]
        else:
            keys = ENTITY_TYPES
        for k in keys:
            for tag in entities[k]:
                name = tag['text']
                tag[val_key] = val_map[name]
        return entities
