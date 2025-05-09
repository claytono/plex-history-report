"""Tests for the formatters module."""

import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import yaml
from rich.console import Console

from plex_history_report.formatters import (
    BaseFormatter,
    CompactFormatter,
    CsvFormatter,
    FormatterFactory,
    JsonFormatter,
    MarkdownFormatter,
    RichFormatter,
    YamlFormatter,
)


class TestRounding(unittest.TestCase):
    """Test that formatters correctly round numerical values."""

    def test_rich_formatter_rounding(self):
        """Test that RichFormatter correctly rounds percentages."""
        # Create a sample show with an uneven percentage
        sample_show = {
            "title": "Test Show",
            "total_episodes": 100,
            "watched_episodes": 65,
            "completion_percentage": 65.91466666666668,
            "total_watch_time_minutes": 123.4567,
            "last_watched": datetime(2023, 4, 1, 12, 0, 0),
            "year": 2020,
            "rating": 9.1,
        }

        # Test with Rich formatter
        formatter = RichFormatter()
        result = formatter.format_show_statistics([sample_show])

        # Check that the result contains the rounded percentage
        self.assertIn("65.9%", result)
        # We shouldn't see the full unrounded number
        self.assertNotIn("65.91466666666668", result)

    def test_markdown_formatter_rounding(self):
        """Test that MarkdownFormatter correctly rounds percentages."""
        # Create a sample show with an uneven percentage
        sample_show = {
            "title": "Test Show",
            "total_episodes": 100,
            "watched_episodes": 65,
            "completion_percentage": 65.91466666666668,
            "total_watch_time_minutes": 123.4567,
            "last_watched": datetime(2023, 4, 1, 12, 0, 0),
            "year": 2020,
            "rating": 9.1,
        }

        # Test with Markdown formatter
        formatter = MarkdownFormatter()
        result = formatter.format_show_statistics([sample_show])

        # Check that the percentage is rounded to 1 decimal place
        self.assertIn("65.9%", result)
        # We shouldn't see the full unrounded number
        self.assertNotIn("65.91466666666668", result)

    def test_json_formatter_output(self):
        """Test that JsonFormatter produces valid output with numbers."""
        # Create a sample show with an uneven percentage
        sample_show = {
            "title": "Test Show",
            "total_episodes": 100,
            "watched_episodes": 65,
            "completion_percentage": 65.91466666666668,
            "total_watch_time_minutes": 123.4567,
            "last_watched": datetime(2023, 4, 1, 12, 0, 0),
            "year": 2020,
            "rating": 9.1,
        }

        # Test with JSON formatter
        formatter = JsonFormatter()
        result = formatter.format_show_statistics([sample_show])

        # The result should be valid JSON
        data = json.loads(result)
        # We expect the original value to be preserved in JSON output
        self.assertEqual(data["shows"][0]["completion_percentage"], 65.9)

    def test_csv_formatter_rounding(self):
        """Test that CsvFormatter correctly rounds percentages."""
        # Create a sample show with an uneven percentage
        sample_show = {
            "title": "Test Show",
            "total_episodes": 100,
            "watched_episodes": 65,
            "completion_percentage": 65.91466666666668,
            "total_watch_time_minutes": 123.4567,
            "last_watched": datetime(2023, 4, 1, 12, 0, 0),
            "year": 2020,
            "rating": 9.1,
        }

        # Test with CSV formatter
        formatter = CsvFormatter()
        result = formatter.format_show_statistics([sample_show])

        # Check that the CSV contains the rounded percentage
        self.assertIn("65.9", result)
        # We shouldn't see the full unrounded number
        self.assertNotIn("65.91466666666668", result)

    def test_yaml_formatter_output(self):
        """Test that YamlFormatter produces valid output with numbers."""
        # Create a sample show with an uneven percentage
        sample_show = {
            "title": "Test Show",
            "total_episodes": 100,
            "watched_episodes": 65,
            "completion_percentage": 65.91466666666668,
            "total_watch_time_minutes": 123.4567,
            "last_watched": datetime(2023, 4, 1, 12, 0, 0),
            "year": 2020,
            "rating": 9.1,
        }

        # Test with YAML formatter
        formatter = YamlFormatter()
        result = formatter.format_show_statistics([sample_show])

        # The result should be valid YAML
        data = yaml.safe_load(result)
        # We expect the original value to be preserved in YAML output
        self.assertEqual(data["shows"][0]["completion_percentage"], 65.9)


