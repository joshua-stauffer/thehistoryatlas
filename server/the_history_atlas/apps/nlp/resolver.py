import logging

from the_history_atlas.apps.domain.models.nlp.text_analysis import TextAnalysisResponse
from the_history_atlas.apps.domain.models.readmodel.queries import GetEntityIDsByNames
from the_history_atlas.apps.readmodel import ReadModelApp

log = logging.getLogger(__name__)

ENTITY_TYPES = ["PERSON", "PLACE", "TIME"]
TextMap = dict[str, list[dict]]


class Resolver:
    def __init__(
        self, text: str, text_map: dict, boundaries: list, readmodel_app: ReadModelApp
    ) -> None:
        self._readmodel_app = readmodel_app

        # data
        self._text = text
        self._text_map = text_map
        self._boundaries = boundaries
        self._tag_view = list()  # utility view to work with all tags at once
        [self._tag_view.extend(tag_list) for tag_list in text_map.values()]

    def run(self) -> TextAnalysisResponse:

        # TODO: if names aren't found for a service request, shouldn't send it.
        names = self._get_names(self._text_map)
        entity_ids_by_name = self._readmodel_app.get_entity_ids_by_names(
            query=GetEntityIDsByNames(names=names)
        )
        self._add_guids(entity_ids_by_name.names)

        geo_names = self._get_names(self._text_map, key="PLACE")

        coords_by_name = self._readmodel_app.get_coords_by_names(names=geo_names)
        self._add_coords(coords_by_name.coords)

        return TextAnalysisResponse.parse_obj(
            {
                "text_map": self._text_map,
                "text": self._text,
                "boundaries": self._boundaries,
            }
        )

    @staticmethod
    def _get_names(entities: TextMap, key: str = None) -> list[str]:
        names = list()
        if not key:
            keys = ENTITY_TYPES
        else:
            keys = [key]
        for k in keys:
            names.extend(entity["text"] for entity in entities[k])
        return names

    def _add_guids(self, name_map: dict) -> None:
        """Add GUIDs received from a service to the current text_map"""
        for tag in self._tag_view:
            tag_name = tag["text"]
            # we need every tag to have a guids list, whether or not we found results
            tag["guids"] = name_map.get(tag_name)

    def _add_coords(self, coord_map: dict) -> None:
        """Add coordinates received from GeoService to the current text_map.
        If no geo name was found, the coordinate field will not be added."""
        for tag in self._tag_view:
            tag_name = tag["text"]
            if coords := coord_map.get(tag_name):
                tag["coords"] = coords
