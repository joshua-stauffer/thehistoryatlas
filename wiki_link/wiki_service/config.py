import os


class WikiServiceConfig:
    def __init__(self):
        self.DB_URI = os.environ.get("THA_DB_URI")
        self.DEBUG = bool(os.environ.get("DEBUG"))
        self.WIKIDATA_SEARCH_LIMIT = 10
        self.WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
        self.USER_ID = "a5749422-65c1-4ce5-a582-7b08c3e71de6"
        self.username = os.environ.get("WIKILINK_USERNAME")
        self.password = os.environ.get("WIKILINK_PASSWORD")
        self.base_url = os.environ.get("WIKILINK_BASE_URL")
        self.server_base_url = os.environ.get("SERVER_BASE_URL", "localhost:8000")