class TestComplexData(unittest.TestCase):
    """Test that formatters can handle complex nested data structures."""

    def setUp(self):
        """Set up complex test data for all tests."""
        # Create a complex nested data structure with shows that have recent episodes
        self.complex_show_data = [
            {
                "title": "Complex Show",
                "year": 2022,
                "rating": 8.7,
                "total_episodes": 20,
                "watched_episodes": 15,
                "completion_percentage": 75.0,
                "total_watch_time_minutes": 450,
                "last_watched": datetime(2023, 4, 1, 12, 0, 0),
                "recent_episodes": [
                    {
                        "title": "Episode 1",
                        "season": 1,
                        "episode": 1,
                        "watch_date": datetime(2023, 3, 15, 12, 0, 0),
                        "duration_minutes": 30,
                    },
                    {
                        "title": "Episode 2",
                        "season": 1,
                        "episode": 2,
                        "watch_date": datetime(2023, 3, 16, 12, 0, 0),
                        "duration_minutes": 30,
                    },
                ],
            },
            {
                "title": "Another Show",
                "year": 2021,
                "rating": 9.2,
                "total_episodes": 10,
                "watched_episodes": 10,
                "completion_percentage": 100.0,
                "total_watch_time_minutes": 300,
                "last_watched": datetime(2023, 3, 30, 12, 0, 0),
                "recent_episodes": [],  # No recent episodes
            },
        ]

    def test_json_complex_data(self):
        """Test that JsonFormatter correctly handles complex nested data."""
        formatter = JsonFormatter()
        result = formatter.format_show_statistics(self.complex_show_data)

        # Result should be valid JSON
        data = json.loads(result)

        # Check structure is preserved
        self.assertEqual(len(data["shows"]), 2)
        self.assertEqual(data["shows"][0]["title"], "Complex Show")
        self.assertEqual(len(data["shows"][0]["recent_episodes"]), 2)
        self.assertEqual(data["shows"][0]["recent_episodes"][0]["title"], "Episode 1")

    def test_yaml_complex_data(self):
        """Test that YamlFormatter correctly handles complex nested data."""
        formatter = YamlFormatter()
        result = formatter.format_show_statistics(self.complex_show_data)

        # Result should be valid YAML
        data = yaml.safe_load(result)

        # Check structure is preserved
        self.assertEqual(len(data["shows"]), 2)
        self.assertEqual(data["shows"][0]["title"], "Complex Show")
        self.assertEqual(len(data["shows"][0]["recent_episodes"]), 2)
        self.assertEqual(data["shows"][0]["recent_episodes"][0]["title"], "Episode 1")

    def test_markdown_complex_data(self):
        """Test that MarkdownFormatter correctly handles complex nested data."""
        formatter = MarkdownFormatter()
        result = formatter.format_show_statistics(self.complex_show_data)

        # Check that all important elements are included in the markdown
        self.assertIn("Complex Show", result)
        self.assertIn("75.0%", result)
        # Episodes aren't actually included in the standard show statistics markdown output
        # They would only appear in the recently watched output
        self.assertIn("Another Show", result)
        self.assertIn("100.0%", result)

    def test_csv_complex_data(self):
        """Test that CsvFormatter correctly handles complex nested data."""
        formatter = CsvFormatter()
        result = formatter.format_show_statistics(self.complex_show_data)

        # CSV should contain the show titles
        self.assertIn("Complex Show", result)
        self.assertIn("Another Show", result)

        # CSV typically flattens data, so recent episodes might not be included
        # or might be represented in a simplified way

    def test_rich_complex_data(self):
        """Test that RichFormatter correctly handles complex nested data."""
        formatter = RichFormatter()
        result = formatter.format_show_statistics(self.complex_show_data)

        # Check that all important elements are included in the output
        self.assertIn("Complex Show", result)
        self.assertIn("75.0%", result)
        self.assertIn("Another Show", result)
        self.assertIn("100.0%", result)


