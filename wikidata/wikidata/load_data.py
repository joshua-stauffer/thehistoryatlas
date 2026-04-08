import argparse
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from rocksdict.rocksdict import Options, Rdict, WriteOptions, WriteBatch
from wikidata.repository import Config
import json
import gzip


def load_data(
    data_path: str,
    db_path: str | None,
    start_index: int,
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

    # avoid `Too many open files` exception
    # run `ulimit -n 10240` prior to running this script if the error is encountered.
    options.set_max_open_files(10240)
    options.set_table_cache_num_shard_bits(4)  # Helps with file handle management

    try:
        db = Rdict(path=config.DB_PATH, options=options)

        # Configure write options for bulk loading
        write_options = WriteOptions()
        write_options.disable_wal = True  # Disable write-ahead log for bulk loading

        # Process and insert WikiData entities in batches
        BATCH_SIZE = 100_000
        batch = WriteBatch()
        tz = ZoneInfo("Europe/Paris")
        absolute_start = datetime.now(tz=tz)
        total_expected_batches = 117_082_035 / BATCH_SIZE
        batch_start = datetime.now(tz=tz)
        batch_times = []

        with gzip.open(data_path, "rt", encoding="utf-8") as f:
            for index, line in enumerate(f):
                if index < start_index:
                    continue
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
                        batch_time = (datetime.now(tz=tz) - batch_start).total_seconds()
                        print(f"Processed to index {index}: {batch_time} seconds.")
                        batch_times.append(batch_time)
                        batch_start = datetime.now(tz=tz)
                        if len(batch_times) % 10 == 0 and len(batch_times):
                            average_batch_time = sum(batch_times) / len(batch_times)
                            expected_finish_time = absolute_start + timedelta(
                                seconds=(total_expected_batches * average_batch_time)
                            )
                            print(
                                f"Average batch in {average_batch_time} seconds, done at {expected_finish_time}"
                            )
                except json.JSONDecodeError:
                    continue

        if len(batch):
            db.write(batch, write_options)

        options.set_disable_auto_compactions(False)

        # Close the database
        db.close()
    except Exception as e:
        print(f"Exiting on exception: {e}")
        db.close()


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
    args = parser.parse_args()

    load_data(
        data_path=args.data_path,
        db_path=args.db_path,
        start_index=args.start_index,
    )
