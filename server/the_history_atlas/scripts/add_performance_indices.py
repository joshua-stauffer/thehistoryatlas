#!/usr/bin/env python
"""
Database migration script to add performance-optimizing indices.

This script addresses performance bottlenecks in the following methods:
- Repository.get_tags_by_wikidata_ids
- Repository calls in HistoryApp.create_wikidata_event
- Repository.time_exists
- Repository.create_person
- Repository.create_place
- Repository.create_time

Usage:
    python add_performance_indices.py
"""

import logging
import os
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database connection string from environment variable
db_uri = os.environ.get("THA_DB_URI")
if not db_uri:
    logger.error("THA_DB_URI environment variable is not set")
    exit(1)

# Connect to the database
engine = create_engine(db_uri)

# Define the indices to add
INDICES = [
    # Index for faster lookup of tags by wikidata_id (used in get_tags_by_wikidata_ids)
    """
    CREATE INDEX IF NOT EXISTS idx_tags_wikidata_id 
    ON tags (wikidata_id)
    WHERE wikidata_id IS NOT NULL;
    """,
    
    # Composite index for time_exists method
    """
    CREATE INDEX IF NOT EXISTS idx_times_lookup 
    ON times (datetime, calendar_model, precision);
    """,
    
    # Index for tag instances by tag_id and story_order for faster sorting
    """
    CREATE INDEX IF NOT EXISTS idx_tag_instances_tag_id_story_order 
    ON tag_instances (tag_id, story_order);
    """,
    
    # Index for summaries by text for faster lookups
    """
    CREATE INDEX IF NOT EXISTS idx_summaries_text 
    ON summaries USING hash (text);
    """,
    
    # Index for citations by summary_id
    """
    CREATE INDEX IF NOT EXISTS idx_citations_summary_id 
    ON citations (summary_id);
    """,
    
    # Index for tag_names lookup
    """
    CREATE INDEX IF NOT EXISTS idx_tag_names_composite 
    ON tag_names (tag_id, name_id);
    """,
    
    # Time-related indices for faster related story lookups
    """
    CREATE INDEX IF NOT EXISTS idx_times_datetime 
    ON times (datetime);
    """,
    
    # Index for place coordinates
    """
    CREATE INDEX IF NOT EXISTS idx_places_coordinates 
    ON places (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
    """
]

# Add statistics collection for query planner
ANALYZE_TABLES = [
    "ANALYZE tags;",
    "ANALYZE times;",
    "ANALYZE tag_instances;",
    "ANALYZE summaries;",
    "ANALYZE citations;",
    "ANALYZE tag_names;",
    "ANALYZE places;"
]

def main():
    """Create the indices in the database."""
    logger.info("Starting to add performance indices to the database")
    
    with engine.connect() as connection:
        # Create indices
        for index_sql in INDICES:
            try:
                logger.info(f"Adding index: {index_sql.strip().split()[5]}")
                connection.execute(text(index_sql))
                connection.commit()
            except Exception as e:
                logger.error(f"Error creating index: {e}")
                connection.rollback()
        
        # Analyze tables for better query planning
        for analyze_sql in ANALYZE_TABLES:
            try:
                logger.info(f"Analyzing table: {analyze_sql}")
                connection.execute(text(analyze_sql))
                connection.commit()
            except Exception as e:
                logger.error(f"Error analyzing table: {e}")
                connection.rollback()
    
    logger.info("Finished adding performance indices")

if __name__ == "__main__":
    main() 