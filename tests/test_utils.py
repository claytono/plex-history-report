"""Tests for the utils module."""

import logging
import unittest
from unittest.mock import patch

import plex_history_report.utils
from plex_history_report.utils import (
    PerformanceLogHandler,
    set_benchmarking,
    timing_decorator,
)


class TestUtils(unittest.TestCase):
    """Test the utils module."""

    def setUp(self):
        """Set up the test environment."""
        # Store original benchmarking value to restore later
        self.original_benchmarking = plex_history_report.utils.benchmarking_enabled

    def tearDown(self):
        """Reset benchmarking after each test."""
        # Restore the original benchmarking value
        plex_history_report.utils.benchmarking_enabled = self.original_benchmarking

    def test_set_benchmarking(self):
        """Test the set_benchmarking function."""
        # Set a known initial state
        plex_history_report.utils.benchmarking_enabled = False
        self.assertFalse(plex_history_report.utils.benchmarking_enabled)

        # Test setting to True
        set_benchmarking(True)
        self.assertTrue(plex_history_report.utils.benchmarking_enabled)

        # Test setting to False
        set_benchmarking(False)
        self.assertFalse(plex_history_report.utils.benchmarking_enabled)

    @patch("plex_history_report.utils.time.time")
    @patch("plex_history_report.utils.logger")
    def test_timing_decorator_enabled(self, mock_logger, mock_time):
        """Test the timing_decorator when benchmarking is enabled."""
        # Mock time.time() to return predictable values
        mock_time.side_effect = [1.0, 2.5]  # Start time, end time (1.5s elapsed)

        # Define test function
        @timing_decorator
        def test_function():
            return "result"

        # Enable benchmarking
        set_benchmarking(True)

        # Call the decorated function
        result = test_function()

        # Verify the function returned the correct result
        self.assertEqual(result, "result")

        # Verify that the logger was called with the correct message
        mock_logger.info.assert_called_once_with("PERFORMANCE: test_function took 1.50 seconds")

    @patch("plex_history_report.utils.time.time")
    @patch("plex_history_report.utils.logger")
    def test_timing_decorator_disabled(self, mock_logger, mock_time):
        """Test the timing_decorator when benchmarking is disabled."""

        # Define test function
        @timing_decorator
        def test_function():
            return "result"

        # Ensure benchmarking is disabled
        set_benchmarking(False)

        # Call the decorated function
        result = test_function()

        # Verify the function returned the correct result
        self.assertEqual(result, "result")

        # Verify that the logger was not called
        mock_logger.info.assert_not_called()
        mock_time.assert_not_called()

    @patch("plex_history_report.utils.time.time")
    @patch("plex_history_report.utils.logger")
    def test_timing_decorator_on_method(self, mock_logger, mock_time):
        """Test the timing_decorator on a class method."""
        # Mock time.time() to return predictable values
        mock_time.side_effect = [3.0, 4.2]  # Start time, end time (1.2s elapsed)

        # Define test class with decorated method
        class TestClass:
            @timing_decorator
            def test_method(self):
                return "method result"

        # Enable benchmarking
        set_benchmarking(True)

        # Create instance and call method
        instance = TestClass()
        result = instance.test_method()

        # Verify the method returned the correct result
        self.assertEqual(result, "method result")

        # Verify that the logger was called with the correct message
        mock_logger.info.assert_called_once_with(
            "PERFORMANCE: TestClass.test_method took 1.20 seconds"
        )

    def test_performance_log_handler_init(self):
        """Test PerformanceLogHandler initialization."""
        # Test with default parameter
        handler = PerformanceLogHandler()
        self.assertEqual(handler.performance_data, {})

        # Test with provided performance_data
        existing_data = {"function_name": [1.5, 2.0]}
        handler = PerformanceLogHandler(existing_data)
        self.assertEqual(handler.performance_data, existing_data)

    def test_performance_log_handler_emit_valid(self):
        """Test PerformanceLogHandler.emit with valid performance logs."""
        handler = PerformanceLogHandler()

        # Create log records with performance data
        record1 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="PERFORMANCE: test_func took 1.50 seconds",
            args=(),
            exc_info=None,
        )

        record2 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="PERFORMANCE: test_func took 2.30 seconds",
            args=(),
            exc_info=None,
        )

        record3 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="PERFORMANCE: other_func took 0.75 seconds",
            args=(),
            exc_info=None,
        )

        # Process the records
        handler.emit(record1)
        handler.emit(record2)
        handler.emit(record3)

        # Check that the performance data was recorded correctly
        expected_data = {"test_func": [1.5, 2.3], "other_func": [0.75]}
        self.assertEqual(handler.performance_data, expected_data)

    def test_performance_log_handler_emit_invalid(self):
        """Test PerformanceLogHandler.emit with invalid logs."""
        handler = PerformanceLogHandler()

        # Create log records with invalid formats
        record1 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Regular log message",  # Not a performance log
            args=(),
            exc_info=None,
        )

        record2 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="PERFORMANCE: test_func invalid format",  # Missing "took" keyword
            args=(),
            exc_info=None,
        )

        record3 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="PERFORMANCE: test_func took invalid_time seconds",  # Invalid time format
            args=(),
            exc_info=None,
        )

        # Process the records
        handler.emit(record1)
        handler.emit(record2)
        handler.emit(record3)

        # Check that no performance data was recorded for invalid logs
        self.assertEqual(handler.performance_data, {})

    def test_get_performance_data(self):
        """Test PerformanceLogHandler.get_performance_data method."""
        # Initialize with some data
        initial_data = {"function1": [1.0, 2.0]}
        handler = PerformanceLogHandler(initial_data)

        # Add more data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="PERFORMANCE: function2 took 3.25 seconds",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

        # Verify that get_performance_data returns the correct data
        expected_data = {"function1": [1.0, 2.0], "function2": [3.25]}
        self.assertEqual(handler.get_performance_data(), expected_data)


if __name__ == "__main__":
    unittest.main()
