import json
import os
from typing import Dict, Optional, Any
from rocksdict import Rdict, Options, AccessType, BlockBasedOptions, Cache
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    DB_PATH: str = "./data/rocks_db"


class Repository:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._db = None
        self._open_db()

    def _open_db(self):
        if self._db is None:
            opts, cols = Options.load_latest(self.config.DB_PATH)
            opts.set_disable_auto_compactions(False)
            opts.increase_parallelism(os.cpu_count())
            opts.set_max_background_jobs(10)
            opts.set_max_open_files(10240)
            opts.set_table_cache_num_shard_bits(6)
            opts.set_allow_mmap_reads(True)
            table_opts = BlockBasedOptions()

            # 2) Increase block size for fewer seeks
            table_opts.set_block_size(16 * 1024)  # 16 KiB blocks instead of 4 KiB

            # 3) Add a per-block bloom filter
            table_opts.set_bloom_filter(bits_per_key=10, block_based=True)

            # 4) Keep index & filter blocks pinned in cache
            table_opts.set_cache_index_and_filter_blocks(True)
            table_opts.set_pin_l0_filter_and_index_blocks_in_cache(True)

            # 5) Give yourself a big LRU cache (adjust to your available RAM)
            table_opts.set_block_cache(Cache(4 * 1024 * 1024 * 1024))  # 4 GiB

            # 6) Plug it into your main Options
            opts.set_block_based_table_factory(table_opts)
            self._db = Rdict(
                self.config.DB_PATH, options=opts, access_type=AccessType.read_only()
            )

    def close(self):
        """Close the database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None

    def __del__(self):
        self.close()

    def get(self, id: str) -> dict:
        """
        Retrieve a document by its ID from the repository.

        Args:
            id: The ID of the document to retrieve

        Returns:
            dict: The document data

        Raises:
            KeyError: If the document with the given ID doesn't exist
        """
        try:
            self._open_db()
            value = self._db.get(id.encode("utf-8"))
            if value is None:
                raise KeyError(f"No document found with id: {id}")
            return json.loads(value.decode("utf-8"))
        except Exception as e:
            if isinstance(e, KeyError):
                raise
            raise KeyError(f"Failed to retrieve document with id {id}: {str(e)}")

    def put(self, id: str, data: dict) -> None:
        """
        Store a document in the repository with the given ID.

        Args:
            id: The ID of the document to store
            data: The document data to store

        Raises:
            ValueError: If the data is not a dictionary
            RuntimeError: If there was an error storing the data
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        try:
            self._open_db()
            self._db.put(id.encode("utf-8"), json.dumps(data).encode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Failed to store document with id {id}: {str(e)}")
