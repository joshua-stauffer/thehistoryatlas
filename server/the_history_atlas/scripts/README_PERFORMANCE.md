# Performance Optimization Migration

This directory contains scripts to address performance bottlenecks in The History Atlas database operations.

## Identified Bottlenecks

The following methods were identified as performance bottlenecks:

1. `Repository.get_tags_by_wikidata_ids` - Slow lookup of tags by Wikidata IDs
2. Repository calls in `HistoryApp.create_wikidata_event` - Multiple database operations with unoptimized queries
3. `Repository.time_exists` - Inefficient lookup of time combinations
4. `Repository.create_person`, `Repository.create_place`, `Repository.create_time` - Potentially slow insertion operations

## Optimizations Applied

The `add_performance_indices.py` script adds the following database optimizations:

1. `idx_tags_wikidata_id` - Index for faster lookup of tags by wikidata_id
2. `idx_times_lookup` - Composite index for faster time lookups by datetime/calendar/precision
3. `idx_tag_instances_tag_id_story_order` - Speeds up story order operations
4. `idx_summaries_text` - Hash index for faster text lookups
5. `idx_citations_summary_id` - Faster citation lookup by summary
6. `idx_tag_names_composite` - Optimizes tag name associations
7. `idx_times_datetime` - Improves time-based story lookups
8. `idx_places_coordinates` - Faster spatial searches for places

The script also runs ANALYZE on relevant tables to improve query planning.


## Additional Considerations

These optimizations focus on database-level improvements. Additional application-level optimizations could include:

1. Batch operations for creating multiple entities at once
2. Caching frequently accessed data
3. Asynchronous processing for non-critical operations

## Monitoring

After applying these optimizations, monitor the performance of the identified methods. Further tuning may be necessary based on actual query patterns and data growth. 