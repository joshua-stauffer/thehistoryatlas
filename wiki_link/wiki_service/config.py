import os

from the_history_atlas.apps.config import Config


class WikiServiceConfig(Config):
    def __init__(self):
        super().__init__()
        self.WIKIDATA_SEARCH_LIMIT = 10
        self.WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
        self.USER_ID = "a5749422-65c1-4ce5-a582-7b08c3e71de6"
        self.username = os.environ.get("WIKILINK_USERNAME")
        self.password = os.environ.get("WIKILINK_PASSWORD")
        self.base_url = os.environ.get("WIKILINK_BASE_URL")
        # if not all([self.base_url, self.username, self.password]):
        #     raise EnvironmentError("Missing environment variables")
