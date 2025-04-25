# Wikidata Repository

A simple key/value store repository built on top of RocksDB for efficient storage and retrieval of data.

## Installation

```bash
pip install -e .
```

## Configuration

The repository uses a RocksDB instance for storage. By default, it looks for the database at `./data/rocks_db`. 
You can customize this by creating a custom Config object:

```python
from wikidata import Config, Repository

config = Config(db_path="/path/to/your/rocks_db")
repo = Repository(config=config)
```

## Usage

```python
from wikidata import Repository

# Create a repository using the default config
repo = Repository()

# Get an item by ID
try:
    item = repo.get("item_id")
    print(item)
except KeyError:
    print("Item not found")

# Store an item
item_data = {"id": "item_id", "name": "Test Item", "value": 42}
repo.put("item_id", item_data)

# Update an existing item
updated_data = {"id": "item_id", "name": "Updated Item", "value": 100}
repo.put("item_id", updated_data)

# Close the repository when done (optional, will be closed on garbage collection)
repo.close()
```

## Running Tests

```bash
pytest
``` 