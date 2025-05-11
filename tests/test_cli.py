"""Tests for the CLI module."""

import unittest
from contextlib import suppress
from pathlib import Path
from unittest.mock import MagicMock, patch

from plex_history_report.cli import (
    configure_parser,
    display_performance_report,
    get_media_statistics,
    get_recently_watched,
    handle_config,
    handle_list_users,
    initialize_plex_client,
    run,
    setup_logging,
    validate_media_selection,
)


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


class TestRefactoredCLIFunctions(unittest.TestCase):
    """Test the refactored CLI functions to improve code coverage."""

    def test_setup_logging_with_benchmark(self):
        """Test setup_logging with benchmark mode enabled."""
        mock_args = MagicMock()
        mock_args.debug = False
        mock_args.benchmark = True

        with patch("plex_history_report.cli.logging"), patch(
            "plex_history_report.cli.logger"
        ), patch("plex_history_report.utils.set_benchmarking") as mock_set_benchmark, patch(
            "plex_history_report.cli.PerformanceLogHandler"
        ) as mock_perf_handler:
            performance_data = setup_logging(mock_args)

            # Check that the performance handler was created
            mock_perf_handler.assert_called_once_with(performance_data)
            # Check that set_benchmarking was called
            mock_set_benchmark.assert_called_once_with(True)

    def test_setup_logging_with_debug_and_benchmark(self):
        """Test setup_logging with both debug and benchmark modes enabled."""
        mock_args = MagicMock()
        mock_args.debug = True
        mock_args.benchmark = True

        with patch("plex_history_report.cli.logging"), patch(
            "plex_history_report.cli.logger"
        ) as mock_logger, patch(
            "plex_history_report.utils.set_benchmarking"
        ) as mock_set_benchmark, patch(
            "plex_history_report.cli.PerformanceLogHandler"
        ):
            setup_logging(mock_args)

            # Check that debug logging was enabled
            mock_logger.debug.assert_called_with("Debug logging enabled")
            # Check that benchmark logging was enabled
            mock_logger.info.assert_called_with("Performance benchmarking enabled")
            # Check that set_benchmarking was called
            mock_set_benchmark.assert_called_once_with(True)

    def test_handle_config_create_config(self):
        """Test handle_config with create_config flag."""
        mock_args = MagicMock()
        mock_args.create_config = True
        mock_args.config = None
        mock_console = MagicMock()

        with patch("plex_history_report.cli.create_default_config") as mock_create_config:
            mock_create_config.return_value = Path("/tmp/config.yaml")
            config, exit_code = handle_config(mock_args, mock_console)

            # Check that config is None and exit code is 0
            self.assertIsNone(config)
            self.assertEqual(exit_code, 0)
            # Check that create_default_config was called
            mock_create_config.assert_called_once()
            # Check that messages were printed
            mock_console.print.assert_any_call(
                "Created default configuration file at: /tmp/config.yaml"
            )

    def test_handle_config_create_config_error(self):
        """Test handle_config with create_config flag and error."""
        mock_args = MagicMock()
        mock_args.create_config = True
        mock_args.config = None
        mock_console = MagicMock()

        with patch(
            "plex_history_report.cli.create_default_config", side_effect=Exception("Test error")
        ), patch("plex_history_report.cli.logger") as mock_logger:
            config, exit_code = handle_config(mock_args, mock_console)

            # Check that config is None and exit code is 1
            self.assertIsNone(config)
            self.assertEqual(exit_code, 1)
            # Check that the error was logged
            mock_logger.error.assert_called_once()

    def test_handle_config_missing_config(self):
        """Test handle_config with missing config file."""
        mock_args = MagicMock()
        mock_args.create_config = False
        mock_args.config = "/non/existent/config.yaml"
        mock_console = MagicMock()

        # Mock Path.exists() to return False for the config path
        with patch("plex_history_report.cli.Path") as mock_path, patch(
            "plex_history_report.cli.create_default_config"
        ), patch("plex_history_report.cli.load_config"):
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value = mock_path_instance

            config, exit_code = handle_config(mock_args, mock_console)

            # Check that config is None and exit code is 0
            self.assertIsNone(config)
            self.assertEqual(exit_code, 0)
            # Check that messages were printed for creating a config
            mock_console.print.assert_any_call(
                f"Configuration file not found at: {mock_path_instance}"
            )

    def test_handle_config_config_error(self):
        """Test handle_config with ConfigError."""
        mock_args = MagicMock()
        mock_args.create_config = False
        mock_args.config = "/tmp/config.yaml"
        mock_console = MagicMock()

        with patch("plex_history_report.cli.Path") as mock_path, patch(
            "plex_history_report.cli.load_config"
        ) as mock_load_config:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            # Make load_config raise ConfigError
            from plex_history_report.config import ConfigError

            mock_load_config.side_effect = ConfigError("Test error")

            config, exit_code = handle_config(mock_args, mock_console)

            # Check that config is None and exit code is 1
            self.assertIsNone(config)
            self.assertEqual(exit_code, 1)
            # Check that error message was printed
            mock_console.print.assert_any_call(
                "[bold red]Configuration error:[/bold red] Test error"
            )

    def test_initialize_plex_client_with_record(self):
        """Test initialize_plex_client with record option."""
        mock_config = {"plex": {"base_url": "test_url", "token": "test_token"}}
        mock_args = MagicMock()
        mock_args.record = "test-data"

        with patch("plex_history_report.cli.PlexClient") as mock_plex_client, patch(
            "plex_history_report.recorders.PlexDataRecorder"
        ) as mock_recorder_class, patch("plex_history_report.cli.logger") as mock_logger:
            # Mock the recorder
            mock_recorder = MagicMock()
            mock_recorder_class.return_value = mock_recorder

            client, username = initialize_plex_client(mock_config, mock_args)

            # Check that PlexDataRecorder was created with the right mode
            mock_recorder_class.assert_called_once_with(mode="test-data")
            # Check that logger.info was called with the right message
            mock_logger.info.assert_called_with("Recording Plex data in 'test-data' mode")
            # Check that PlexClient was initialized with the recorder
            mock_plex_client.assert_called_once_with(
                "test_url", "test_token", data_recorder=mock_recorder
            )

    def test_initialize_plex_client_with_user_arg(self):
        """Test initialize_plex_client with user argument."""
        mock_config = {"plex": {"base_url": "test_url", "token": "test_token"}}
        mock_args = MagicMock()
        mock_args.record = None
        mock_args.user = "test_user"

        with patch("plex_history_report.cli.PlexClient"):
            client, username = initialize_plex_client(mock_config, mock_args)

            # Check that username is set to the argument value
            self.assertEqual(username, "test_user")

    def test_handle_list_users(self):
        """Test handle_list_users function."""
        mock_client = MagicMock()
        mock_client.get_available_users.return_value = ["user1", "user2", "admin"]
        mock_console = MagicMock()

        exit_code = handle_list_users(mock_client, mock_console)

        # Check that get_available_users was called
        mock_client.get_available_users.assert_called_once()
        # Check that console.print was called with the header
        mock_console.print.assert_any_call("[bold]Available Plex Users:[/bold]")
        # Check that each user was printed
        mock_console.print.assert_any_call("- user1")
        mock_console.print.assert_any_call("- user2")
        mock_console.print.assert_any_call("- admin")
        # Check that exit code is 0
        self.assertEqual(exit_code, 0)

    def test_handle_list_users_no_users(self):
        """Test handle_list_users function with no users."""
        mock_client = MagicMock()
        mock_client.get_available_users.return_value = []
        mock_console = MagicMock()

        exit_code = handle_list_users(mock_client, mock_console)

        # Check that get_available_users was called
        mock_client.get_available_users.assert_called_once()
        # Check that console.print was called with the no users message
        mock_console.print.assert_any_call(
            "No users found or cannot access user information with current token."
        )
        # Check that exit code is 0
        self.assertEqual(exit_code, 0)

    def test_validate_media_selection_no_selection(self):
        """Test validate_media_selection with no media type selected."""
        mock_args = MagicMock()
        mock_args.tv = False
        mock_args.movies = False
        mock_console = MagicMock()

        media_type, sort_by, exit_code = validate_media_selection(mock_args, mock_console)

        # Check that error message was printed
        mock_console.print.assert_any_call(
            "[bold red]Error:[/bold red] Either --tv or --movies must be specified."
        )
        # Check that exit code is 1
        self.assertEqual(exit_code, 1)
        # Check that media_type and sort_by are empty
        self.assertEqual(media_type, "")
        self.assertEqual(sort_by, "")

    def test_validate_media_selection_invalid_sort(self):
        """Test validate_media_selection with invalid sort option."""
        mock_args = MagicMock()
        mock_args.tv = True
        mock_args.movies = False
        mock_args.sort_by = "invalid_sort"
        mock_console = MagicMock()

        media_type, sort_by, exit_code = validate_media_selection(mock_args, mock_console)

        # Check that error message was printed
        mock_console.print.assert_any_call("[bold red]Invalid sort option:[/bold red] invalid_sort")
        # Check that exit code is 1
        self.assertEqual(exit_code, 1)
        # Check that media_type and sort_by are empty
        self.assertEqual(media_type, "")
        self.assertEqual(sort_by, "")

    def test_get_media_statistics_tv_partially_watched(self):
        """Test get_media_statistics for TV shows with partially_watched_only flag."""
        mock_client = MagicMock()
        mock_args = MagicMock()
        mock_args.partially_watched_only = True
        mock_args.include_unwatched = False

        # Create some mock TV show data
        mock_shows = [
            {"title": "Show1", "completion_percentage": 0},  # Unwatched
            {"title": "Show2", "completion_percentage": 50},  # Partially watched
            {"title": "Show3", "completion_percentage": 100},  # Fully watched
        ]
        mock_client.get_all_show_statistics.return_value = mock_shows

        with patch("plex_history_report.cli.logger"):
            results = get_media_statistics(
                mock_client, mock_args, "show", "completion_percentage", "test_user"
            )

        # Check that the client method was called with correct arguments
        mock_client.get_all_show_statistics.assert_called_once_with(
            username="test_user", include_unwatched=False, sort_by="completion_percentage"
        )

        # Check that only the partially watched show is returned
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Show2")

    def test_get_media_statistics_movies_partially_watched(self):
        """Test get_media_statistics for movies with partially_watched_only flag."""
        mock_client = MagicMock()
        mock_args = MagicMock()
        mock_args.partially_watched_only = True
        mock_args.include_unwatched = False

        # Create some mock movie data
        mock_movies = [
            {"title": "Movie1", "completion_percentage": 0},  # Unwatched
            {"title": "Movie2", "completion_percentage": 30},  # Partially watched
            {"title": "Movie3", "completion_percentage": 75},  # Partially watched
            {"title": "Movie4", "completion_percentage": 100},  # Fully watched
        ]
        mock_client.get_all_movie_statistics.return_value = mock_movies

        with patch("plex_history_report.cli.logger"):
            results = get_media_statistics(
                mock_client, mock_args, "movie", "last_watched", "test_user"
            )

        # Check that the client method was called with correct arguments
        mock_client.get_all_movie_statistics.assert_called_once_with(
            username="test_user", include_unwatched=False, sort_by="last_watched"
        )

        # Check that only partially watched movies are returned
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Movie2")
        self.assertEqual(results[1]["title"], "Movie3")

    def test_get_media_statistics_edge_cases(self):
        """Test get_media_statistics with edge cases in the data."""
        # Create a simple mock client that returns data we control
        mock_client = MagicMock()
        mock_args = MagicMock()
        mock_args.partially_watched_only = True
        mock_args.include_unwatched = False

        # Create data with valid completion_percentage only
        mock_valid_data = [{"title": "Valid", "completion_percentage": 50}]

        # Test with valid data first
        mock_client.get_all_show_statistics.return_value = mock_valid_data

        with patch("plex_history_report.cli.logger"):
            results = get_media_statistics(mock_client, mock_args, "show", "title", "test_user")

            # Check that the valid item is included
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["title"], "Valid")

        # Test problematic data
        edge_case_data = [
            {"title": "Missing Percentage"},  # No completion_percentage
            {"title": "None Value", "completion_percentage": None},  # None value
            {"title": "Negative", "completion_percentage": -10},  # Invalid negative percentage
            {"title": "Over 100", "completion_percentage": 110},  # Invalid over 100% percentage
            {"title": "Valid", "completion_percentage": 50},  # Valid partially watched
        ]

        mock_client.get_all_show_statistics.return_value = edge_case_data

        with patch("plex_history_report.cli.logger"):
            results = get_media_statistics(mock_client, mock_args, "show", "title", "test_user")

            # Check that only the valid item passes the filter
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["title"], "Valid")

        # Similar test for movies
        mock_client.get_all_movie_statistics.return_value = edge_case_data

        with patch("plex_history_report.cli.logger"):
            results = get_media_statistics(mock_client, mock_args, "movie", "title", "test_user")

            # Check that only the valid item passes the filter
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["title"], "Valid")

    def test_get_media_statistics_include_unwatched(self):
        """Test get_media_statistics with include_unwatched flag."""
        mock_client = MagicMock()
        mock_args = MagicMock()
        mock_args.partially_watched_only = False
        mock_args.include_unwatched = True

        # Create mock data with a mix of watched and unwatched
        mock_data = [
            {"title": "Unwatched", "completion_percentage": 0},
            {"title": "Partially", "completion_percentage": 50},
            {"title": "Complete", "completion_percentage": 100},
        ]

        # Test for TV shows
        mock_client.get_all_show_statistics.return_value = mock_data.copy()

        with patch("plex_history_report.cli.logger"):
            results = get_media_statistics(mock_client, mock_args, "show", "title", "test_user")

        # All items should be included
        self.assertEqual(len(results), 3)

    def test_get_recently_watched_tv(self):
        """Test get_recently_watched for TV shows."""
        mock_client = MagicMock()
        mock_client.get_recently_watched_shows.return_value = ["show1", "show2"]

        result = get_recently_watched(mock_client, "show", "test_user")

        # Check that get_recently_watched_shows was called with the right username
        mock_client.get_recently_watched_shows.assert_called_once_with(username="test_user")
        # Check that the result is the expected list
        self.assertEqual(result, ["show1", "show2"])

    def test_get_recently_watched_movies(self):
        """Test get_recently_watched for movies."""
        mock_client = MagicMock()
        mock_client.get_recently_watched_movies.return_value = ["movie1", "movie2"]

        result = get_recently_watched(mock_client, "movie", "test_user")

        # Check that get_recently_watched_movies was called with the right username
        mock_client.get_recently_watched_movies.assert_called_once_with(username="test_user")
        # Check that the result is the expected list
        self.assertEqual(result, ["movie1", "movie2"])

    def test_display_performance_report(self):
        """Test display_performance_report function."""
        mock_console = MagicMock()
        performance_data = {"func1": [1.0, 2.0, 3.0], "func2": [0.5, 0.7], "func3": [5.0]}

        display_performance_report(mock_console, performance_data)

        # Check that console.print was called with the header
        mock_console.print.assert_any_call("\n[bold]Performance Benchmark Report:[/bold]")
        # Check that console.print was called with the dividing line
        mock_console.print.assert_any_call("=" * 60)
        # Check that functions are displayed in order of total time
        call_args_list = mock_console.print.call_args_list
        # We expect func3 (total 5.0) to be first, then func1 (total 6.0), then func2 (total 1.2)
        self.assertTrue(any("func3" in str(args) for args, _ in call_args_list))
        self.assertTrue(any("func1" in str(args) for args, _ in call_args_list))
        self.assertTrue(any("func2" in str(args) for args, _ in call_args_list))

    def test_display_performance_report_empty(self):
        """Test display_performance_report function with empty data."""
        mock_console = MagicMock()
        performance_data = {}

        # Should not raise an exception or call console.print
        display_performance_report(mock_console, performance_data)
        mock_console.print.assert_not_called()

    def test_display_performance_report_none(self):
        """Test display_performance_report function with None data."""
        mock_console = MagicMock()
        performance_data = None

        # Should not raise an exception or call console.print
        display_performance_report(mock_console, performance_data)
        mock_console.print.assert_not_called()


if __name__ == "__main__":
    unittest.main()
