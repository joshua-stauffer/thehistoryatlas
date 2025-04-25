import argparse

from wikidata.repository import Repository, Config
import json
import gzip


def load_data(data_path: str, db_path: str | None) -> None:
    if db_path:
        config = Config(DB_PATH=db_path)
    else:  # rely on env var
        config = Config()
    repository = Repository(config)
    with gzip.open(data_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line in "[" or line == "]":
                continue
            if line.endswith(","):
                line = line[:-1]

            try:
                entity = json.loads(line)
                entity_id = entity["id"]
                repository.put(id=entity_id, data=entity)

            except json.JSONDecodeError:
                continue


def stats(db_path: str | None) -> None:
    if db_path:
        config = Config(DB_PATH=db_path)
    else:  # rely on env var
        config = Config()


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
    args = parser.parse_args()
    load_data(
        data_path=args.data_path,
        db_path=args.db_path,
    )
