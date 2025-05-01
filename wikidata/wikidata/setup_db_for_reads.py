import os

from rocksdict import Options, Rdict, BlockBasedOptions, Cache
from wikidata.repository import Config


def configure_for_read(config: Config):
    opts, cols = Options.load_latest(config.DB_PATH)

    opts.set_disable_auto_compactions(False)
    opts.increase_parallelism(os.cpu_count())
    opts.set_max_background_jobs(10)
    opts.set_max_open_files(10240)
    opts.set_table_cache_num_shard_bits(6)
    opts.set_allow_mmap_reads(True)

    db = Rdict(
        config.DB_PATH,
        options=opts,
    )
    print("starting flush")
    db.flush()
    print("compacting range")
    db.compact_range(begin=None, end=None)
    print("finished compacting range")

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


if __name__ == "__main__":
    configure_for_read(Config())
