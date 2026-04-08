#!/usr/bin/env python
"""
Script to analyze event factory logs from WikiLink service.

This script reads trace logs and extracts metrics about event factory processing,
providing statistics about entity processing times, event creation rates, and more.

Usage:
    python analyze_event_factories.py [logfile]
    cat logfile | python analyze_event_factories.py

If no logfile is provided, input is read from stdin.
"""

import sys
import re
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple

# Match entity processing log lines
# Format: Entity processed: Q12345 (Person Name), Type: PERSON, Time: 123.45ms, Events created: 3
ENTITY_PATTERN = re.compile(
    r"Entity processed: (\w+) \((.+?)\), Type: (\w+), Time: ([\d.]+)ms, Events created: (\d+)"
)

# Match factory metrics log lines
# Format: Factory: Person died, Count: 1, Events: 1, Avg time: 123.45ms
FACTORY_PATTERN = re.compile(
    r"Factory: (.+?), Count: (\d+), Events: (\d+), Avg time: ([\d.]+)ms"
)

# Also collect trace time data for event factories
TRACE_PATTERN = re.compile(r"TRACE: (.+EventFactory.+) took ([\d.]+)ms")


def analyze_logs(lines):
    # Data structures to store metrics
    entities_processed = (
        []
    )  # (entity_id, entity_name, entity_type, time_ms, events_count)
    factory_metrics = defaultdict(
        list
    )  # factory_name -> [(count, events, avg_time), ...]
    factory_trace_times = defaultdict(list)  # factory_name -> [time_ms, ...]

    # Process each line
    for line in lines:
        # Check for entity processing logs
        entity_match = ENTITY_PATTERN.search(line)
        if entity_match:
            entity_id, entity_name, entity_type, time_ms, events_count = (
                entity_match.groups()
            )
            entities_processed.append(
                (entity_id, entity_name, entity_type, float(time_ms), int(events_count))
            )
            continue

        # Check for factory metrics logs
        factory_match = FACTORY_PATTERN.search(line)
        if factory_match:
            factory_name, count, events, avg_time = factory_match.groups()
            factory_metrics[factory_name].append(
                (int(count), int(events), float(avg_time))
            )
            continue

        # Check for trace time logs
        trace_match = TRACE_PATTERN.search(line)
        if trace_match:
            func_name, duration_str = trace_match.groups()
            # Filter for event factory traces
            if "EventFactory" in func_name:
                # Extract factory name from the function name
                parts = func_name.split(".")
                if len(parts) >= 2:
                    factory_name = parts[0]  # Class name is typically the first part
                    factory_trace_times[factory_name].append(float(duration_str))

    return entities_processed, factory_metrics, factory_trace_times


def calculate_entity_stats(entities_processed):
    if not entities_processed:
        return {}

    # Count total entities and events
    total_entities = len(entities_processed)
    total_events = sum(e[4] for e in entities_processed)

    # Times for all entities
    entity_times = [e[3] for e in entities_processed]

    # Calculate entity processing time statistics
    avg_entity_time = statistics.mean(entity_times) if entity_times else 0
    median_entity_time = statistics.median(entity_times) if entity_times else 0
    min_entity_time = min(entity_times) if entity_times else 0
    max_entity_time = max(entity_times) if entity_times else 0
    stdev_entity_time = statistics.stdev(entity_times) if len(entity_times) > 1 else 0

    # Group by entity type
    entity_types = defaultdict(list)
    for entity in entities_processed:
        entity_types[entity[2]].append(entity)

    # Calculate stats by entity type
    type_stats = {}
    for entity_type, entities in entity_types.items():
        type_count = len(entities)
        type_events = sum(e[4] for e in entities)
        type_times = [e[3] for e in entities]

        type_stats[entity_type] = {
            "count": type_count,
            "events": type_events,
            "avg_time": statistics.mean(type_times) if type_times else 0,
            "median_time": statistics.median(type_times) if type_times else 0,
            "min_time": min(type_times) if type_times else 0,
            "max_time": max(type_times) if type_times else 0,
        }

    return {
        "total_entities": total_entities,
        "total_events": total_events,
        "avg_entity_time": avg_entity_time,
        "median_entity_time": median_entity_time,
        "min_entity_time": min_entity_time,
        "max_entity_time": max_entity_time,
        "stdev_entity_time": stdev_entity_time,
        "events_per_entity": total_events / total_entities if total_entities else 0,
        "entity_types": type_stats,
    }