class TestMarkdownLinting(unittest.TestCase):
    """Test that markdown output follows proper markdown format conventions."""

    def setUp(self):
        """Set up test data with edge cases for markdown formatting."""
        self.show_with_special_chars = {
            "title": "Test Show | with | pipes",  # Title with pipe chars that need escaping
            "total_episodes": 10,
            "watched_episodes": 5,
            "completion_percentage": 50.0,
            "total_watch_time_minutes": 150,
            "last_watched": datetime(2023, 4, 1, 12, 0, 0),
            "year": 2020,
            "rating": 8.5,
        }

    def test_markdown_table_format(self):
        """Test that markdown tables are properly formatted."""
        formatter = MarkdownFormatter()
        result = formatter.format_show_statistics([self.show_with_special_chars])

        # Check for proper markdown heading format
        self.assertIn("# TV Show Statistics", result)

        # Check that table headers exist and are properly formatted
        self.assertIn("| Title | Watched | Total | Completion | Watch Time |", result)
        self.assertIn("|-------|---------|-------|------------|------------|", result)

        # Check that special characters in titles are properly escaped
        self.assertIn("| Test Show \\| with \\| pipes |", result)

        # Check that the summary section is properly formatted
        self.assertIn("## Summary", result)
        self.assertIn("- **Total Shows:** 1", result)

    def test_markdown_recently_watched_format(self):
        """Test that recently watched markdown is properly formatted."""
        formatter = MarkdownFormatter()
        result = formatter.format_recently_watched(
            [self.show_with_special_chars], media_type="show"
        )

        # Check for proper markdown heading format
        self.assertIn("# Recently Watched Shows", result)

        # Check that table headers exist and are properly formatted
        self.assertIn("| Title | Last Watched | Progress | Watch Time |", result)
        self.assertIn("|-------|--------------|----------|------------|", result)

        # Check that special characters in titles are properly escaped
        self.assertIn("| Test Show \\| with \\| pipes |", result)

    def test_markdown_movie_statistics_format(self):
        """Test that movie statistics markdown is properly formatted."""
        movie_with_special_chars = {
            "title": "Movie | with | pipes",
            "year": 2021,
            "watch_count": 2,
            "last_watched": datetime(2023, 5, 15, 20, 30, 0),
            "duration_minutes": 120,
            "watched": True,
            "rating": 9.0,
        }

        formatter = MarkdownFormatter()
        result = formatter.format_movie_statistics([movie_with_special_chars])

        # Check for proper markdown heading format
        self.assertIn("# Movie Statistics", result)

        # Check that table headers exist and are properly formatted
        self.assertIn("| Title | Watch Count | Last Watched | Duration | Rating |", result)
        self.assertIn("|-------|-------------|--------------|----------|--------|", result)

        # Check that special characters in titles are properly escaped
        self.assertIn("| Movie \\| with \\| pipes |", result)

        # Check that the summary section is properly formatted
        self.assertIn("## Summary", result)
        self.assertIn("- **Total Movies:** 1", result)

    def test_empty_markdown_output(self):
        """Test that empty markdown output is still valid markdown."""
        formatter = MarkdownFormatter()

        # Test empty show statistics
        show_result = formatter.format_show_statistics([])
        self.assertIn("# TV Show Statistics", show_result)
        self.assertIn("No TV shows found in your Plex library.", show_result)

        # Test empty movie statistics
        movie_result = formatter.format_movie_statistics([])
        self.assertIn("# Movie Statistics", movie_result)
        self.assertIn("No movies found in your Plex library.", movie_result)

        # Test empty recently watched
        recent_result = formatter.format_recently_watched([], media_type="show")
        self.assertIn("# Recently Watched Shows", recent_result)
        self.assertIn("No recently watched shows found.", recent_result)


