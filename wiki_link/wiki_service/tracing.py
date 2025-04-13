import time
import logging
import functools
import os
from typing import Callable, TypeVar, Any, cast
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Configure logging
logger = logging.getLogger("wiki_link.tracing")

# Type variable for function return type
T = TypeVar("T")

# Check if tracing is enabled from environment variable
TRACING_ENABLED = os.environ.get("WIKI_LINK_TRACING_ENABLED", "false").lower() == "true"
# Threshold in milliseconds above which to log (to reduce noise)
TRACING_THRESHOLD_MS = float(os.environ.get("WIKI_LINK_TRACING_THRESHOLD_MS", "0"))
# Check if file logging is enabled
FILE_LOGGING_ENABLED = (
    os.environ.get("WIKI_LINK_FILE_LOGGING", "false").lower() == "true"
)
# Get log file path from environment or use default
LOG_FILE_PATH = os.environ.get("WIKI_LINK_LOG_FILE", "/tmp/wiki_link_tracing.log")
# Maximum log file size (10MB default)
LOG_FILE_MAX_SIZE = int(os.environ.get("WIKI_LINK_LOG_MAX_SIZE", 10 * 1024 * 1024))
# Number of backup files to keep
LOG_FILE_BACKUP_COUNT = int(os.environ.get("WIKI_LINK_LOG_BACKUP_COUNT", 3))


def ensure_dir_exists(file_path):
    """Ensure the directory for the given file path exists."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")
            return False
    return True


# Configure file logging if enabled
if FILE_LOGGING_ENABLED:
    # Ensure log directory exists
    if ensure_dir_exists(LOG_FILE_PATH):
        try:
            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

            # Create file handler
            file_handler = RotatingFileHandler(
                LOG_FILE_PATH,
                maxBytes=LOG_FILE_MAX_SIZE,
                backupCount=LOG_FILE_BACKUP_COUNT,
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)

            # Add file handler to logger
            logger.addHandler(file_handler)
            logger.setLevel(logging.INFO)

            logger.info(f"Trace logging to file enabled at {LOG_FILE_PATH}")
        except Exception as e:
            print(f"Failed to set up file logging: {e}")
            # Fallback to console only
            FILE_LOGGING_ENABLED = False
    else:
        # Fallback to console only
        FILE_LOGGING_ENABLED = False
        print(
            f"Could not create log directory for {LOG_FILE_PATH}, file logging disabled"
        )


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


def configure_tracing(
    enabled: bool = None,
    threshold_ms: float = None,
    file_logging: bool = None,
    log_file: str = None,
):
    """
    Configure tracing parameters at runtime.

    Args:
        enabled: Whether tracing is enabled
        threshold_ms: Minimum duration in milliseconds to log
        file_logging: Whether to log to a file
        log_file: Path to the log file
    """
    global TRACING_ENABLED, TRACING_THRESHOLD_MS, FILE_LOGGING_ENABLED, LOG_FILE_PATH

    changed = False

    if enabled is not None and enabled != TRACING_ENABLED:
        TRACING_ENABLED = enabled
        changed = True

    if threshold_ms is not None and threshold_ms != TRACING_THRESHOLD_MS:
        TRACING_THRESHOLD_MS = threshold_ms
        changed = True

    if file_logging is not None and file_logging != FILE_LOGGING_ENABLED:
        FILE_LOGGING_ENABLED = file_logging
        changed = True

        if FILE_LOGGING_ENABLED:
            # Ensure log directory exists
            file_path = log_file or LOG_FILE_PATH
            if ensure_dir_exists(file_path):
                try:
                    # Set up file logging if newly enabled
                    formatter = logging.Formatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )
                    file_handler = RotatingFileHandler(
                        file_path,
                        maxBytes=LOG_FILE_MAX_SIZE,
                        backupCount=LOG_FILE_BACKUP_COUNT,
                    )
                    file_handler.setFormatter(formatter)
                    file_handler.setLevel(logging.INFO)

                    # Remove existing file handlers
                    for handler in logger.handlers[:]:
                        if isinstance(handler, RotatingFileHandler):
                            logger.removeHandler(handler)

                    logger.addHandler(file_handler)
                    logger.setLevel(logging.INFO)
                except Exception as e:
                    print(f"Failed to set up file logging: {e}")
                    FILE_LOGGING_ENABLED = False
            else:
                print(
                    f"Could not create log directory for {file_path}, file logging disabled"
                )
                FILE_LOGGING_ENABLED = False
        else:
            # Remove file handlers if disabled
            for handler in logger.handlers[:]:
                if isinstance(handler, RotatingFileHandler):
                    logger.removeHandler(handler)

    if log_file is not None and log_file != LOG_FILE_PATH and FILE_LOGGING_ENABLED:
        if ensure_dir_exists(log_file):
            LOG_FILE_PATH = log_file
            changed = True

            try:
                # Update the file handler with the new path
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                file_handler = RotatingFileHandler(
                    LOG_FILE_PATH,
                    maxBytes=LOG_FILE_MAX_SIZE,
                    backupCount=LOG_FILE_BACKUP_COUNT,
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(logging.INFO)

                # Remove existing file handlers
                for handler in logger.handlers[:]:
                    if isinstance(handler, RotatingFileHandler):
                        logger.removeHandler(handler)

                logger.addHandler(file_handler)
            except Exception as e:
                print(f"Failed to update log file: {e}")
                FILE_LOGGING_ENABLED = False
        else:
            print(
                f"Could not create log directory for {log_file}, file logging disabled"
            )
            FILE_LOGGING_ENABLED = False

    if changed:
        status_msg = f"Tracing {'enabled' if TRACING_ENABLED else 'disabled'} with threshold {TRACING_THRESHOLD_MS}ms"
        if FILE_LOGGING_ENABLED:
            status_msg += f", logging to file {LOG_FILE_PATH}"
        logger.info(status_msg)
