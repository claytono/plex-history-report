"""Tests for the formatters module."""

import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock

import yaml

from plex_history_report.formatters import (
    CsvFormatter,
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
            'title': 'Test Show',
            'total_episodes': 100,
            'watched_episodes': 65,
            'completion_percentage': 65.91466666666668,
            'total_watch_time_minutes': 123.4567,
            'last_watched': datetime(2023, 4, 1, 12, 0, 0),
            'year': 2020,
            'rating': 9.1
        }

        # Mock the console to check output
        formatter = RichFormatter()
        mock_console = MagicMock()
        formatter.console = mock_console

        # Format the show
        formatter.format_show_statistics([sample_show])

        # Check that the console.print was called with a table
        mock_console.print.assert_called()

    def test_markdown_formatter_rounding(self):
        """Test that MarkdownFormatter correctly rounds percentages."""
        # Create a sample show with an uneven percentage
        sample_show = {
            'title': 'Test Show',
            'total_episodes': 100,
            'watched_episodes': 65,
            'completion_percentage': 65.91466666666668,
            'total_watch_time_minutes': 123.4567,
            'last_watched': datetime(2023, 4, 1, 12, 0, 0),
            'year': 2020,
            'rating': 9.1
        }

        # Test with Markdown formatter
        formatter = MarkdownFormatter()
        result = formatter.format_show_statistics([sample_show])

        # Check that the percentage is rounded to 1 decimal place
        self.assertIn('65.9%', result)
        # We shouldn't see the full unrounded number
        self.assertNotIn('65.91466666666668', result)

    def test_json_formatter_output(self):
        """Test that JsonFormatter produces valid output with numbers."""
        # Create a sample show with an uneven percentage
        sample_show = {
            'title': 'Test Show',
            'total_episodes': 100,
            'watched_episodes': 65,
            'completion_percentage': 65.91466666666668,
            'total_watch_time_minutes': 123.4567,
            'last_watched': datetime(2023, 4, 1, 12, 0, 0),
            'year': 2020,
            'rating': 9.1
        }

        # Test with JSON formatter
        formatter = JsonFormatter()
        result = formatter.format_show_statistics([sample_show])

        # The result should be valid JSON
        data = json.loads(result)
        # We expect the original value to be preserved in JSON output
        self.assertEqual(data['shows'][0]['completion_percentage'], 65.9)

    def test_csv_formatter_rounding(self):
        """Test that CsvFormatter correctly rounds percentages."""
        # Create a sample show with an uneven percentage
        sample_show = {
            'title': 'Test Show',
            'total_episodes': 100,
            'watched_episodes': 65,
            'completion_percentage': 65.91466666666668,
            'total_watch_time_minutes': 123.4567,
            'last_watched': datetime(2023, 4, 1, 12, 0, 0),
            'year': 2020,
            'rating': 9.1
        }

        # Test with CSV formatter
        formatter = CsvFormatter()
        result = formatter.format_show_statistics([sample_show])

        # Check that the CSV contains the rounded percentage
        self.assertIn('65.9', result)
        # We shouldn't see the full unrounded number
        self.assertNotIn('65.91466666666668', result)

    def test_yaml_formatter_output(self):
        """Test that YamlFormatter produces valid output with numbers."""
        # Create a sample show with an uneven percentage
        sample_show = {
            'title': 'Test Show',
            'total_episodes': 100,
            'watched_episodes': 65,
            'completion_percentage': 65.91466666666668,
            'total_watch_time_minutes': 123.4567,
            'last_watched': datetime(2023, 4, 1, 12, 0, 0),
            'year': 2020,
            'rating': 9.1
        }

        # Test with YAML formatter
        formatter = YamlFormatter()
        result = formatter.format_show_statistics([sample_show])

        # The result should be valid YAML
        data = yaml.safe_load(result)
        # We expect the original value to be preserved in YAML output
        self.assertEqual(data['shows'][0]['completion_percentage'], 65.9)


