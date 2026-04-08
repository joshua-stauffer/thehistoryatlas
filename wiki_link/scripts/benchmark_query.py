#!/usr/bin/env python3

import os
import time
import statistics
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from wiki_service.schema import WikiQueue


def benchmark_query(iterations=100):
    """Benchmark the performance of the get_oldest_item_from_queue query."""
    db_uri = os.environ.get("TEST_DB_URI")
    if not db_uri:
        print("TEST_DB_URI environment variable not set")
        return 1

    engine = create_engine(db_uri)

    # Store execution times
    times = []

    for i in range(iterations):
        start_time = time.time()

        with Session(engine) as session:
            row = (
                session.query(WikiQueue)
                .order_by(WikiQueue.time_added)
                .limit(1)
                .one_or_none()
            )

        end_time = time.time()
        query_time = (end_time - start_time) * 1000  # convert to ms
        times.append(query_time)
        print(f"Query {i+1}/{iterations}: {query_time:.2f} ms")

    # Calculate statistics
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    min_time = min(times)
    max_time = max(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0

    print("\nPerformance Statistics:")
    print(f"Average: {avg_time:.2f} ms")
    print(f"Median: {median_time:.2f} ms")
    print(f"Min: {min_time:.2f} ms")
    print(f"Max: {max_time:.2f} ms")
    print(f"StdDev: {std_dev:.2f} ms")

    return 0


if __name__ == "__main__":
    exit(benchmark_query(10))  # run 10 iterations for a quick test
