import os


class WikiServiceConfig:
    def __init__(self):
        self.DB_URI = os.environ.get("THA_DB_URI")
        self.DEBUG = bool(os.environ.get("DEBUG"))
        self.WIKIDATA_SEARCH_LIMIT = int(os.environ.get("WIKIDATA_SEARCH_LIMIT", 1000))
        self.WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
        self.USER_ID = "a5749422-65c1-4ce5-a582-7b08c3e71de6"
        self.username = os.environ.get("WIKILINK_USERNAME")
        self.password = os.environ.get("WIKILINK_PASSWORD")
        self.base_url = os.environ.get("WIKILINK_BASE_URL")
        self.server_base_url = os.environ.get(
            "SERVER_BASE_URL", "http://localhost:8000"
        )
        self.wikidata_base_url = os.environ.get(
            "WIKIDATA_BASE_URL", "https://www.wikidata.org/w/rest.php/wikibase"
        )
        self.contact = os.environ.get("WIKILINK_CONTACT", "https://historyatlas.org")
        # Token refresh configuration
        self.TOKEN_REFRESH_BY = int(os.environ.get("REFRESH_BY", 7200))

        # Cache configuration
        self.ENTITY_CACHE_SIZE = int(os.environ.get("THA_ENTITY_CACHE_SIZE", "1000"))
        self.LABEL_CACHE_SIZE = int(os.environ.get("THA_LABEL_CACHE_SIZE", "5000"))
        self.DESCRIPTION_CACHE_SIZE = int(
            os.environ.get("THA_DESCRIPTION_CACHE_SIZE", "5000")
        )
