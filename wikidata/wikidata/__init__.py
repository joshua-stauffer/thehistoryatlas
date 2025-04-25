"""
WikiData API - A package for accessing WikiData information.
"""

__version__ = "0.1.0"

from .repository import Repository, Config
from .wikidata_app import WikiDataApp

__all__ = ["Repository", "Config", "WikiDataApp"]
