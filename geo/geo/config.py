import os
from tha_config import Config as ConfigBase

class Config(ConfigBase):
    def __init__(self):
        super().__init__()
        self.GEONAMES_URL = os.environ.get('GEONAMES_URL', '')

