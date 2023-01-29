from tha_config import Config


class WikiServiceConfig(Config):
    def __init__(self):
        super().__init__()
        self.WIKIDATA_SEARCH_LIMIT = 10
        self.WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
        self.USER_ID = "a5749422-65c1-4ce5-a582-7b08c3e71de6"
