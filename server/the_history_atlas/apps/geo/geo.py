import logging
from the_history_atlas.apps.geo.config import Config
from the_history_atlas.apps.geo.state.database import Database
from the_history_atlas.apps.geo.geonames import GeoNames
from the_history_atlas.apps.geo.state.query_handler import QueryHandler


logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


class GeoService:
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config)
        self.query_handler = QueryHandler(self.db)
        db_update_timestamp = self.db.get_last_update_timestamp()
        if db_update_timestamp is None:
            # the geo database is empty, fill it!
            log.info("The Geo database is empty, filling it now")
            geo = GeoNames(self.config.GEONAMES_URL)
            city_rows = geo.build()
            self.db.build_db(city_rows)
            log.info("Geo database filled.")
        else:
            log.info(f"Geo database was last filled on {db_update_timestamp}")
