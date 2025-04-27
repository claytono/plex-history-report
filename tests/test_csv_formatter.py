"""Tests for the CSV formatter module."""

import csv
import io
import unittest
from datetime import datetime

from plex_history_report.formatters import CsvFormatter


class TestCsvFormatter(unittest.TestCase):
    """Test the CSV formatter."""

    def setUp(self):
        """Set up test data for all tests."""
        self.formatter = CsvFormatter()

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
                "title": "Test Show 3, with comma",  # Title with comma to test CSV escaping
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
                "title": "Test Movie 3, with comma",  # Title with comma to test CSV escaping
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
                "title": "Recent Show 2, with comma",  # Title with comma to test CSV escaping
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
                "title": "Recent Movie 2, with comma",  # Title with comma to test CSV escaping
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
        self.assertEqual(result, "No TV shows found in your Plex library.")

    def test_format_show_statistics(self):
        """Test formatting show statistics."""
        result = self.formatter.format_show_statistics(self.show_data)

        # Parse the CSV to verify structure
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        # Check header row
        self.assertEqual(
            rows[0],
            [
                "Title",
                "Watched Episodes",
                "Total Episodes",
                "Completion Percentage",
                "Watch Time (minutes)",
                "Year",
                "Last Watched",
            ],
        )

        # Check that all shows are included
        self.assertEqual(rows[1][0], "Test Show 1")
        self.assertEqual(rows[2][0], "Test Show 2")
        self.assertEqual(rows[3][0], "Test Show 3, with comma")

        # Check proper escaping of comma in title
        self.assertIn("Test Show 3, with comma", result)

        # Check data formatting
        # Test Show 1
        self.assertEqual(rows[1][1], "5")  # watched episodes
        self.assertEqual(rows[1][2], "10")  # total episodes
        self.assertEqual(rows[1][3], "50.0")  # completion percentage
        self.assertEqual(rows[1][4], "150")  # watch time
        self.assertEqual(rows[1][5], "2020")  # year
        self.assertEqual(rows[1][6], "2023-04-01 12:00:00")  # last watched

        # Test Show 2
        self.assertEqual(rows[2][1], "0")  # watched episodes
        self.assertEqual(rows[2][2], "20")  # total episodes
        self.assertEqual(rows[2][3], "0.0")  # completion percentage
        self.assertEqual(rows[2][4], "0")  # watch time
        self.assertEqual(rows[2][5], "2021")  # year
        self.assertEqual(rows[2][6], "")  # last watched (None)

        # Test Show 3
        self.assertEqual(rows[3][1], "5")  # watched episodes
        self.assertEqual(rows[3][2], "5")  # total episodes
        self.assertEqual(rows[3][3], "100.0")  # completion percentage
        self.assertEqual(rows[3][4], "30")  # watch time
        self.assertEqual(rows[3][5], "2022")  # year
        self.assertEqual(rows[3][6], "2023-05-15 18:30:00")  # last watched

        # Check summary section
        self.assertIn("Summary", result)
        self.assertIn("Total Shows,3", result)
        self.assertIn("Watched Shows,2", result)
        self.assertIn("Total Episodes,35", result)
        self.assertIn("Watched Episodes,10", result)
        self.assertIn("Overall Completion,28.6%", result)
        self.assertIn("Total Watch Time (minutes),180", result)

    def test_format_movie_statistics_empty(self):
        """Test formatting empty movie statistics."""
        result = self.formatter.format_movie_statistics([])

        # Check that output contains the no movies found message
        self.assertEqual(result, "No movies found in your Plex library.")

    def test_format_movie_statistics(self):
        """Test formatting movie statistics."""
        result = self.formatter.format_movie_statistics(self.movie_data)

        # Parse the CSV to verify structure
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        # Check header row
        self.assertEqual(
            rows[0],
            [
                "Title",
                "Year",
                "Watch Count",
                "Last Watched",
                "Duration (minutes)",
                "Watched",
                "Rating",
            ],
        )

        # Check that all movies are included
        self.assertEqual(rows[1][0], "Test Movie 1")
        self.assertEqual(rows[2][0], "Test Movie 2")
        self.assertEqual(rows[3][0], "Test Movie 3, with comma")

        # Check proper escaping of comma in title
        self.assertIn("Test Movie 3, with comma", result)

        # Check data formatting
        # Test Movie 1
        self.assertEqual(rows[1][1], "2020")  # year
        self.assertEqual(rows[1][2], "2")  # watch count
        self.assertEqual(rows[1][3], "2023-04-01 12:00:00")  # last watched
        self.assertEqual(rows[1][4], "120")  # duration
        self.assertEqual(rows[1][5], "Yes")  # watched
        self.assertEqual(rows[1][6], "8.5")  # rating

        # Test Movie 2
        self.assertEqual(rows[2][1], "2021")  # year
        self.assertEqual(rows[2][2], "0")  # watch count
        self.assertEqual(rows[2][3], "")  # last watched (None)
        self.assertEqual(rows[2][4], "90")  # duration
        self.assertEqual(rows[2][5], "No")  # watched
        self.assertEqual(rows[2][6], "")  # rating (None)

        # Test Movie 3
        self.assertEqual(rows[3][1], "2022")  # year
        self.assertEqual(rows[3][2], "3")  # watch count
        self.assertTrue(rows[3][3])  # last watched (timestamp converted)
        self.assertEqual(rows[3][4], "45")  # duration
        self.assertEqual(rows[3][5], "Yes")  # watched
        self.assertEqual(rows[3][6], "9.2")  # rating

        # Check summary section
        self.assertIn("Summary", result)
        self.assertIn("Total Movies,3", result)
        self.assertIn("Watched Movies,2", result)
        self.assertIn("Completion,66.7%", result)
        self.assertIn("Total Watch Count,5", result)
        self.assertIn("Total Duration (minutes),255", result)
        self.assertIn("Total Watch Time (minutes),375", result)

    def test_format_recently_watched_shows_empty(self):
        """Test formatting empty recently watched shows."""
        result = self.formatter.format_recently_watched([], media_type="show")

        # Check that output contains the no recently watched shows message
        self.assertEqual(result, "No recently watched shows found.")

    def test_format_recently_watched_shows(self):
        """Test formatting recently watched shows."""
        result = self.formatter.format_recently_watched(
            self.recently_watched_shows, media_type="show"
        )

        # Parse the CSV to verify structure
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        # Check header row
        self.assertEqual(
            rows[0],
            [
                "Title",
                "Last Watched",
                "Watched Episodes",
                "Total Episodes",
                "Completion Percentage",
                "Watch Time (minutes)",
            ],
        )

        # Check that all shows are included
        self.assertEqual(rows[1][0], "Recent Show 1")
        self.assertEqual(rows[2][0], "Recent Show 2, with comma")

        # Check proper escaping of comma in title
        self.assertIn("Recent Show 2, with comma", result)

        # Check data formatting
        # Recent Show 1
        self.assertEqual(rows[1][1], "2023-05-15 21:00:00")  # last watched
        self.assertEqual(rows[1][2], "6")  # watched episodes
        self.assertEqual(rows[1][3], "10")  # total episodes
        self.assertEqual(rows[1][4], "60.0")  # completion percentage
        self.assertEqual(rows[1][5], "180")  # watch time

        # Recent Show 2
        self.assertTrue(rows[2][1])  # last watched (timestamp converted)
        self.assertEqual(rows[2][2], "2")  # watched episodes
        self.assertEqual(rows[2][3], "8")  # total episodes
        self.assertEqual(rows[2][4], "25.0")  # completion percentage
        self.assertEqual(rows[2][5], "60")  # watch time

    def test_format_recently_watched_movies_empty(self):
        """Test formatting empty recently watched movies."""
        result = self.formatter.format_recently_watched([], media_type="movie")

        # Check that output contains the no recently watched movies message
        self.assertEqual(result, "No recently watched movies found.")

    def test_format_recently_watched_movies(self):
        """Test formatting recently watched movies."""
        result = self.formatter.format_recently_watched(
            self.recently_watched_movies, media_type="movie"
        )

        # Parse the CSV to verify structure
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        # Check header row
        self.assertEqual(
            rows[0],
            [
                "Title",
                "Last Watched",
                "Watch Count",
                "Duration (minutes)",
            ],
        )

        # Check that all movies are included
        self.assertEqual(rows[1][0], "Recent Movie 1")
        self.assertEqual(rows[2][0], "Recent Movie 2, with comma")

        # Check proper escaping of comma in title
        self.assertIn("Recent Movie 2, with comma", result)

        # Check data formatting
        # Recent Movie 1
        self.assertEqual(rows[1][1], "2023-05-15 20:00:00")  # last watched
        self.assertEqual(rows[1][2], "1")  # watch count
        self.assertEqual(rows[1][3], "110")  # duration

        # Recent Movie 2
        self.assertTrue(rows[2][1])  # last watched (timestamp converted)
        self.assertEqual(rows[2][2], "2")  # watch count
        self.assertEqual(rows[2][3], "95")  # duration

    def test_csv_row_handling(self):
        """Test edge cases in CSV row handling."""
        # Create a show with special characters that might need escaping in CSV
        special_chars_show = {
            "title": 'Show with "quotes" and, commas',
            "total_episodes": 10,
            "watched_episodes": 5,
            "completion_percentage": 50.0,
            "total_watch_time_minutes": 150,
            "last_watched": datetime(2023, 4, 1, 12, 0, 0),
            "year": 2020,
        }

        result = self.formatter.format_show_statistics([special_chars_show])

        # Verify the CSV can be parsed correctly
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        # Check the title was escaped properly
        self.assertEqual(rows[1][0], 'Show with "quotes" and, commas')


if __name__ == "__main__":
    unittest.main()
