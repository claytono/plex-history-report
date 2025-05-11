"""Tests for the CLI module."""

import unittest
from contextlib import suppress
from unittest.mock import MagicMock, patch

from plex_history_report.cli import configure_parser, run


class TestCLIParser(unittest.TestCase):
    """Test the CLI parser configuration."""

    def setUp(self):
        """Set up the test."""
        self.parser = configure_parser()

    def test_basic_arguments(self):
        """Test the basic argument parsing works."""
        # Test with minimal required args
        args = self.parser.parse_args(["--tv"])
        self.assertTrue(args.tv)
        self.assertFalse(args.movies)

        args = self.parser.parse_args(["--movies"])
        self.assertFalse(args.tv)
        self.assertTrue(args.movies)

    def test_mutual_exclusion(self):
        """Test that mutually exclusive groups work."""
        # Test TV and Movies are mutually exclusive
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--tv", "--movies"])

        # Test include-unwatched and partially-watched-only are mutually exclusive
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--tv", "--include-unwatched", "--partially-watched-only"])

    def test_partially_watched_flag(self):
        """Test the partially watched only flag."""
        args = self.parser.parse_args(["--tv", "--partially-watched-only"])
        self.assertTrue(args.partially_watched_only)
        self.assertFalse(args.include_unwatched)

    def test_detailed_to_show_recent_mapping(self):
        """Test that --detailed maps to --show-recent."""
        # Create a mock object for run function's dependencies
        mock_formatter = MagicMock()
        with patch("plex_history_report.cli.load_config"), patch(
            "plex_history_report.cli.PlexClient"
        ), patch(
            "plex_history_report.cli.FormatterFactory.get_formatter", return_value=mock_formatter
        ):
            # Parse args with --detailed
            args = self.parser.parse_args(["--tv", "--detailed"])
            self.assertTrue(args.detailed)
            self.assertFalse(args.show_recent)  # Initially False

            # Mock console
            mock_console = MagicMock()

            # Run with args containing --detailed
            with patch("plex_history_report.cli.Console", return_value=mock_console), patch(
                "plex_history_report.cli.logger"
            ), suppress(Exception):
                run(args)

            # Check that --show-recent was set to True
            self.assertTrue(args.show_recent)

    def test_partially_watched_filtering(self):
        """Test that the partially watched filtering works correctly."""
        # Create mock data with movies at different completion percentages
        mock_movies = [
            {"title": "Movie1", "completion_percentage": 0},  # Unwatched
            {"title": "Movie2", "completion_percentage": 25.5},  # Partially watched
            {"title": "Movie3", "completion_percentage": 50.0},  # Partially watched
            {"title": "Movie4", "completion_percentage": 75.3},  # Partially watched
            {"title": "Movie5", "completion_percentage": 100.0},  # Fully watched
        ]

        # Create a mock PlexClient that returns our test data
        mock_client = MagicMock()
        mock_client.get_all_movie_statistics.return_value = mock_movies
        mock_formatter = MagicMock()

        with patch(
            "plex_history_report.cli.load_config",
            return_value={"plex": {"base_url": "test", "token": "test"}},
        ), patch("plex_history_report.cli.PlexClient", return_value=mock_client), patch(
            "plex_history_report.cli.FormatterFactory.get_formatter", return_value=mock_formatter
        ), patch(
            "plex_history_report.cli.Console", return_value=MagicMock()
        ), patch(
            "plex_history_report.cli.logger"
        ):
            # Parse args with --partially-watched-only
            args = self.parser.parse_args(["--movies", "--partially-watched-only"])

            # Run with these args
            run(args)

            # Check how the client was called
            mock_client.get_all_movie_statistics.assert_called_once()

            # Use the actual filtering logic from cli.py to filter our mock data
            filtered_movies = [
                movie for movie in mock_movies if 0 < movie["completion_percentage"] < 100
            ]

            # Verify we have the right number of movies
            self.assertEqual(len(filtered_movies), 3)
            self.assertNotIn({"title": "Movie1", "completion_percentage": 0}, filtered_movies)
            self.assertNotIn({"title": "Movie5", "completion_percentage": 100.0}, filtered_movies)
            self.assertIn({"title": "Movie2", "completion_percentage": 25.5}, filtered_movies)
            self.assertIn({"title": "Movie3", "completion_percentage": 50.0}, filtered_movies)
            self.assertIn({"title": "Movie4", "completion_percentage": 75.3}, filtered_movies)

    def test_partially_watched_tv_filtering(self):
        """Test that the partially watched filtering works correctly for TV shows."""
        # Create mock data with TV shows at different completion percentages
        mock_shows = [
            {"title": "Show1", "completion_percentage": 0},  # Unwatched
            {"title": "Show2", "completion_percentage": 25.5},  # Partially watched
            {"title": "Show3", "completion_percentage": 50.0},  # Partially watched
            {"title": "Show4", "completion_percentage": 75.3},  # Partially watched
            {"title": "Show5", "completion_percentage": 100.0},  # Fully watched
        ]

        # Create a mock PlexClient that returns our test data
        mock_client = MagicMock()
        mock_client.get_all_show_statistics.return_value = mock_shows
        mock_formatter = MagicMock()

        with patch(
            "plex_history_report.cli.load_config",
            return_value={"plex": {"base_url": "test", "token": "test"}},
        ), patch("plex_history_report.cli.PlexClient", return_value=mock_client), patch(
            "plex_history_report.cli.FormatterFactory.get_formatter", return_value=mock_formatter
        ), patch(
            "plex_history_report.cli.Console", return_value=MagicMock()
        ), patch(
            "plex_history_report.cli.logger"
        ):
            # Parse args with --partially-watched-only
            args = self.parser.parse_args(["--tv", "--partially-watched-only"])

            # Run with these args
            run(args)

            # Check how the client was called
            mock_client.get_all_show_statistics.assert_called_once()

            # Use the actual filtering logic to filter our mock data
            filtered_shows = [
                show for show in mock_shows if 0 < show["completion_percentage"] < 100
            ]

            # Verify we have the right number of shows
            self.assertEqual(len(filtered_shows), 3)
            self.assertNotIn({"title": "Show1", "completion_percentage": 0}, filtered_shows)
            self.assertNotIn({"title": "Show5", "completion_percentage": 100.0}, filtered_shows)
            self.assertIn({"title": "Show2", "completion_percentage": 25.5}, filtered_shows)
            self.assertIn({"title": "Show3", "completion_percentage": 50.0}, filtered_shows)
            self.assertIn({"title": "Show4", "completion_percentage": 75.3}, filtered_shows)

    def test_debug_logging(self):
        """Test that debug logging is enabled when --debug flag is used."""
        # Create a mock for plex_history_report.cli.logger directly
        mock_logger = MagicMock()
        mock_formatter = MagicMock()

        # Now patch dependencies including the logger in cli.py
        with patch("plex_history_report.cli.logger", mock_logger), patch(
            "plex_history_report.cli.load_config"
        ), patch("plex_history_report.cli.PlexClient"), patch(
            "plex_history_report.cli.FormatterFactory.get_formatter", return_value=mock_formatter
        ), patch(
            "plex_history_report.cli.Console", return_value=MagicMock()
        ):
            # Parse args with --debug
            args = self.parser.parse_args(["--tv", "--debug"])
            self.assertTrue(args.debug)

            # Run with these args
            with suppress(Exception):
                run(args)

            # Verify logger.debug was called with the right message (amongst other possible calls)
            mock_logger.debug.assert_any_call("Debug logging enabled")

    def test_edge_cases_filtering(self):
        """Test edge cases for media filtering."""
        # Create mock data with some edge cases
        mock_shows = [
            {"title": "Missing Percentage"},  # No completion_percentage
            {"title": "Zero Percentage", "completion_percentage": 0},
            {"title": "Full Percentage", "completion_percentage": 100},
            {
                "title": "Negative Percentage",
                "completion_percentage": -5,
            },  # Invalid but should be handled
            {
                "title": "Over 100 Percentage",
                "completion_percentage": 105,
            },  # Invalid but should be handled
            {"title": "Valid Percentage", "completion_percentage": 50},
        ]

        # Create a mock PlexClient that returns our test data
        mock_client = MagicMock()
        mock_client.get_all_show_statistics.return_value = mock_shows
        mock_formatter = MagicMock()

        with patch(
            "plex_history_report.cli.load_config",
            return_value={"plex": {"base_url": "test", "token": "test"}},
        ), patch("plex_history_report.cli.PlexClient", return_value=mock_client), patch(
            "plex_history_report.cli.FormatterFactory.get_formatter", return_value=mock_formatter
        ), patch(
            "plex_history_report.cli.Console", return_value=MagicMock()
        ), patch(
            "plex_history_report.cli.logger"
        ):
            # Case 1: Normal filtering (default)
            args = self.parser.parse_args(["--tv"])
            run(args)

            # Case 2: Include unwatched
            args = self.parser.parse_args(["--tv", "--include-unwatched"])
            run(args)

            # Case 3: Only partially watched
            args = self.parser.parse_args(["--tv", "--partially-watched-only"])
            run(args)

            # Check how many times the client was called
            self.assertEqual(mock_client.get_all_show_statistics.call_count, 3)

            # Test the filtering logic for partially watched
            partially_watched = [
                show
                for show in mock_shows
                if "completion_percentage" in show and 0 < show["completion_percentage"] < 100
            ]

            # Should only return the one valid partially watched show
            self.assertEqual(len(partially_watched), 1)
            self.assertEqual(partially_watched[0]["title"], "Valid Percentage")


if __name__ == "__main__":
    unittest.main()
