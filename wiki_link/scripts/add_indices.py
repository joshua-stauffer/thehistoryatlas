#!/usr/bin/env python
import os
from sqlalchemy import create_engine, text

# Get database connection string from environment variable
db_uri = os.environ.get("THA_DB_URI")
if not db_uri:
    raise ValueError("THA_DB_URI environment variable must be set")

# Create engine
engine = create_engine(db_uri)

# Create indices
with engine.connect() as conn:
    # Check if indices already exist before creating them
    existing_indices = conn.execute(
        text(
            """
        SELECT indexname FROM pg_indexes 
        WHERE tablename IN ('factory_results', 'created_events', 'wiki_queue')
        """
        )
    ).fetchall()
    existing_indices = [idx[0] for idx in existing_indices]

    # Add index on (wiki_id, factory_label) to factory_results table
    if "idx_factory_results_wiki_id_factory_label" not in existing_indices:
        print("Creating index on factory_results(wiki_id, factory_label)...")
        conn.execute(
            text(
                """
            CREATE INDEX idx_factory_results_wiki_id_factory_label 
            ON factory_results (wiki_id, factory_label)
            """
            )
        )
    else:
        print("Index on factory_results(wiki_id, factory_label) already exists")

    # Add index on primary_entity_id to created_events table
    if "idx_created_events_primary_entity_id" not in existing_indices:
        print("Creating index on created_events(primary_entity_id)...")
        conn.execute(
            text(
                """
            CREATE INDEX idx_created_events_primary_entity_id 
            ON created_events (primary_entity_id)
            """
            )
        )
    else:
        print("Index on created_events(primary_entity_id) already exists")

    # Add index on factory_result_id to created_events table
    if "idx_created_events_factory_result_id" not in existing_indices:
        print("Creating index on created_events(factory_result_id)...")
        conn.execute(
            text(
                """
            CREATE INDEX idx_created_events_factory_result_id 
            ON created_events (factory_result_id)
            """
            )
        )
    else:
        print("Index on created_events(factory_result_id) already exists")

    # Additional indices for get_server_id_by_event_label performance

    # Add index on factory_label to factory_results table
    if "idx_factory_results_factory_label" not in existing_indices:
        print("Creating index on factory_results(factory_label)...")
        conn.execute(
            text(
                """
            CREATE INDEX idx_factory_results_factory_label 
            ON factory_results (factory_label)
            """
            )
        )
    else:
        print("Index on factory_results(factory_label) already exists")

    # Add index on secondary_entity_id to created_events table
    if "idx_created_events_secondary_entity_id" not in existing_indices:
        print("Creating index on created_events(secondary_entity_id)...")
        conn.execute(
            text(
                """
            CREATE INDEX idx_created_events_secondary_entity_id 
            ON created_events (secondary_entity_id)
            """
            )
        )
    else:
        print("Index on created_events(secondary_entity_id) already exists")

    # Add index on server_id to created_events table
    if "idx_created_events_server_id" not in existing_indices:
        print("Creating index on created_events(server_id)...")
        conn.execute(
            text(
                """
            CREATE INDEX idx_created_events_server_id 
            ON created_events (server_id)
            WHERE server_id IS NOT NULL
            """
            )
        )
    else:
        print("Index on created_events(server_id) already exists")

    # New indices for improved performance

    # Add compound index for event_exists method
    if "idx_factory_results_wiki_id_factory_label_version" not in existing_indices:
        print(
            "Creating compound index on factory_results(wiki_id, factory_label, factory_version)..."
        )
        conn.execute(
            text(
                """
            CREATE INDEX idx_factory_results_wiki_id_factory_label_version 
            ON factory_results (wiki_id, factory_label, factory_version)
            """
            )
        )
    else:
        print(
            "Index on factory_results(wiki_id, factory_label, factory_version) already exists"
        )

    # Add GIN index on wiki_queue.errors for faster JSON operations (used in report_queue_error)
    if "idx_wiki_queue_errors" not in existing_indices:
        print("Creating GIN index on wiki_queue(errors)...")
        conn.execute(
            text(
                """
            CREATE INDEX idx_wiki_queue_errors
            ON wiki_queue USING GIN (errors)
            """
            )
        )
    else:
        print("GIN Index on wiki_queue(errors) already exists")

    # Add index on wiki_queue.entity_type to speed up type-based queries
    if "idx_wiki_queue_entity_type" not in existing_indices:
        print("Creating index on wiki_queue(entity_type)...")
        conn.execute(
            text(
                """
            CREATE INDEX idx_wiki_queue_entity_type
            ON wiki_queue (entity_type)
            """
            )
        )
    else:
        print("Index on wiki_queue(entity_type) already exists")

    conn.commit()

print("Indices created successfully")
