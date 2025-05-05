# WikiService Event Factory Tracing

This module provides tracing capabilities for the WikiService event factory system. 
It allows gathering metrics about entity processing and event creation to better
understand performance and behavior of the event creation system.

## Overview

The tracing system captures:

- How many total entities are processed
- How many events are created, of which type, for each entity
- Statistics about the frequency of each event type
- The average amount of time it took to process each entity
- The average amount of time it took to process each EventFactory

## Usage

### Enabling Tracing

Tracing is integrated with the WikiService's existing tracing system. To enable it:

```bash
# Enable tracing with a 0ms threshold (capture all traces)
python wiki_link/scripts/enable_tracing.py --enable --threshold 0 --file-logging
```

Or use environment variables:

```bash
export WIKI_LINK_TRACING_ENABLED=true
export WIKI_LINK_TRACING_THRESHOLD_MS=0
export WIKI_LINK_FILE_LOGGING=true
export WIKI_LINK_LOG_FILE=/path/to/log/file.log
```

### Analyzing Results

Once you have collected log data, you can analyze it using the provided script:

```bash
# Analyze logs from a file
python wiki_link/scripts/analyze_event_factories.py /path/to/log/file.log

# Or pipe logs directly
cat /path/to/log/file.log | python wiki_link/scripts/analyze_event_factories.py
```

## Output Format

The analysis tool produces a detailed report with sections for:

1. **Entity Processing Statistics** - Overall metrics about entity processing
2. **Statistics by Entity Type** - Breakdown of metrics by entity type (PERSON, BOOK, etc.)
3. **Event Factory Statistics** - Performance metrics for each event factory
4. **Event Type Frequency** - Distribution of event types in the processed data

Example output:

```
WikiLink Event Factory Analysis Report
====================================

Entity Processing Statistics
--------------------------
Total entities processed: 100
Total events created: 325
Average events per entity: 3.25
Average entity processing time: 234.56ms
Median entity processing time: 201.33ms
Min entity processing time: 125.45ms
Max entity processing time: 789.12ms

Statistics by Entity Type
------------------------

PERSON:
  Count: 80
  Events: 290
  Events per entity: 3.63
  Average processing time: 245.67ms
  Median processing time: 215.50ms
  Min processing time: 135.45ms
  Max processing time: 789.12ms

BOOK:
  Count: 20
  Events: 35
  Events per entity: 1.75
  Average processing time: 184.23ms
  Median processing time: 172.15ms
  Min processing time: 125.45ms
  Max processing time: 356.78ms

Event Factory Statistics
----------------------
Factory                         Count    Events   Avg Time   Events/Call  
---------------------------------------------------------------------------
Person died                     75       75       45.67ms    1.00
Person was born                 72       72       48.23ms    1.00
Person took position            68       68       67.12ms    1.00
Book was published              20       20       35.45ms    1.00
Person received award           18       18       52.33ms    1.00

Event Type Frequency
------------------
Person died: 75 events (23.1%)
Person was born: 72 events (22.2%)
Person took position: 68 events (20.9%)
Book was published: 20 events (6.2%)
Person received award: 18 events (5.5%)
```

## Implementation Details

The tracing system is implemented using several components:

1. **EventFactory Base Class** - Enhanced with timing metrics
2. **Logging in WikiService** - Captures metrics about entity processing
3. **Analysis Scripts** - Process logs to extract meaningful metrics

Each EventFactory implementation needs to use the new `_create_events()` method instead
of directly implementing `create_wiki_event()`. The base class handles the timing and
statistics collection. 