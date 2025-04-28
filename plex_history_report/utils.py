"""Utility functions and tools for Plex History Report."""

import functools
import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


def timing_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to measure function execution time.

    Args:
        func: The function to be timed.

    Returns:
        Wrapped function that logs timing information.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        # Get the class name if method belongs to a class
        if args and hasattr(args[0], "__class__"):
            class_name = args[0].__class__.__name__
            name = f"{class_name}.{func.__name__}"
        else:
            name = func.__name__
        logger.info(f"PERFORMANCE: {name} took {elapsed_time:.2f} seconds")
        return result

    return wrapper


class PerformanceLogHandler(logging.Handler):
    """Custom logging handler to capture performance metrics.

    This handler captures log messages that start with "PERFORMANCE:"
    and extracts timing information from them.
    """

    def __init__(self, performance_data: Optional[Dict[str, List[float]]] = None):
        """Initialize the handler with an optional performance data dictionary.

        Args:
            performance_data: Optional dictionary to store performance data.
                If not provided, a new dictionary will be created.
        """
        super().__init__()
        self.performance_data = performance_data if performance_data is not None else {}

    def emit(self, record):
        """Process a log record if it contains performance information.

        Args:
            record: The log record to process.
        """
        if hasattr(record, "msg") and record.msg.startswith("PERFORMANCE:"):
            # Extract the function name and timing from the log message
            parts = record.msg.split("took")
            if len(parts) == 2:
                func_name = parts[0].replace("PERFORMANCE:", "").strip()
                time_str = parts[1].strip()
                try:
                    time_seconds = float(time_str.split()[0])
                    # Use list unpacking instead of concatenation
                    self.performance_data[func_name] = [
                        *self.performance_data.get(func_name, []),
                        time_seconds,
                    ]
                except (ValueError, IndexError):
                    pass

    def get_performance_data(self) -> Dict[str, List[float]]:
        """Get the collected performance data.

        Returns:
            Dictionary mapping function names to lists of execution times.
        """
        return self.performance_data
