"""Integration tests for Plex History Report CLI.

This module contains integration tests that verify the CLI works correctly
by mocking the PlexClient to use our fixture data instead of calling a real Plex server.
"""

import io
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console

from plex_history_report.cli import run


class MockPlexClient:
    """Mock PlexClient that returns our fixture data instead of calling a real Plex server."""

    def _convert_date_strings(self, items):
        """Convert ISO format date strings to datetime objects.

        Args:
            items: List of dictionaries that might contain date strings.
        """
        from datetime import datetime

        if not items:
            return

        for item in items:
            # Convert last_watched if it's a string
            if "last_watched" in item and isinstance(item["last_watched"], str):
                try:
                    item["last_watched"] = datetime.fromisoformat(item["last_watched"])
                except ValueError:
                    # If conversion fails, set to None
                    item["last_watched"] = None

            # Convert viewed_at if it's a string
            if "viewed_at" in item and isinstance(item["viewed_at"], str):
                try:
                    item["viewed_at"] = datetime.fromisoformat(item["viewed_at"])
                except ValueError:
                    # If conversion fails, set to None
                    item["viewed_at"] = None

    def _load_fixtures(self):
        """Load test fixtures from JSON files."""
        import json

        # Load TV show data
        with self.tv_fixtures_path.open("r", encoding="utf-8") as f:
            tv_data = json.load(f)
            self.all_shows = tv_data.get("all_shows", [])
            self.recently_watched_shows = tv_data.get("recently_watched_shows", [])

            # Convert string dates to datetime objects
            self._convert_date_strings(self.all_shows)
            self._convert_date_strings(self.recently_watched_shows)

        # Load movie data
        with self.movie_fixtures_path.open("r", encoding="utf-8") as f:
            movie_data = json.load(f)
            self.all_movies = movie_data.get("all_movies", [])
            self.recently_watched_movies = movie_data.get("recently_watched_movies", [])

            # Convert string dates to datetime objects
            self._convert_date_strings(self.all_movies)
            self._convert_date_strings(self.recently_watched_movies)

    def __init__(self, base_url=None, token=None, data_recorder=None):
        """Initialize the mock client with our test fixtures.

        Args:
            base_url: Ignored in the mock.
            token: Ignored in the mock.
            data_recorder: Optional recorder for capturing data.
        """
        self.base_url = base_url
        self.token = token
        self.data_recorder = data_recorder

        # Load test fixtures
        fixtures_dir = Path(__file__).parent / "fixtures"
        self.tv_fixtures_path = fixtures_dir / "plex_test_tv_data.json"
        self.movie_fixtures_path = fixtures_dir / "plex_test_movie_data.json"

        # Check if fixtures exist
        if not self.tv_fixtures_path.exists():
            raise FileNotFoundError(f"TV fixture not found: {self.tv_fixtures_path}")
        if not self.movie_fixtures_path.exists():
            raise FileNotFoundError(f"Movie fixture not found: {self.movie_fixtures_path}")

        # Load fixtures
        self._load_fixtures()

    def get_library_sections(self):
        """Mock getting library sections."""
        # Return minimal section data for tests
        return [
            {"type": "show", "title": "TV Shows"},
            {"type": "movie", "title": "Movies"},
        ]

    def get_all_show_statistics(
        self, username=None, include_unwatched=False, partially_watched_only=False, sort_by="title"
    ):
        """Mock getting TV show statistics.

        Args:
            username: Filter statistics for a specific user.
            include_unwatched: Include shows with no watched episodes.
            partially_watched_only: Only include shows that are partially watched.
            sort_by: Field to sort results by.

        Returns:
            List of show statistics from our fixture data.
        """
        # Use username to avoid unused argument lint error
        _ = username
        # Record the call if a recorder is present
        if self.data_recorder:
            self.data_recorder.record_data("all_shows", self.all_shows)

        # Apply filtering based on the parameters
        result = self.all_shows.copy()

        # Filter unwatched shows if needed
        if not include_unwatched:
            result = [show for show in result if show.get("watched_episodes", 0) > 0]

        # Filter for partially watched shows if needed
        if partially_watched_only:
            result = [show for show in result if 0 < show.get("completion_percentage", 0) < 100]

        # Apply sorting
        if sort_by == "title":
            result.sort(key=lambda x: x.get("title", "").lower())
        elif sort_by == "watched_episodes":
            result.sort(key=lambda x: x.get("watched_episodes", 0), reverse=True)
        elif sort_by == "completion_percentage":
            result.sort(key=lambda x: x.get("completion_percentage", 0), reverse=True)
        elif sort_by in ["last_watched", "year", "rating"]:
            # For these fields, items with None values should be at the end
            result.sort(
                key=lambda x: (x.get(sort_by) is None, x.get(sort_by)),
                reverse=sort_by != "title",
            )

        return result

    def get_all_movie_statistics(
        self, username=None, include_unwatched=False, partially_watched_only=False, sort_by="title"
    ):
        """Mock getting movie statistics.

        Args:
            username: Filter statistics for a specific user.
            include_unwatched: Include unwatched movies.
            partially_watched_only: Only include partially watched movies.
            sort_by: Field to sort results by.

        Returns:
            List of movie statistics from our fixture data.
        """
        # Use username to avoid unused argument lint error
        _ = username
        # Record the call if a recorder is present
        if self.data_recorder:
            self.data_recorder.record_data("all_movies", self.all_movies)

        # Apply filtering based on the parameters
        result = self.all_movies.copy()

        # Filter unwatched movies if needed
        if not include_unwatched:
            result = [movie for movie in result if movie.get("watched", False)]

        # Filter for partially watched movies if needed
        if partially_watched_only:
            result = [movie for movie in result if 0 < movie.get("completion_percentage", 0) < 100]

        # Apply sorting
        if sort_by == "title":
            result.sort(key=lambda x: x.get("title", "").lower())
        elif sort_by == "watch_count":
            result.sort(key=lambda x: x.get("watch_count", 0), reverse=True)
        elif sort_by == "duration_minutes":
            result.sort(key=lambda x: x.get("duration_minutes", 0), reverse=True)
        elif sort_by in ["last_watched", "year", "rating"]:
            # For these fields, items with None values should be at the end
            result.sort(
                key=lambda x: (x.get(sort_by) is None, x.get(sort_by)),
                reverse=sort_by != "title",
            )

        return result

    def get_recently_watched_shows(self, username=None, limit=10):
        """Mock getting recently watched shows.

        Args:
            username: Filter for a specific user.
            limit: Maximum number of results to return.

        Returns:
            List of recently watched shows from our fixture data.
        """
        # Use username to avoid unused argument lint error
        _ = username
        # Record the call if a recorder is present
        if self.data_recorder:
            self.data_recorder.record_data("recently_watched_shows", self.recently_watched_shows)

        # Return limited number of items
        return self.recently_watched_shows[:limit]

    def get_recently_watched_movies(self, username=None, limit=10):
        """Mock getting recently watched movies.

        Args:
            username: Filter for a specific user.
            limit: Maximum number of results to return.

        Returns:
            List of recently watched movies from our fixture data.
        """
        # Use username to avoid unused argument lint error
        _ = username
        # Record the call if a recorder is present
        if self.data_recorder:
            self.data_recorder.record_data("recently_watched_movies", self.recently_watched_movies)

        # Return limited number of items
        return self.recently_watched_movies[:limit]

    def get_available_users(self):
        """Mock getting available users.

        Returns:
            List of mock users.
        """
        # Return some mock users
        return ["admin", "test_user"]


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for the CLI using mock Plex data."""

    @patch("plex_history_report.cli.PlexClient")
    def test_tv_basic_table(self, mock_plex_client_class):
        """Test the CLI with basic TV show statistics table."""
        # Set up mock PlexClient to return our mock client
        mock_plex_client_class.return_value = MockPlexClient()

        # Create a Rich Console that writes to a string buffer
        buffer = io.StringIO()
        console = Console(file=buffer, width=100, highlight=False)

        # Create a minimal config for testing
        mock_config = {"plex": {"base_url": "http://localhost:32400", "token": "test_token"}}

        # Create args for the CLI
        class MockArgs:
            tv = True
            movies = False
            config = None
            format = "table"
            show_recent = False
            create_config = False
            debug = False
            benchmark = False
            record = None
            user = None
            include_unwatched = False
            partially_watched_only = False
            list_users = False
            sort_by = "title"
            detailed = False

        args = MockArgs()

        # Run the CLI with our mocks
        with patch("plex_history_report.cli.Console", return_value=console), patch(
            "plex_history_report.cli.load_config", return_value=mock_config
        ):
            result = run(args)

        # Check that the command ran successfully
        self.assertEqual(result, 0)

        # Check output for expected content
        output = buffer.getvalue()
        self.assertIn("TV Show Statistics", output)

    @patch("plex_history_report.cli.PlexClient")
    def test_movies_basic_table(self, mock_plex_client_class):
        """Test the CLI with basic movie statistics table."""
        # Set up mock PlexClient to return our mock client
        mock_plex_client_class.return_value = MockPlexClient()

        # Create a Rich Console that writes to a string buffer
        buffer = io.StringIO()
        console = Console(file=buffer, width=100, highlight=False)

        # Create a minimal config for testing
        mock_config = {"plex": {"base_url": "http://localhost:32400", "token": "test_token"}}

        # Create args for the CLI
        class MockArgs:
            tv = False
            movies = True
            config = None
            format = "table"
            show_recent = False
            create_config = False
            debug = False
            benchmark = False
            record = None
            user = None
            include_unwatched = False
            partially_watched_only = False
            list_users = False
            sort_by = "title"
            detailed = False

        args = MockArgs()

        # Run the CLI with our mocks
        with patch("plex_history_report.cli.Console", return_value=console), patch(
            "plex_history_report.cli.load_config", return_value=mock_config
        ):
            result = run(args)

        # Check that the command ran successfully
        self.assertEqual(result, 0)

        # Check output for expected content
        output = buffer.getvalue()
        self.assertIn("Movie Statistics", output)

    @patch("plex_history_report.cli.PlexClient")
    def test_tv_show_recent(self, mock_plex_client_class):
        """Test the CLI with TV show statistics and recently watched shows."""
        # Set up mock PlexClient to return our mock client
        mock_plex_client_class.return_value = MockPlexClient()

        # Create a Rich Console that writes to a string buffer
        buffer = io.StringIO()
        console = Console(file=buffer, width=100, highlight=False)

        # Create a minimal config for testing
        mock_config = {"plex": {"base_url": "http://localhost:32400", "token": "test_token"}}

        # Create args for the CLI
        class MockArgs:
            tv = True
            movies = False
            config = None
            format = "table"
            show_recent = True
            create_config = False
            debug = False
            benchmark = False
            record = None
            user = None
            include_unwatched = False
            partially_watched_only = False
            list_users = False
            sort_by = "title"
            detailed = False

        args = MockArgs()

        # Run the CLI with our mocks
        with patch("plex_history_report.cli.Console", return_value=console), patch(
            "plex_history_report.cli.load_config", return_value=mock_config
        ):
            result = run(args)

        # Check that the command ran successfully
        self.assertEqual(result, 0)

        # Check output for expected content
        output = buffer.getvalue()
        self.assertIn("TV Show Statistics", output)
        self.assertIn("Recently Watched", output)


if __name__ == "__main__":
    unittest.main()