class TestFormatterFactory(unittest.TestCase):
    """Test the FormatterFactory class."""

    def test_get_formatter(self):
        """Test that get_formatter returns the correct formatter instance."""
        # Test each formatter type
        self.assertIsInstance(FormatterFactory.get_formatter("table"), RichFormatter)
        self.assertIsInstance(FormatterFactory.get_formatter("json"), JsonFormatter)
        self.assertIsInstance(FormatterFactory.get_formatter("markdown"), MarkdownFormatter)
        self.assertIsInstance(FormatterFactory.get_formatter("csv"), CsvFormatter)
        self.assertIsInstance(FormatterFactory.get_formatter("yaml"), YamlFormatter)
        self.assertIsInstance(FormatterFactory.get_formatter("compact"), CompactFormatter)

    def test_get_formatter_invalid(self):
        """Test that get_formatter raises ValueError for invalid format names."""
        with self.assertRaises(ValueError):
            FormatterFactory.get_formatter("invalid_format")

    def test_register_formatter(self):
        """Test registering a new formatter type."""
        # Create a mock formatter class
        mock_formatter_class = MagicMock()
        mock_formatter_instance = MagicMock()
        mock_formatter_class.return_value = mock_formatter_instance

        try:
            # Register the mock formatter
            FormatterFactory.register_formatter("mock_format", mock_formatter_class)

            # Verify it's in the available formats
            self.assertIn("mock_format", FormatterFactory.get_available_formats())

            # Get the formatter and verify it's the correct type
            formatter = FormatterFactory.get_formatter("mock_format")
            self.assertEqual(formatter, mock_formatter_instance)
        finally:
            # Clean up - remove the mock formatter from the registry
            if "mock_format" in FormatterFactory._formatters:
                del FormatterFactory._formatters["mock_format"]

    def test_get_available_formats(self):
        """Test getting the list of available formats."""
        formats = FormatterFactory.get_available_formats()
        self.assertIsInstance(formats, list)
        self.assertIn("table", formats)
        self.assertIn("json", formats)
        self.assertIn("markdown", formats)
        self.assertIn("csv", formats)
        self.assertIn("yaml", formats)
        self.assertIn("compact", formats)


class TestBaseFormatterMethods(unittest.TestCase):
    """Test the new methods in BaseFormatter."""

    def setUp(self):
        """Set up test data."""

        # Create a simple formatter that implements the required methods
        class TestFormatter(BaseFormatter):
            def format_show_statistics(self, stats):
                return f"Shows: {len(stats)} items"

            def format_movie_statistics(self, stats):
                return f"Movies: {len(stats)} items"

            def format_recently_watched(self, stats, media_type="show"):
                return f"Recently watched {media_type}s: {len(stats)} items"

        self.formatter = TestFormatter()
        self.show_stats = [{"title": "Show1"}, {"title": "Show2"}]
        self.movie_stats = [{"title": "Movie1"}, {"title": "Movie2"}, {"title": "Movie3"}]
        self.recently_watched = [{"title": "Recent1"}, {"title": "Recent2"}]

    def test_format_content_shows(self):
        """Test format_content with show statistics."""
        outputs = self.formatter.format_content(
            self.show_stats, media_type="show", show_recent=False
        )
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0], "Shows: 2 items")

    def test_format_content_movies(self):
        """Test format_content with movie statistics."""
        outputs = self.formatter.format_content(
            self.movie_stats, media_type="movie", show_recent=False
        )
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0], "Movies: 3 items")

    def test_format_content_with_recent(self):
        """Test format_content with recently watched content."""
        outputs = self.formatter.format_content(
            self.show_stats,
            media_type="show",
            show_recent=True,
            recently_watched=self.recently_watched,
        )
        self.assertEqual(len(outputs), 2)
        self.assertEqual(outputs[0], "Shows: 2 items")
        self.assertEqual(outputs[1], "Recently watched shows: 2 items")

    def test_display_output(self):
        """Test displaying output to the console."""
        mock_console = MagicMock(spec=Console)
        outputs = ["Output 1", "Output 2", ""]  # Include an empty output that should be skipped

        self.formatter.display_output(mock_console, outputs)

        # Verify console.print was called for non-empty outputs
        self.assertEqual(mock_console.print.call_count, 2)
        mock_console.print.assert_any_call("Output 1")
        mock_console.print.assert_any_call("Output 2")