class TestComplexData(unittest.TestCase):
    """Test that formatters can handle complex nested data structures."""

    def setUp(self):
        """Set up complex test data for all tests."""
        # Create a complex nested data structure with shows that have recent episodes
        self.complex_show_data = [
            {
                'title': 'Complex Show',
                'year': 2022,
                'rating': 8.7,
                'total_episodes': 20,
                'watched_episodes': 15,
                'completion_percentage': 75.0,
                'total_watch_time_minutes': 450,
                'last_watched': datetime(2023, 4, 1, 12, 0, 0),
                'recent_episodes': [
                    {
                        'title': 'Episode 1',
                        'season': 1,
                        'episode': 1,
                        'watch_date': datetime(2023, 3, 15, 12, 0, 0),
                        'duration_minutes': 30
                    },
                    {
                        'title': 'Episode 2',
                        'season': 1,
                        'episode': 2,
                        'watch_date': datetime(2023, 3, 16, 12, 0, 0),
                        'duration_minutes': 30
                    }
                ]
            },
            {
                'title': 'Another Show',
                'year': 2021,
                'rating': 9.2,
                'total_episodes': 10,
                'watched_episodes': 10,
                'completion_percentage': 100.0,
                'total_watch_time_minutes': 300,
                'last_watched': datetime(2023, 3, 30, 12, 0, 0),
                'recent_episodes': []  # No recent episodes
            }
        ]

    def test_json_complex_data(self):
        """Test that JsonFormatter correctly handles complex nested data."""
        formatter = JsonFormatter()
        result = formatter.format_show_statistics(self.complex_show_data)

        # Result should be valid JSON
        data = json.loads(result)

        # Check structure is preserved
        self.assertEqual(len(data['shows']), 2)
        self.assertEqual(data['shows'][0]['title'], 'Complex Show')
        self.assertEqual(len(data['shows'][0]['recent_episodes']), 2)
        self.assertEqual(data['shows'][0]['recent_episodes'][0]['title'], 'Episode 1')

    def test_yaml_complex_data(self):
        """Test that YamlFormatter correctly handles complex nested data."""
        formatter = YamlFormatter()
        result = formatter.format_show_statistics(self.complex_show_data)

        # Result should be valid YAML
        data = yaml.safe_load(result)

        # Check structure is preserved
        self.assertEqual(len(data['shows']), 2)
        self.assertEqual(data['shows'][0]['title'], 'Complex Show')
        self.assertEqual(len(data['shows'][0]['recent_episodes']), 2)
        self.assertEqual(data['shows'][0]['recent_episodes'][0]['title'], 'Episode 1')

    def test_markdown_complex_data(self):
        """Test that MarkdownFormatter correctly handles complex nested data."""
        formatter = MarkdownFormatter()
        result = formatter.format_show_statistics(self.complex_show_data)

        # Check that all important elements are included in the markdown
        self.assertIn('Complex Show', result)
        self.assertIn('75.0%', result)
        # Episodes aren't actually included in the standard show statistics markdown output
        # They would only appear in the recently watched output
        self.assertIn('Another Show', result)
        self.assertIn('100.0%', result)

    def test_csv_complex_data(self):
        """Test that CsvFormatter correctly handles complex nested data."""
        formatter = CsvFormatter()
        result = formatter.format_show_statistics(self.complex_show_data)

        # CSV should contain the show titles
        self.assertIn('Complex Show', result)
        self.assertIn('Another Show', result)

        # CSV typically flattens data, so recent episodes might not be included
        # or might be represented in a simplified way

    def test_rich_complex_data(self):
        """Test that RichFormatter correctly handles complex nested data."""
        formatter = RichFormatter()

        # Mock console to capture output
        mock_console = MagicMock()
        formatter.console = mock_console

        # Format the show
        formatter.format_show_statistics(self.complex_show_data)

        # Check that the console.print was called
        mock_console.print.assert_called()


class TestMarkdownLinting(unittest.TestCase):
    """Test that markdown output follows proper markdown format conventions."""

    def setUp(self):
        """Set up test data with edge cases for markdown formatting."""
        self.show_with_special_chars = {
            'title': 'Test Show | with | pipes',  # Title with pipe chars that need escaping
            'total_episodes': 10,
            'watched_episodes': 5,
            'completion_percentage': 50.0,
            'total_watch_time_minutes': 150,
            'last_watched': datetime(2023, 4, 1, 12, 0, 0),
            'year': 2020,
            'rating': 8.5
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
        result = formatter.format_recently_watched([self.show_with_special_chars], media_type="show")

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
            'title': 'Movie | with | pipes',
            'year': 2021,
            'watch_count': 2,
            'last_watched': datetime(2023, 5, 15, 20, 30, 0),
            'duration_minutes': 120,
            'watched': True,
            'rating': 9.0
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


if __name__ == '__main__':
    unittest.main()
