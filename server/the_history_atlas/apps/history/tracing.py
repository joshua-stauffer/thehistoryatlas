import functools
import logging
import time
from pathlib import Path

# Set up logging
LOGS_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

trace_logger = logging.getLogger("history_trace")
trace_logger.setLevel(logging.DEBUG)

# File handler for trace logs
trace_handler = logging.FileHandler(LOGS_DIR / "history_trace.log")
trace_handler.setLevel(logging.DEBUG)
trace_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
trace_handler.setFormatter(trace_formatter)
trace_logger.addHandler(trace_handler)


def trace_method(method_name=None):
    """Decorator to trace method execution time and log it."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            # Use either provided method name or function name
            name = method_name or func.__name__

            trace_logger.debug(f"{name}:duration_seconds:{execution_time:.6f}")
            return result

        return wrapper

    return decorator


def trace_block(block_name):
    """Context manager to trace block execution time."""

    class TraceBlock:
        def __init__(self, name):
            self.name = name

        def __enter__(self):
            self.start_time = time.perf_counter()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            end_time = time.perf_counter()
            execution_time = end_time - self.start_time
            trace_logger.debug(f"{self.name}:duration_seconds:{execution_time:.6f}")

    return TraceBlock(block_name)