class TestIntegratedFormatting(unittest.TestCase):
    """Test the integration between the formatter factory and output methods."""

    def setUp(self):
        """Set up test data."""
        self.stats = [
            {
                "title": "Test Item",
                "total_episodes": 10,
                "watched_episodes": 5,
                "completion_percentage": 50.0,
                "total_watch_time_minutes": 150,
                "last_watched": datetime(2023, 4, 1, 12, 0, 0),
                "year": 2020,
                "rating": 8.5,
            }
        ]

        # Create test data that works for both show and movie formatters
        self.versatile_stats = [
            {
                "title": "Versatile Item",
                # Show fields
                "total_episodes": 10,
                "watched_episodes": 5,
                "completion_percentage": 50.0,
                "total_watch_time_minutes": 150,
                # Movie fields
                "watched": True,
                "watch_count": 2,
                "duration_minutes": 120,
                # Common fields
                "last_watched": datetime(2023, 4, 1, 12, 0, 0),
                "year": 2020,
                "rating": 8.5,
            }
        ]

        self.recently_watched = [
            {
                "title": "Recent Item",
                # Show fields
                "total_episodes": 10,
                "watched_episodes": 2,
                "completion_percentage": 20.0,
                "total_watch_time_minutes": 60,
                # Movie fields
                "watched": True,
                "watch_count": 1,
                "duration_minutes": 90,
                # Common fields
                "last_watched": datetime(2023, 4, 15, 12, 0, 0),
                "year": 2022,
                "rating": 9.0,
            }
        ]

    def test_json_format_content(self):
        """Test using format_content with JSON formatter."""
        formatter = FormatterFactory.get_formatter("json")
        outputs = formatter.format_content(
            self.stats, media_type="show", show_recent=True, recently_watched=self.recently_watched
        )

        self.assertEqual(len(outputs), 2)

        # Verify both outputs are valid JSON
        main_data = json.loads(outputs[0])
        self.assertEqual(len(main_data["shows"]), 1)
        self.assertEqual(main_data["shows"][0]["title"], "Test Item")

        recent_data = json.loads(outputs[1])
        self.assertEqual(len(recent_data["recently_watched_shows"]), 1)
        self.assertEqual(recent_data["recently_watched_shows"][0]["title"], "Recent Item")

    def test_yaml_format_content(self):
        """Test using format_content with YAML formatter."""
        formatter = FormatterFactory.get_formatter("yaml")
        outputs = formatter.format_content(
            self.versatile_stats,
            media_type="movie",
            show_recent=True,
            recently_watched=self.recently_watched,
        )

        self.assertEqual(len(outputs), 2)

        # Verify both outputs are valid YAML
        main_data = yaml.safe_load(outputs[0])
        self.assertIn("movies", main_data)
        self.assertEqual(len(main_data["movies"]), 1)

        recent_data = yaml.safe_load(outputs[1])
        self.assertIn("recently_watched_movies", recent_data)
        self.assertEqual(len(recent_data["recently_watched_movies"]), 1)

    def test_compact_format_content(self):
        """Test using format_content with Compact formatter."""
        formatter = FormatterFactory.get_formatter("compact")
        outputs = formatter.format_content(
            self.stats, media_type="show", show_recent=True, recently_watched=self.recently_watched
        )

        self.assertEqual(len(outputs), 2)
        # Compact formatter should have a minimal representation with pipes
        self.assertIn("|", outputs[0])
        self.assertIn("|", outputs[1])
        self.assertIn("Test Item", outputs[0])
        self.assertIn("Recent Item", outputs[1])

    @patch("plex_history_report.formatters.RichFormatter.format_show_statistics")
    @patch("plex_history_report.formatters.RichFormatter.format_recently_watched")
    def test_rich_formatter_direct_methods(self, mock_format_recent, mock_format_show):
        """Test that RichFormatter's methods are called correctly."""
        formatter = FormatterFactory.get_formatter("table")

        # Set up mocks to return string values
        mock_format_show.return_value = "Mock show statistics with summary"
        mock_format_recent.return_value = "Mock recently watched"

        # Call format_content
        outputs = formatter.format_content(
            self.stats, media_type="show", show_recent=True, recently_watched=self.recently_watched
        )

        # Verify the underlying methods were called
        mock_format_show.assert_called_once_with(self.stats)
        mock_format_recent.assert_called_once_with(self.recently_watched, media_type="show")

        # Check that the returned strings are included in the output
        self.assertEqual(len(outputs), 2)
        self.assertEqual(outputs[0], "Mock show statistics with summary")
        self.assertEqual(outputs[1], "Mock recently watched")


if __name__ == "__main__":
    unittest.main()
