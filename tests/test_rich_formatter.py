"""Tests for the Rich formatter module."""

import unittest
from datetime import datetime

from plex_history_report.formatters import RichFormatter


class TestRichFormatter(unittest.TestCase):
    """Test the Rich formatter."""

    def setUp(self):
        """Set up test data for all tests."""
        self.formatter = RichFormatter()

        # Sample show data
        self.show_data = [
            {
                "title": "Test Show 1",
                "total_episodes": 10,
                "watched_episodes": 5,
                "completion_percentage": 50.0,
                "total_watch_time_minutes": 150,
                "last_watched": datetime(2023, 4, 1, 12, 0, 0),
                "year": 2020,
            },
            {
                "title": "Test Show 2",
                "total_episodes": 20,
                "watched_episodes": 0,
                "completion_percentage": 0.0,
                "total_watch_time_minutes": 0,
                "last_watched": None,
                "year": 2021,
            },
            {
                "title": "Test Show 3",
                "total_episodes": 5,
                "watched_episodes": 5,
                "completion_percentage": 100.0,
                "total_watch_time_minutes": 30,
                "last_watched": datetime(2023, 5, 15, 18, 30, 0),
                "year": 2022,
            },
        ]

        # Sample movie data
        self.movie_data = [
            {
                "title": "Test Movie 1",
                "watch_count": 2,
                "last_watched": datetime(2023, 4, 1, 12, 0, 0),
                "duration_minutes": 120,
                "watched": True,
                "rating": 8.5,
                "year": 2020,
            },
            {
                "title": "Test Movie 2",
                "watch_count": 0,
                "last_watched": None,
                "duration_minutes": 90,
                "watched": False,
                "rating": None,
                "year": 2021,
            },
            {
                "title": "Test Movie 3",
                "watch_count": 3,
                "last_watched": 1683021600,  # Unix timestamp: 2023-05-02
                "duration_minutes": 45,
                "watched": True,
                "rating": 9.2,
                "year": 2022,
            },
        ]

        # Sample recently watched data for shows
        self.recently_watched_shows = [
            {
                "title": "Recent Show 1",
                "total_episodes": 10,
                "watched_episodes": 6,
                "completion_percentage": 60.0,
                "total_watch_time_minutes": 180,
                "last_watched": datetime(2023, 5, 15, 21, 0, 0),
            },
            {
                "title": "Recent Show 2",
                "total_episodes": 8,
                "watched_episodes": 2,
                "completion_percentage": 25.0,
                "total_watch_time_minutes": 60,
                "last_watched": 1683108000,  # Unix timestamp: 2023-05-03
            },
        ]

        # Sample recently watched data for movies
        self.recently_watched_movies = [
            {
                "title": "Recent Movie 1",
                "watch_count": 1,
                "last_watched": datetime(2023, 5, 15, 20, 0, 0),
                "duration_minutes": 110,
                "watched": True,
            },
            {
                "title": "Recent Movie 2",
                "watch_count": 2,
                "last_watched": 1683194400,  # Unix timestamp: 2023-05-04
                "duration_minutes": 95,
                "watched": True,
            },
        ]

    def test_format_show_statistics_empty(self):
        """Test formatting empty show statistics."""
        result = self.formatter.format_show_statistics([])

        # Check that output contains the no shows found message
        self.assertIn("No TV shows found in your Plex library", result)
        self.assertIn("TV Show Statistics", result)

    def test_format_show_statistics(self):
        """Test formatting show statistics."""
        result = self.formatter.format_show_statistics(self.show_data)

        # Check that output contains all show titles
        self.assertIn("Test Show 1", result)
        self.assertIn("Test Show 2", result)
        self.assertIn("Test Show 3", result)

        # Check that completion percentages are formatted correctly
        self.assertIn("50.0%", result)
        self.assertIn("0.0%", result)
        self.assertIn("100.0%", result)

        # Check watch time formatting
        self.assertIn("2h 30m", result)  # 150 minutes for Test Show 1
        self.assertIn("0m", result)  # 0 minutes for Test Show 2
        self.assertIn("30m", result)  # 30 minutes for Test Show 3

    def test_format_show_statistics_contains_summary(self):
        """Test that show statistics output includes summary information."""
        result = self.formatter.format_show_statistics(self.show_data)

        # Check that output contains the summary title
        self.assertIn("TV Show Summary", result)

        # Check that summary statistics are correct
        self.assertIn("Total Shows: 3", result)
        self.assertIn("Watched Shows: 2", result)  # Test Show 2 has 0 watched episodes
        self.assertIn("Total Episodes: 35", result)  # 10 + 20 + 5 = 35
        self.assertIn("Watched Episodes: 10", result)  # 5 + 0 + 5 = 10
        self.assertIn("Overall Completion: 28.6%", result)  # 10/35 = 28.6%
        self.assertIn("Total Watch Time: 3 hours, 0 minutes", result)  # 150 + 0 + 30 = 180 minutes

    def test_format_movie_statistics_empty(self):
        """Test formatting empty movie statistics."""
        result = self.formatter.format_movie_statistics([])

        # Check that output contains the no movies found message
        self.assertIn("No movies found in your Plex library", result)
        self.assertIn("Movie Statistics", result)

    def test_format_movie_statistics(self):
        """Test formatting movie statistics."""
        result = self.formatter.format_movie_statistics(self.movie_data)

        # Check that output contains all movie titles
        self.assertIn("Test Movie 1", result)
        self.assertIn("Test Movie 2", result)
        self.assertIn("Test Movie 3", result)

        # Check watch count formatting
        self.assertIn("2", result)  # Test Movie 1 watch count
        self.assertIn("0", result)  # Test Movie 2 watch count
        self.assertIn("3", result)  # Test Movie 3 watch count

        # Check date formatting (only checking one date as example)
        self.assertIn("2023-04-01", result)  # Test Movie 1 watch date
        self.assertIn("2023-05-02", result)  # Test Movie 3 watch date (from unix timestamp)

        # Check duration formatting
        self.assertIn("2h 0m", result)  # 120 minutes for Test Movie 1
        self.assertIn("1h 30m", result)  # 90 minutes for Test Movie 2
        self.assertIn("45m", result)  # 45 minutes for Test Movie 3

        # Check rating formatting
        self.assertIn("8.5", result)  # Test Movie 1 rating
        self.assertIn("-", result)  # No rating for Test Movie 2
        self.assertIn("9.2", result)  # Test Movie 3 rating

    def test_format_movie_statistics_contains_summary(self):
        """Test that movie statistics output includes summary information."""
        result = self.formatter.format_movie_statistics(self.movie_data)

        # Check that output contains the summary title
        self.assertIn("Movie Summary", result)

        # Check that summary statistics are correct
        self.assertIn("Total Movies: 3", result)
        self.assertIn("Watched Movies: 2", result)  # Test Movie 2 has watched=False
        self.assertIn("Completion: 66.7%", result)  # 2/3 = 66.7%
        self.assertIn("Total Watch Count: 5", result)  # 2 + 0 + 3 = 5
        self.assertIn("Total Duration: 4 hours, 15 minutes", result)  # 120 + 90 + 45 = 255 minutes

        # Check watched duration calculation (watched movies only)
        # Test Movie 1: 120 minutes x 2 watches = 240 minutes
        # Test Movie 3: 45 minutes x 3 watches = 135 minutes
        # Total: 375 minutes = 6 hours 15 minutes
        self.assertIn("Total Watch Time: 6 hours, 15 minutes", result)

    def test_format_recently_watched_shows_empty(self):
        """Test formatting empty recently watched shows."""
        result = self.formatter.format_recently_watched([], media_type="show")

        # Check that output contains the no recently watched shows message
        self.assertIn("No recently watched shows found", result)
        self.assertIn("Recently Watched Shows", result)

    def test_format_recently_watched_shows(self):
        """Test formatting recently watched shows."""
        result = self.formatter.format_recently_watched(
            self.recently_watched_shows, media_type="show"
        )

        # Check that output contains all show titles
        self.assertIn("Recent Show 1", result)
        self.assertIn("Recent Show 2", result)

        # Check last watched date formatting
        self.assertIn("2023-05-15 21:00", result)  # Recent Show 1
        self.assertIn("2023-05-03", result)  # Recent Show 2 (from unix timestamp)

        # Check progress formatting
        self.assertIn("6/10", result)  # Recent Show 1 progress
        self.assertIn("60.0%", result)  # Recent Show 1 percentage
        self.assertIn("2/8", result)  # Recent Show 2 progress
        self.assertIn("25.0%", result)  # Recent Show 2 percentage

        # Check watch time formatting
        self.assertIn("3h 0m", result)  # 180 minutes for Recent Show 1
        self.assertIn("1h 0m", result)  # 60 minutes for Recent Show 2

    def test_format_recently_watched_movies_empty(self):
        """Test formatting empty recently watched movies."""
        result = self.formatter.format_recently_watched([], media_type="movie")

        # Check that output contains the no recently watched movies message
        self.assertIn("No recently watched movies found", result)
        self.assertIn("Recently Watched Movies", result)

    def test_format_recently_watched_movies(self):
        """Test formatting recently watched movies."""
        result = self.formatter.format_recently_watched(
            self.recently_watched_movies, media_type="movie"
        )

        # Check that output contains all movie titles
        self.assertIn("Recent Movie 1", result)
        self.assertIn("Recent Movie 2", result)

        # Check last watched date formatting
        self.assertIn("2023-05-15 20:00", result)  # Recent Movie 1
        self.assertIn("2023-05-04", result)  # Recent Movie 2 (from unix timestamp)

        # Check watch count formatting
        self.assertIn("1", result)  # Recent Movie 1 watch count
        self.assertIn("2", result)  # Recent Movie 2 watch count

        # Check duration formatting
        self.assertIn("1h 50m", result)  # 110 minutes for Recent Movie 1
        self.assertIn("1h 35m", result)  # 95 minutes for Recent Movie 2

    def test_rich_console_output(self):
        """Test that rich console output works properly."""
        # After examining the code, we know the RichFormatter uses StringIO
        # for capturing console output in format_show_statistics, so we don't need
        # to mock the console directly. Instead, we'll verify the output string contains
        # expected rich formatting codes.

        result = self.formatter.format_show_statistics(self.show_data)

        # Verify it's a non-empty string
        self.assertTrue(isinstance(result, str))
        self.assertTrue(len(result) > 0)

        # Looking for table boundaries or rich formatting codes (simplified)
        self.assertTrue("TV Show Statistics" in result)

        # Make sure all expected column names are in the output
        self.assertTrue("Title" in result)
        self.assertTrue("Watched" in result)
        self.assertTrue("Total" in result)
        self.assertTrue("Completion" in result)
        self.assertTrue("Watch Time" in result)


if __name__ == "__main__":
    unittest.main()
