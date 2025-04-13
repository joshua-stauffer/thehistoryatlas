import time
import logging
import functools
import os
from typing import Callable, TypeVar, Any, cast

# Configure logging
logger = logging.getLogger("wiki_link.tracing")

# Type variable for function return type
T = TypeVar("T")

# Check if tracing is enabled from environment variable
TRACING_ENABLED = os.environ.get("WIKI_LINK_TRACING_ENABLED", "false").lower() == "true"
# Threshold in milliseconds above which to log (to reduce noise)
TRACING_THRESHOLD_MS = float(os.environ.get("WIKI_LINK_TRACING_THRESHOLD_MS", "0"))


def trace_time(label: str = None):
    """
    Decorator that traces the execution time of a function.

    Args:
        label: Optional prefix for the log message. If not provided, uses the function name.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Skip tracing if disabled
            if not TRACING_ENABLED:
                return func(*args, **kwargs)

            # Get the class name if this is a method call
            class_name = args[0].__class__.__name__ if args else ""
            func_name = func.__name__
            trace_label = label or f"{class_name}.{func_name}"

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                # Only log if duration exceeds threshold
                if duration_ms >= TRACING_THRESHOLD_MS:
                    logger.info(f"TRACE: {trace_label} took {duration_ms:.2f}ms")

        return cast(Callable[..., T], wrapper)

    return decorator


def configure_tracing(enabled: bool = None, threshold_ms: float = None):
    """
    Configure tracing parameters at runtime.

    Args:
        enabled: Whether tracing is enabled
        threshold_ms: Minimum duration in milliseconds to log
    """
    global TRACING_ENABLED, TRACING_THRESHOLD_MS

    if enabled is not None:
        TRACING_ENABLED = enabled

    if threshold_ms is not None:
        TRACING_THRESHOLD_MS = threshold_ms

    logger.info(
        f"Tracing {'enabled' if TRACING_ENABLED else 'disabled'} with threshold {TRACING_THRESHOLD_MS}ms"
    )
