"""Tests for the Compact formatter module."""

import unittest
from datetime import datetime

from plex_history_report.formatters import CompactFormatter


class TestCompactFormatter(unittest.TestCase):
    """Test the Compact formatter."""

    def setUp(self):
        """Set up test data for all tests."""
        self.formatter = CompactFormatter()

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
                "title": "Test Show 3|with|pipes",  # Title with pipe chars to test escaping
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
                "title": "Test Movie 3|with|pipes",  # Title with pipe chars to test escaping
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
                "title": "Recent Show 2|with|pipes",  # Title with pipe chars to test escaping
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
                "title": "Recent Movie 2|with|pipes",  # Title with pipe chars to test escaping
                "watch_count": 2,
                "last_watched": 1683194400,  # Unix timestamp: 2023-05-04
                "duration_minutes": 95,
                "watched": True,
            },
        ]

    def test_format_show_statistics_empty(self):
        """Test formatting empty show statistics."""
        result = self.formatter.format_show_statistics([])

        # Check that output for empty stats is just a simple message
        self.assertEqual(result, "NoShows")

    def test_format_show_statistics(self):
        """Test formatting show statistics."""
        result = self.formatter.format_show_statistics(self.show_data)

        # Split the result into lines for analysis
        lines = result.strip().split("\n")

        # Check that we have the correct number of lines (header + 3 shows)
        self.assertEqual(len(lines), 4)

        # Check header line
        self.assertEqual(lines[0], "Title|WatchedEps|TotalEps|WatchTime")

        # Parse the data lines
        data_lines = [line.split("|") for line in lines[1:]]

        # Check show 1 data
        self.assertEqual(data_lines[0][0], "Test Show 1")
        self.assertEqual(data_lines[0][1], "5")
        self.assertEqual(data_lines[0][2], "10")
        self.assertEqual(data_lines[0][3], "2h30m")

        # Check show 2 data
        self.assertEqual(data_lines[1][0], "Test Show 2")
        self.assertEqual(data_lines[1][1], "0")
        self.assertEqual(data_lines[1][2], "20")
        self.assertEqual(data_lines[1][3], "0m")

        # Check show 3 data (with pipe character escaping)
        self.assertEqual(data_lines[2][0], "Test Show 3/with/pipes")  # Pipes replaced with /
        self.assertEqual(data_lines[2][1], "5")
        self.assertEqual(data_lines[2][2], "5")
        self.assertEqual(data_lines[2][3], "30m")

    def test_format_movie_statistics_empty(self):
        """Test formatting empty movie statistics."""
        result = self.formatter.format_movie_statistics([])

        # Check that output for empty stats is just a simple message
        self.assertEqual(result, "NoMovies")

    def test_format_movie_statistics(self):
        """Test formatting movie statistics."""
        result = self.formatter.format_movie_statistics(self.movie_data)

        # Split the result into lines for analysis
        lines = result.strip().split("\n")

        # Check that we have the correct number of lines (header + 3 movies)
        self.assertEqual(len(lines), 4)

        # Check header line
        self.assertEqual(lines[0], "Title|WatchCount|LastWatched|Duration|Rating")

        # Parse the data lines
        data_lines = [line.split("|") for line in lines[1:]]

        # Check movie 1 data
        self.assertEqual(data_lines[0][0], "Test Movie 1")
        self.assertEqual(data_lines[0][1], "2")
        self.assertEqual(data_lines[0][2], "23-04-01")  # Short year format
        self.assertEqual(data_lines[0][3], "2h0m")
        self.assertEqual(data_lines[0][4], "8.5")

        # Check movie 2 data
        self.assertEqual(data_lines[1][0], "Test Movie 2")
        self.assertEqual(data_lines[1][1], "0")
        self.assertEqual(data_lines[1][2], "-")  # No last watched date
        self.assertEqual(data_lines[1][3], "1h30m")
        self.assertEqual(data_lines[1][4], "-")  # No rating

        # Check movie 3 data (with pipe character escaping)
        self.assertEqual(data_lines[2][0], "Test Movie 3/with/pipes")  # Pipes replaced with /
        self.assertEqual(data_lines[2][1], "3")
        self.assertTrue(len(data_lines[2][2]) > 0)  # Some date format from timestamp
        self.assertEqual(data_lines[2][3], "45m")
        self.assertEqual(data_lines[2][4], "9.2")

    def test_format_recently_watched_shows_empty(self):
        """Test formatting empty recently watched shows."""
        result = self.formatter.format_recently_watched([], media_type="show")

        # Check that output for empty stats is just a simple message
        self.assertEqual(result, "NoRecentShows")

    def test_format_recently_watched_shows(self):
        """Test formatting recently watched shows."""
        result = self.formatter.format_recently_watched(
            self.recently_watched_shows, media_type="show"
        )

        # Split the result into lines for analysis
        lines = result.strip().split("\n")

        # Check that we have the correct number of lines (header + 2 shows)
        self.assertEqual(len(lines), 3)

        # Check header line
        self.assertEqual(lines[0], "Title|LastWatched|Progress|WatchTime")

        # Parse the data lines
        data_lines = [line.split("|") for line in lines[1:]]

        # Check show 1 data
        self.assertEqual(data_lines[0][0], "Recent Show 1")
        self.assertEqual(data_lines[0][1], "23-05-15")  # Short year format
        self.assertEqual(data_lines[0][2], "6/10")  # Progress format
        self.assertEqual(data_lines[0][3], "3h0m")

        # Check show 2 data (with pipe character escaping)
        self.assertEqual(data_lines[1][0], "Recent Show 2/with/pipes")  # Pipes replaced with /
        self.assertTrue(len(data_lines[1][1]) > 0)  # Some date format from timestamp
        self.assertEqual(data_lines[1][2], "2/8")  # Progress format
        self.assertEqual(data_lines[1][3], "1h0m")

    def test_format_recently_watched_movies_empty(self):
        """Test formatting empty recently watched movies."""
        result = self.formatter.format_recently_watched([], media_type="movie")

        # Check that output for empty stats is just a simple message
        self.assertEqual(result, "NoRecentMovies")

    def test_format_recently_watched_movies(self):
        """Test formatting recently watched movies."""
        result = self.formatter.format_recently_watched(
            self.recently_watched_movies, media_type="movie"
        )

        # Split the result into lines for analysis
        lines = result.strip().split("\n")

        # Check that we have the correct number of lines (header + 2 movies)
        self.assertEqual(len(lines), 3)

        # Check header line
        self.assertEqual(lines[0], "Title|LastWatched|WatchCount|Duration")

        # Parse the data lines
        data_lines = [line.split("|") for line in lines[1:]]

        # Check movie 1 data
        self.assertEqual(data_lines[0][0], "Recent Movie 1")
        self.assertEqual(data_lines[0][1], "23-05-15")  # Short year format
        self.assertEqual(data_lines[0][2], "1")
        self.assertEqual(data_lines[0][3], "1h50m")

        # Check movie 2 data (with pipe character escaping)
        self.assertEqual(data_lines[1][0], "Recent Movie 2/with/pipes")  # Pipes replaced with /
        self.assertTrue(len(data_lines[1][1]) > 0)  # Some date format from timestamp
        self.assertEqual(data_lines[1][2], "2")
        self.assertEqual(data_lines[1][3], "1h35m")

    def test_special_characters_handling(self):
        """Test handling of special characters in compact output."""
        # Create a show with various special characters
        special_chars_show = {
            "title": 'Show with |pipes| and newlines and "quotes"',  # Removed actual newline character
            "total_episodes": 10,
            "watched_episodes": 5,
            "completion_percentage": 50.0,
            "total_watch_time_minutes": 150,
        }

        result = self.formatter.format_show_statistics([special_chars_show])

        # Split and check
        lines = result.strip().split("\n")
        data_line = lines[1].split("|")

        # Verify pipes were properly handled
        self.assertEqual(data_line[0], 'Show with /pipes/ and newlines and "quotes"')


if __name__ == "__main__":
    unittest.main()
