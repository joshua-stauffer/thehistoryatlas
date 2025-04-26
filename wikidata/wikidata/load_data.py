import argparse
import threading

from rocksdict.rocksdict import Options, Rdict, WriteOptions, WriteBatch
from wikidata.repository import Config
import json
import gzip


def load_data(
    data_path: str,
    db_path: str | None,
    start_index: int,
    stop_index: int,
    limit: int,
    repair: bool,
) -> None:
    if db_path:
        config = Config(DB_PATH=db_path)
    else:  # rely on env var
        config = Config()
    # Configure RocksDB options for bulk loading
    options = Options()
    options.create_if_missing(True)
    options.set_write_buffer_size(256 * 1024 * 1024)  # 256MB write buffer
    options.set_max_write_buffer_number(4)
    options.set_target_file_size_base(256 * 1024 * 1024)  # 256MB

    options.set_num_levels(6)
    options.optimize_for_point_lookup(
        4096
    )  # Optimize for point lookups with 4KB block cache
    options.set_disable_auto_compactions(
        True
    )  # Disable auto compactions during bulk load

    # concurrency
    # allow multiple threads to hit the memtable in parallel
    options.set_allow_concurrent_memtable_write(True)
    # threads yielding instead of spinning improves throughput
    options.set_enable_write_thread_adaptive_yield(True)

    # avoid `Too many open files` exception
    # run `ulimit -n 4096` prior to running this script if the error is encountered.
    options.set_max_open_files(-1)
    options.set_table_cache_num_shard_bits(4)  # Helps with file handle management

    if repair:
        Rdict.repair(path=config.DB_PATH, options=options)

    db = Rdict(path=config.DB_PATH, options=options)

    try:

        threads = [
            threading.Thread(
                target=process_chunk, args=(
                   data_path,
                    db,
                    limit,
                    start_index
                )
            )
            for start_index in range(start_index, stop_index, limit)
        ]
        for t in threads: t.start()
        for t in threads: t.join()
        options.set_disable_auto_compactions(False)
        db.compact_range()

        # Close the database
        db.close()
    except Exception as e:
        print(f"Exiting on exception: {e}")
        db.close()


def process_chunk(data_path: str, db: Rdict, limit: int,  start_index):
    # Configure write options for bulk loading
    write_options = WriteOptions()
    write_options.disable_wal = True  # Disable write-ahead log for bulk loading
    # Process and insert WikiData entities in batches
    BATCH_SIZE = 10_000
    batch = WriteBatch()
    with gzip.open(data_path, "rt", encoding="utf-8") as f:
        for index, line in enumerate(f):
            if index < start_index:
                continue
            elif index > start_index + limit:
                break
            line = line.strip().rstrip(",")
            try:
                entity = json.loads(line)
                entity_id = entity["id"]
                key = entity_id.encode("utf-8")
                value = json.dumps(entity).encode("utf-8")
                batch.put(key=key, value=value)
                if len(batch) >= BATCH_SIZE:
                    db.write(batch, write_options)
                    batch = WriteBatch()
                    print(f"Processed {index} entities")
            except json.JSONDecodeError:
                continue
    if len(batch):
        db.write(batch, write_options)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build WikiData JSON store from dump.")
    parser.add_argument(
        "--data-path", type=str, dest="data_path", help="Path to the dump file."
    )
    parser.add_argument(
        "--db-path",
        type=str,
        required=False,
        dest="db_path",
        help="Path to the RocksDB database. Defaults to DB_PATH env variable if not present.",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        dest="start_index",
        help="Start index. Defaults to 0.",
        default=0,
    )
    parser.add_argument(
        "--stop-index",
        type=int,
        dest="stop_index",
        help="Stop index. Defaults to 200,000,000.",
        default=200_000_000,
    )
    parser.add_argument(
        "--limit",
        type=int,
        dest="limit",
        help="Limit number of entities. Defaults to 10,000,000.",
        default=10_000_000,
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Attempt to first repair any broken indices.",
        required=False,
    )
    args = parser.parse_args()

    load_data(
        data_path=args.data_path,
        db_path=args.db_path,
        start_index=args.start_index,
        stop_index=args.stop_index,
        limit=args.limit,
        repair=args.repair,
    )
