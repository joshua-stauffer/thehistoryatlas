"""Component responsible for handling incoming queries and directing them to
the correct database resource.

Sunday, May 23rd 2021
"""
import logging
from geo.errors import MessageMissingTypeError
from geo.errors import MessageMissingPayloadError
from geo.errors import UnknownQueryError

log = logging.getLogger(__name__)


class QueryHandler:
    def __init__(self, db):
        self._db = db
        self._query_handlers = self._map_query_handlers()

    def handle_query(self, query: dict) -> dict:
        """Direct incoming queries to the correct database resource."""
        log.info(f"Handling a query: {query}")
        query_type = query.get("type")
        payload = query.get("payload")
        if query_type == None:
            raise MessageMissingTypeError
        if payload == None:
            raise MessageMissingPayloadError
        handler = self._query_handlers.get(query_type)
        if not handler:
            raise UnknownQueryError(query_type)
        return handler(payload)

    def _map_query_handlers(self):
        """Create a dict of known query types and the methods to handle them."""
        return {
            "GET_COORDS_BY_NAME": self._handle_get_coords_by_name,
            "GET_COORDS_BY_NAME_BATCH": self._handle_get_coords_by_name_batch,
        }

    def _handle_get_coords_by_name(self, payload):
        """Get a list of coordinates for a single name"""
        # now we know the type of message, we want to throw an error if the
        # field is missing.
        name = payload["name"]
        coords = self._db.get_coords_by_name(name)
        return {"type": "COORDS_BY_NAME", "payload": {"coords": {name: coords}}}

    def _handle_get_coords_by_name_batch(self, payload):
        """Get a list of coordinates for a list of names"""
        # now we know the type of message, we want to throw an error if the
        # field is missing.
        names = payload["names"]
        coords_dict = self._db.get_coords_by_name_batch(names)
        return {"type": "COORDS_BY_NAME_BATCH", "payload": {"coords": coords_dict}}