def calculate_factory_stats(factory_metrics, factory_trace_times):
    factory_stats = {}

    # Process metrics from log entries
    for factory_name, metrics in factory_metrics.items():
        total_count = sum(m[0] for m in metrics)
        total_events = sum(m[1] for m in metrics)
        # Calculate weighted average of average times
        weighted_avg_time = (
            sum(m[0] * m[2] for m in metrics) / total_count if total_count else 0
        )

        factory_stats[factory_name] = {
            "count": total_count,
            "events": total_events,
            "avg_time": weighted_avg_time,
            "events_per_call": total_events / total_count if total_count else 0,
        }

    # Enrich with trace time data
    for factory_name, times in factory_trace_times.items():
        if factory_name in factory_stats:
            factory_stats[factory_name]["trace_count"] = len(times)
            factory_stats[factory_name]["trace_avg_time"] = (
                statistics.mean(times) if times else 0
            )
            factory_stats[factory_name]["trace_median_time"] = (
                statistics.median(times) if times else 0
            )
            factory_stats[factory_name]["trace_min_time"] = min(times) if times else 0
            factory_stats[factory_name]["trace_max_time"] = max(times) if times else 0

    return factory_stats


def print_report(entity_stats, factory_stats):
    print("\nWikiLink Event Factory Analysis Report")
    print("====================================\n")

    # Entity processing stats
    print("Entity Processing Statistics")
    print("--------------------------")
    print(f"Total entities processed: {entity_stats.get('total_entities', 0)}")
    print(f"Total events created: {entity_stats.get('total_events', 0)}")
    print(f"Average events per entity: {entity_stats.get('events_per_entity', 0):.2f}")
    print(
        f"Average entity processing time: {entity_stats.get('avg_entity_time', 0):.2f}ms"
    )
    print(
        f"Median entity processing time: {entity_stats.get('median_entity_time', 0):.2f}ms"
    )
    print(f"Min entity processing time: {entity_stats.get('min_entity_time', 0):.2f}ms")
    print(f"Max entity processing time: {entity_stats.get('max_entity_time', 0):.2f}ms")

    # Stats by entity type
    print("\nStatistics by Entity Type")
    print("------------------------")
    for entity_type, stats in entity_stats.get("entity_types", {}).items():
        print(f"\n{entity_type}:")
        print(f"  Count: {stats['count']}")
        print(f"  Events: {stats['events']}")
        print(
            f"  Events per entity: {stats['events'] / stats['count'] if stats['count'] else 0:.2f}"
        )
        print(f"  Average processing time: {stats['avg_time']:.2f}ms")
        print(f"  Median processing time: {stats['median_time']:.2f}ms")
        print(f"  Min processing time: {stats['min_time']:.2f}ms")
        print(f"  Max processing time: {stats['max_time']:.2f}ms")

    # Factory stats
    print("\nEvent Factory Statistics")
    print("----------------------")
    print(
        f"{'Factory':<30} {'Count':<8} {'Events':<8} {'Avg Time':<10} {'Events/Call':<12}"
    )
    print("-" * 75)

    # Sort factories by total events created (descending)
    sorted_factories = sorted(
        factory_stats.items(), key=lambda x: x[1].get("events", 0), reverse=True
    )

    for factory_name, stats in sorted_factories:
        print(
            f"{factory_name:<30} "
            f"{stats.get('count', 0):<8} "
            f"{stats.get('events', 0):<8} "
            f"{stats.get('avg_time', 0):.2f}ms   "
            f"{stats.get('events_per_call', 0):.2f}"
        )

    # Event type frequency
    print("\nEvent Type Frequency")
    print("------------------")
    total_events = sum(stats.get("events", 0) for stats in factory_stats.values())

    for factory_name, stats in sorted_factories:
        factory_events = stats.get("events", 0)
        if factory_events > 0:
            percentage = (factory_events / total_events) * 100 if total_events else 0
            print(f"{factory_name}: {factory_events} events ({percentage:.1f}%)")


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()

    entities_processed, factory_metrics, factory_trace_times = analyze_logs(lines)
    entity_stats = calculate_entity_stats(entities_processed)
    factory_stats = calculate_factory_stats(factory_metrics, factory_trace_times)

    print_report(entity_stats, factory_stats)


if __name__ == "__main__":
    main()
