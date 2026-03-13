import os


class Config:
    def __init__(self):
        self.claude_api_key = os.environ.get("CLAUDE_API_KEY")
        if not self.claude_api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is required")

        self.tha_api_key = os.environ.get("THA_API_KEY")
        if not self.tha_api_key:
            raise ValueError("THA_API_KEY environment variable is required")

        self.server_url = os.environ.get("THA_SERVER_URL", "http://localhost:8000")
        self.geonames_username = os.environ.get("GEONAMES_USERNAME")
