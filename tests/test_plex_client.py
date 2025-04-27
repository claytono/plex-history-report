"""Tests for the plex_client module."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, PropertyMock, patch

from plexapi.exceptions import Unauthorized
from plexapi.library import LibrarySection
from plexapi.server import PlexServer
from plexapi.video import Movie, Show

from plex_history_report.plex_client import PlexClient, PlexClientError


class TestPlexClient(unittest.TestCase):
    """Test the PlexClient class."""

    def setUp(self):
        """Set up common test fixtures."""
        self.base_url = "http://localhost:32400"
        self.token = "test_token"

        # Create mock for PlexServer
        self.mock_server = MagicMock(spec=PlexServer)
        self.mock_server.friendlyName = "Test Plex Server"

        # Set up the patch for PlexServer
        self.plex_server_patcher = patch(
            "plex_history_report.plex_client.PlexServer", return_value=self.mock_server
        )
        self.mock_plex_server = self.plex_server_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.plex_server_patcher.stop()

    def test_init_successful(self):
        """Test successful initialization of PlexClient."""
        client = PlexClient(self.base_url, self.token)
        self.assertEqual(client.base_url, self.base_url)
        self.assertEqual(client.token, self.token)
        self.assertEqual(client.server, self.mock_server)
        self.mock_plex_server.assert_called_once_with(self.base_url, self.token)

    def test_init_failure(self):
        """Test that initialization failure raises a PlexClientError."""
        self.mock_plex_server.side_effect = Exception("Connection failed")
        with self.assertRaises(PlexClientError) as context:
            PlexClient(self.base_url, self.token)
        self.assertIn("Failed to connect to Plex server", str(context.exception))

    def test_get_available_users_success(self):
        """Test successful retrieval of available users."""
        # Create mock users
        mock_user1 = MagicMock()
        mock_user1.username = "user1"
        mock_user2 = MagicMock()
        mock_user2.username = "user2"

        # Create mock account and set up users
        mock_account = MagicMock()
        mock_account.users.return_value = [mock_user1, mock_user2]
        self.mock_server.myPlexAccount.return_value = mock_account

        # Create the client and test
        client = PlexClient(self.base_url, self.token)
        users = client.get_available_users()

        # Check if the users list contains both admin and shared users
        self.assertEqual(len(users), 3)
        self.assertIn("admin", users)
        self.assertIn("user1", users)
        self.assertIn("user2", users)

    def test_get_available_users_unauthorized(self):
        """Test user retrieval when unauthorized to access myPlex account."""
        # Set up the server mock to raise Unauthorized for myPlexAccount
        self.mock_server.myPlexAccount.side_effect = Unauthorized("Unauthorized")

        client = PlexClient(self.base_url, self.token)
        users = client.get_available_users()

        # Should still return admin user even when unauthorized
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0], "admin")

    def test_get_available_users_exception(self):
        """Test user retrieval with general exception."""
        # Set up the server mock to raise an exception
        self.mock_server.myPlexAccount.side_effect = Exception("Unknown error")

        client = PlexClient(self.base_url, self.token)
        users = client.get_available_users()

        # Should return empty list on general exception
        self.assertEqual(users, [])

    def test_get_library_sections(self):
        """Test retrieving library sections."""
        # Create mock sections
        mock_section1 = MagicMock(spec=LibrarySection)
        mock_section1.title = "Movies"
        mock_section1.type = "movie"

        mock_section2 = MagicMock(spec=LibrarySection)
        mock_section2.title = "TV Shows"
        mock_section2.type = "show"

        # Set up server mock to return sections
        mock_library = MagicMock()
        mock_library.sections.return_value = [mock_section1, mock_section2]
        self.mock_server.library = mock_library

        client = PlexClient(self.base_url, self.token)
        sections = client.get_library_sections()

        # Check if sections match the mock sections
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections, [mock_section1, mock_section2])


class TestPlexClientShowStatistics(unittest.TestCase):
    """Test the show statistics functionality of PlexClient."""

    def setUp(self):
        """Set up common test fixtures."""
        self.base_url = "http://localhost:32400"
        self.token = "test_token"

        # Create mock for PlexServer and library
        self.mock_server = MagicMock(spec=PlexServer)
        # Add friendlyName attribute to prevent AttributeError
        self.mock_server.friendlyName = "Test Plex Server"
        self.mock_library = MagicMock()
        self.mock_server.library = self.mock_library

        # Set up the patch for PlexServer
        self.plex_server_patcher = patch(
            "plex_history_report.plex_client.PlexServer", return_value=self.mock_server
        )
        self.mock_plex_server = self.plex_server_patcher.start()

        # Create some mock shows and episodes
        self.setup_mock_shows()

    def setup_mock_shows(self):
        """Set up mock show and episode objects for testing."""
        # Create mock TV section
        self.mock_tv_section = MagicMock(spec=LibrarySection)
        self.mock_tv_section.type = "show"
        self.mock_tv_section.title = "TV Shows"

        # Mock library sections to return TV section
        self.mock_library.sections.return_value = [self.mock_tv_section]

        # Create mock shows
        self.mock_show1 = MagicMock(spec=Show)
        self.mock_show1.title = "Show 1"
        self.mock_show1.year = 2020
        self.mock_show1.rating = 8.5
        self.mock_show1.key = "/library/metadata/1"

        self.mock_show2 = MagicMock(spec=Show)
        self.mock_show2.title = "Show 2"
        self.mock_show2.year = 2021
        self.mock_show2.rating = 9.0
        self.mock_show2.key = "/library/metadata/2"

        # Mock TV section to return shows
        self.mock_tv_section.all.return_value = [self.mock_show1, self.mock_show2]

        # Create mock episodes for Show 1
        self.mock_episode1 = MagicMock()
        self.mock_episode1.title = "Episode 1"
        self.mock_episode1.isWatched = True
        self.mock_episode1.duration = 30 * 60 * 1000  # 30 minutes in ms

        self.mock_episode2 = MagicMock()
        self.mock_episode2.title = "Episode 2"
        self.mock_episode2.isWatched = False
        self.mock_episode2.duration = 30 * 60 * 1000

        # Create mock episodes for Show 2
        self.mock_episode3 = MagicMock()
        self.mock_episode3.title = "Episode 3"
        self.mock_episode3.isWatched = True
        self.mock_episode3.duration = 45 * 60 * 1000  # 45 minutes in ms

        self.mock_episode4 = MagicMock()
        self.mock_episode4.title = "Episode 4"
        self.mock_episode4.isWatched = True
        self.mock_episode4.duration = 45 * 60 * 1000

        # Mock history entries
        self.mock_history_entry1 = MagicMock()
        self.mock_history_entry1.viewedAt = datetime(2023, 1, 1, 12, 0, 0)

        self.mock_history_entry2 = MagicMock()
        self.mock_history_entry2.viewedAt = datetime(2023, 1, 2, 12, 0, 0)

        # Configure episodes to return history
        self.mock_episode1.history.return_value = [self.mock_history_entry1]
        self.mock_episode2.history.return_value = []
        self.mock_episode3.history.return_value = [self.mock_history_entry2]
        self.mock_episode4.history.return_value = [self.mock_history_entry1]

        # Mock shows to return episodes
        self.mock_show1.episodes.return_value = [self.mock_episode1, self.mock_episode2]
        self.mock_show2.episodes.return_value = [self.mock_episode3, self.mock_episode4]

    def tearDown(self):
        """Clean up after tests."""
        self.plex_server_patcher.stop()

    def test_get_all_show_statistics_basic(self):
        """Test basic functionality of get_all_show_statistics."""
        client = PlexClient(self.base_url, self.token)

        # Call the method
        stats = client.get_all_show_statistics()

        # Verify we got stats for both shows
        self.assertEqual(len(stats), 2)

        # Verify stats for Show 1
        show1_stat = next(stat for stat in stats if stat["title"] == "Show 1")
        self.assertEqual(show1_stat["total_episodes"], 2)
        self.assertEqual(show1_stat["watched_episodes"], 1)
        self.assertEqual(show1_stat["unwatched_episodes"], 1)
        self.assertEqual(show1_stat["completion_percentage"], 50.0)
        self.assertEqual(show1_stat["year"], 2020)
        self.assertEqual(show1_stat["rating"], 8.5)

        # Verify stats for Show 2
        show2_stat = next(stat for stat in stats if stat["title"] == "Show 2")
        self.assertEqual(show2_stat["total_episodes"], 2)
        self.assertEqual(show2_stat["watched_episodes"], 2)
        self.assertEqual(show2_stat["unwatched_episodes"], 0)
        self.assertEqual(show2_stat["completion_percentage"], 100.0)
        self.assertEqual(show2_stat["year"], 2021)
        self.assertEqual(show2_stat["rating"], 9.0)

    def test_get_all_show_statistics_no_tv_sections(self):
        """Test get_all_show_statistics with no TV sections."""
        # Mock library sections to return no TV sections
        self.mock_library.sections.return_value = []

        client = PlexClient(self.base_url, self.token)
        stats = client.get_all_show_statistics()

        # Should return empty list with no TV sections
        self.assertEqual(stats, [])

    def test_get_show_statistics_with_username(self):
        """Test retrieving show statistics for a specific user."""
        # Set up episode history for a specific user
        self.mock_episode1.history.side_effect = lambda username=None: (
            [self.mock_history_entry1] if username == "testuser" else []
        )
        self.mock_episode2.history.return_value = []
        self.mock_episode3.history.side_effect = lambda username=None: (
            [self.mock_history_entry2] if username == "testuser" else []
        )
        self.mock_episode4.history.return_value = []

        client = PlexClient(self.base_url, self.token)
        stats = client.get_all_show_statistics(username="testuser")

        # Verify stats for shows with the specific user
        self.assertEqual(len(stats), 2)

        # Verify stats for Show 1
        show1_stat = next(stat for stat in stats if stat["title"] == "Show 1")
        self.assertEqual(show1_stat["watched_episodes"], 1)
        self.assertEqual(show1_stat["completion_percentage"], 50.0)

        # Verify stats for Show 2
        show2_stat = next(stat for stat in stats if stat["title"] == "Show 2")
        self.assertEqual(show2_stat["watched_episodes"], 1)
        self.assertEqual(show2_stat["completion_percentage"], 50.0)

    def test_get_show_statistics_include_unwatched(self):
        """Test retrieving show statistics including unwatched shows."""
        # Create a completely unwatched show
        mock_unwatched_show = MagicMock(spec=Show)
        mock_unwatched_show.title = "Unwatched Show"
        mock_unwatched_show.year = 2022
        mock_unwatched_show.rating = 7.5
        mock_unwatched_show.key = "/library/metadata/3"

        # Mock library sections to return TV section
        self.mock_library.sections.return_value = [self.mock_tv_section]

        # Create unwatched episodes
        mock_unwatched_episode = MagicMock()
        mock_unwatched_episode.title = "Unwatched Episode"
        mock_unwatched_episode.isWatched = False
        mock_unwatched_episode.duration = 30 * 60 * 1000
        mock_unwatched_episode.history.return_value = []

        # Configure unwatched show to return episodes
        mock_unwatched_show.episodes.return_value = [mock_unwatched_episode]

        # Update the shows returned by the TV section
        self.mock_tv_section.all.return_value = [
            self.mock_show1,
            self.mock_show2,
            mock_unwatched_show,
        ]

        client = PlexClient(self.base_url, self.token)

        # Test without include_unwatched (default)
        stats_default = client.get_all_show_statistics()
        # Should only include shows with watched episodes
        self.assertEqual(len(stats_default), 2)
        self.assertNotIn("Unwatched Show", [s["title"] for s in stats_default])

        # Test with include_unwatched=True
        stats_with_unwatched = client.get_all_show_statistics(include_unwatched=True)
        # Should include all shows
        self.assertEqual(len(stats_with_unwatched), 3)
        self.assertIn("Unwatched Show", [s["title"] for s in stats_with_unwatched])

        # Verify stats for unwatched show
        unwatched_stat = next(s for s in stats_with_unwatched if s["title"] == "Unwatched Show")
        self.assertEqual(unwatched_stat["watched_episodes"], 0)
        self.assertEqual(unwatched_stat["completion_percentage"], 0.0)

    def test_get_show_statistics_partially_watched_only(self):
        """Test retrieving only partially watched shows."""
        client = PlexClient(self.base_url, self.token)

        # Show 1 is partially watched (1 of 2 episodes), Show 2 is fully watched
        stats = client.get_all_show_statistics(partially_watched_only=True)

        # Should only include partially watched shows
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]["title"], "Show 1")
        self.assertEqual(stats[0]["completion_percentage"], 50.0)

    def test_get_show_statistics_sorting(self):
        """Test sorting options for show statistics."""
        client = PlexClient(self.base_url, self.token)

        # Test sort by title (default)
        stats_by_title = client.get_all_show_statistics(sort_by="title")
        self.assertEqual(stats_by_title[0]["title"], "Show 1")
        self.assertEqual(stats_by_title[1]["title"], "Show 2")

        # Test sort by watched_episodes
        stats_by_watched = client.get_all_show_statistics(sort_by="watched_episodes")
        self.assertEqual(stats_by_watched[0]["title"], "Show 2")
        self.assertEqual(stats_by_watched[1]["title"], "Show 1")

        # Test sort by completion_percentage
        stats_by_completion = client.get_all_show_statistics(sort_by="completion_percentage")
        self.assertEqual(stats_by_completion[0]["title"], "Show 2")
        self.assertEqual(stats_by_completion[1]["title"], "Show 1")

        # Test sort by year
        stats_by_year = client.get_all_show_statistics(sort_by="year")
        self.assertEqual(stats_by_year[0]["title"], "Show 2")
        self.assertEqual(stats_by_year[1]["title"], "Show 1")

        # Test sort by rating
        stats_by_rating = client.get_all_show_statistics(sort_by="rating")
        self.assertEqual(stats_by_rating[0]["title"], "Show 2")
        self.assertEqual(stats_by_rating[1]["title"], "Show 1")

        # Test sort by last_watched (need to set last_watched dates)
        self.mock_episode1.history.return_value = [
            MagicMock(viewedAt=datetime(2023, 1, 1, 12, 0, 0))
        ]
        self.mock_episode3.history.return_value = [
            MagicMock(viewedAt=datetime(2023, 1, 2, 12, 0, 0))
        ]
        stats_by_last_watched = client.get_all_show_statistics(sort_by="last_watched")
        self.assertEqual(stats_by_last_watched[0]["title"], "Show 2")
        self.assertEqual(stats_by_last_watched[1]["title"], "Show 1")

    def test_get_show_statistics_error_handling(self):
        """Test error handling in _get_show_statistics."""
        # Mock show.episodes() to raise an exception
        self.mock_show1.episodes.side_effect = Exception("Error getting episodes")

        client = PlexClient(self.base_url, self.token)
        stats = client.get_all_show_statistics(
            include_unwatched=True
        )  # Include all shows, even those with errors

        # Should still return stats for both shows
        self.assertEqual(len(stats), 2)

        # Show 1 should have error details and default values
        show1_stat = next(stat for stat in stats if stat["title"] == "Show 1")
        self.assertEqual(show1_stat["total_episodes"], 0)
        self.assertEqual(show1_stat["watched_episodes"], 0)
        self.assertEqual(show1_stat["completion_percentage"], 0)
        self.assertIn("error", show1_stat)
        self.assertIn("Error getting episodes", show1_stat["error"])

    def test_get_show_statistics_history_exception_with_username(self):
        """Test handling of exceptions when retrieving episode history with a username."""
        # Mock episode to raise an exception when retrieving history with a username
        self.mock_episode1.history.side_effect = lambda username=None: (
            exec('raise Exception("History retrieval error")') if username else []
        )
        self.mock_episode2.history.return_value = []
        self.mock_episode3.history.side_effect = lambda username=None: (
            [self.mock_history_entry2] if username == "testuser" else []
        )
        self.mock_episode4.history.return_value = []

        client = PlexClient(self.base_url, self.token)
        stats = client.get_all_show_statistics(username="testuser")

        # Verify stats for shows with the specific user
        self.assertEqual(len(stats), 2)

        # Verify stats for Show 1
        show1_stat = next(stat for stat in stats if stat["title"] == "Show 1")
        self.assertEqual(show1_stat["watched_episodes"], 1)
        self.assertEqual(show1_stat["completion_percentage"], 50.0)

        # Verify stats for Show 2
        show2_stat = next(stat for stat in stats if stat["title"] == "Show 2")
        self.assertEqual(show2_stat["watched_episodes"], 1)
        self.assertEqual(show2_stat["completion_percentage"], 50.0)


class TestPlexClientMovieStatistics(unittest.TestCase):
    """Test the movie statistics functionality of PlexClient."""

    def setUp(self):
        """Set up common test fixtures."""
        self.base_url = "http://localhost:32400"
        self.token = "test_token"

        # Create mock for PlexServer and library
        self.mock_server = MagicMock(spec=PlexServer)
        # Add friendlyName attribute to prevent AttributeError
        self.mock_server.friendlyName = "Test Plex Server"
        self.mock_library = MagicMock()
        self.mock_server.library = self.mock_library

        # Set up the patch for PlexServer
        self.plex_server_patcher = patch(
            "plex_history_report.plex_client.PlexServer", return_value=self.mock_server
        )
        self.mock_plex_server = self.plex_server_patcher.start()

        # Create some mock movies
        self.setup_mock_movies()

    def setup_mock_movies(self):
        """Set up mock movie objects for testing."""
        # Create mock movie section
        self.mock_movie_section = MagicMock(spec=LibrarySection)
        self.mock_movie_section.type = "movie"
        self.mock_movie_section.title = "Movies"

        # Mock library sections to return movie section
        self.mock_library.sections.return_value = [self.mock_movie_section]

        # Create mock movies
        self.mock_movie1 = MagicMock(spec=Movie)
        self.mock_movie1.title = "Movie 1"
        self.mock_movie1.year = 2020
        self.mock_movie1.rating = 8.5
        self.mock_movie1.key = "/library/metadata/101"
        self.mock_movie1.duration = 120 * 60 * 1000  # 120 minutes in ms
        self.mock_movie1.isWatched = True
        type(self.mock_movie1).viewOffset = PropertyMock(return_value=0)  # Fully watched

        self.mock_movie2 = MagicMock(spec=Movie)
        self.mock_movie2.title = "Movie 2"
        self.mock_movie2.year = 2021
        self.mock_movie2.rating = 9.0
        self.mock_movie2.key = "/library/metadata/102"
        self.mock_movie2.duration = 90 * 60 * 1000  # 90 minutes in ms
        self.mock_movie2.isWatched = False
        # Use PropertyMock for viewOffset to ensure it's detected correctly
        type(self.mock_movie2).viewOffset = PropertyMock(
            return_value=45 * 60 * 1000
        )  # Half watched

        self.mock_movie3 = MagicMock(spec=Movie)
        self.mock_movie3.title = "Movie 3"
        self.mock_movie3.year = 2022
        self.mock_movie3.rating = 7.5
        self.mock_movie3.key = "/library/metadata/103"
        self.mock_movie3.duration = 100 * 60 * 1000  # 100 minutes in ms
        self.mock_movie3.isWatched = False
        type(self.mock_movie3).viewOffset = PropertyMock(return_value=0)  # Not watched

        # Mock movie section to return movies
        self.mock_movie_section.all.return_value = [
            self.mock_movie1,
            self.mock_movie2,
            self.mock_movie3,
        ]

        # Mock history entries
        self.mock_history_entry1 = MagicMock()
        self.mock_history_entry1.viewedAt = datetime(2023, 1, 1, 12, 0, 0)

        self.mock_history_entry2 = MagicMock()
        self.mock_history_entry2.viewedAt = datetime(2023, 1, 2, 12, 0, 0)

        # Configure movies to return history
        self.mock_movie1.history.return_value = [self.mock_history_entry1, self.mock_history_entry2]
        self.mock_movie2.history.return_value = []
        self.mock_movie3.history.return_value = []

    def tearDown(self):
        """Clean up after tests."""
        self.plex_server_patcher.stop()

    def test_get_all_movie_statistics_basic(self):
        """Test basic functionality of get_all_movie_statistics."""
        client = PlexClient(self.base_url, self.token)

        # Call the method
        stats = client.get_all_movie_statistics()

        # By default, only return watched movies
        self.assertEqual(len(stats), 1)

        # Verify stats for Movie 1
        movie1_stat = stats[0]
        self.assertEqual(movie1_stat["title"], "Movie 1")
        self.assertEqual(movie1_stat["year"], 2020)
        self.assertEqual(movie1_stat["rating"], 8.5)
        self.assertEqual(movie1_stat["duration_minutes"], 120)
        self.assertTrue(movie1_stat["watched"])
        self.assertEqual(movie1_stat["watch_count"], 2)
        self.assertEqual(movie1_stat["completion_percentage"], 100)

    def test_get_all_movie_statistics_include_unwatched(self):
        """Test get_all_movie_statistics with include_unwatched=True."""
        client = PlexClient(self.base_url, self.token)

        # Call the method with include_unwatched=True
        stats = client.get_all_movie_statistics(include_unwatched=True)

        # Should include all movies
        self.assertEqual(len(stats), 3)

        # Verify titles are included
        titles = [movie["title"] for movie in stats]
        self.assertIn("Movie 1", titles)
        self.assertIn("Movie 2", titles)
        self.assertIn("Movie 3", titles)

        # Verify stats for partially watched movie
        movie2_stat = next(movie for movie in stats if movie["title"] == "Movie 2")
        self.assertEqual(movie2_stat["completion_percentage"], 50.0)
        self.assertFalse(movie2_stat["watched"])

        # Verify stats for unwatched movie
        movie3_stat = next(movie for movie in stats if movie["title"] == "Movie 3")
        self.assertEqual(movie3_stat["completion_percentage"], 0.0)
        self.assertFalse(movie3_stat["watched"])

    def test_get_movie_statistics_partially_watched_only(self):
        """Test get_all_movie_statistics with partially_watched_only=True."""
        client = PlexClient(self.base_url, self.token)

        # Make sure the mock movie has a view offset but also appears to be watched
        # in the history, otherwise it might be filtered out as unwatched
        history_entry = MagicMock()
        history_entry.viewedAt = datetime(2023, 1, 1, 12, 0, 0)
        self.mock_movie2.history.return_value = [history_entry]

        # Call the method with partially_watched_only=True and include_unwatched=True
        # to avoid filtering based on watch status
        stats = client.get_all_movie_statistics(partially_watched_only=True, include_unwatched=True)

        # Should only include partially watched movies (Movie 2)
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]["title"], "Movie 2")
        self.assertEqual(stats[0]["completion_percentage"], 50.0)

    def test_get_movie_statistics_with_username(self):
        """Test retrieving movie statistics for a specific user."""
        # Set up movie history for a specific user
        self.mock_movie1.history.side_effect = lambda username=None: (
            [self.mock_history_entry1] if username == "testuser" else []
        )
        self.mock_movie2.history.side_effect = lambda username=None: (
            [self.mock_history_entry2] if username == "testuser" else []
        )

        client = PlexClient(self.base_url, self.token)
        stats = client.get_all_movie_statistics(username="testuser")

        # Verify stats for movies with the specific user
        self.assertEqual(len(stats), 2)

        # Verify titles are included
        titles = [movie["title"] for movie in stats]
        self.assertIn("Movie 1", titles)
        self.assertIn("Movie 2", titles)
        self.assertNotIn("Movie 3", titles)

    def test_get_movie_statistics_sorting(self):
        """Test sorting options for movie statistics."""
        client = PlexClient(self.base_url, self.token)

        # Include all movies for sorting tests
        # No need to store the result in a variable
        client.get_all_movie_statistics(include_unwatched=True)

        # Test sort by title (default)
        stats_by_title = client.get_all_movie_statistics(include_unwatched=True, sort_by="title")
        self.assertEqual(stats_by_title[0]["title"], "Movie 1")
        self.assertEqual(stats_by_title[1]["title"], "Movie 2")
        self.assertEqual(stats_by_title[2]["title"], "Movie 3")

        # Test sort by year
        stats_by_year = client.get_all_movie_statistics(include_unwatched=True, sort_by="year")
        self.assertEqual(stats_by_year[0]["title"], "Movie 3")
        self.assertEqual(stats_by_year[1]["title"], "Movie 2")
        self.assertEqual(stats_by_year[2]["title"], "Movie 1")

        # Test sort by watch_count
        stats_by_watch_count = client.get_all_movie_statistics(
            include_unwatched=True, sort_by="watch_count"
        )
        self.assertEqual(stats_by_watch_count[0]["title"], "Movie 1")

        # Test sort by rating
        stats_by_rating = client.get_all_movie_statistics(include_unwatched=True, sort_by="rating")
        self.assertEqual(stats_by_rating[0]["title"], "Movie 2")
        self.assertEqual(stats_by_rating[1]["title"], "Movie 1")
        self.assertEqual(stats_by_rating[2]["title"], "Movie 3")

        # Test sort by duration_minutes
        stats_by_duration = client.get_all_movie_statistics(
            include_unwatched=True, sort_by="duration_minutes"
        )
        self.assertEqual(stats_by_duration[0]["title"], "Movie 1")
        self.assertEqual(stats_by_duration[1]["title"], "Movie 3")
        self.assertEqual(stats_by_duration[2]["title"], "Movie 2")

    def test_get_movie_statistics_sort_by_last_watched(self):
        """Test sorting movie statistics by last_watched date."""
        # Configure each movie with different last watched dates
        now = datetime(2023, 1, 10, 12, 0, 0)
        yesterday = datetime(2023, 1, 9, 12, 0, 0)
        week_ago = datetime(2023, 1, 3, 12, 0, 0)

        history_entry_now = MagicMock()
        history_entry_now.viewedAt = now

        history_entry_yesterday = MagicMock()
        history_entry_yesterday.viewedAt = yesterday

        history_entry_week_ago = MagicMock()
        history_entry_week_ago.viewedAt = week_ago

        # Movie 1 - watched yesterday
        self.mock_movie1.history.return_value = [history_entry_yesterday]

        # Movie 2 - watched now (most recent)
        self.mock_movie2.history.return_value = [history_entry_now]

        # Movie 3 - watched a week ago (oldest)
        self.mock_movie3.history.return_value = [history_entry_week_ago]

        # Make sure all movies will be included in the results
        # by setting them to have some watch history
        self.mock_movie1.isWatched = True
        self.mock_movie2.isWatched = True
        self.mock_movie3.isWatched = True

        client = PlexClient(self.base_url, self.token)

        # Call the method with sort_by="last_watched"
        stats = client.get_all_movie_statistics(sort_by="last_watched")

        # Should be sorted by last_watched date, most recent first
        self.assertEqual(len(stats), 3)
        self.assertEqual(stats[0]["title"], "Movie 2")  # most recent (now)
        self.assertEqual(stats[1]["title"], "Movie 1")  # yesterday
        self.assertEqual(stats[2]["title"], "Movie 3")  # week ago

    def test_get_movie_statistics_error_handling(self):
        """Test error handling in _get_movie_statistics."""
        # Add a problematic movie that raises an exception when accessing attributes
        mock_error_movie = MagicMock(spec=Movie)
        mock_error_movie.title = "Error Movie"
        mock_error_movie.key = "/library/metadata/104"

        # Make duration and other property access raise an exception
        type(mock_error_movie).duration = PropertyMock(side_effect=Exception("Duration error"))

        # Update the movies returned by the movie section
        self.mock_movie_section.all.return_value = [
            self.mock_movie1,
            self.mock_movie2,
            self.mock_movie3,
            mock_error_movie,
        ]

        client = PlexClient(self.base_url, self.token)
        stats = client.get_all_movie_statistics(include_unwatched=True)

        # Should return stats for all 4 movies, including the one with error
        self.assertEqual(len(stats), 4)

        # Find the error movie stats
        error_movie_stat = next(movie for movie in stats if movie["title"] == "Error Movie")
        self.assertIn("error", error_movie_stat)
        self.assertEqual(error_movie_stat["duration_minutes"], 0)
        self.assertEqual(error_movie_stat["watch_count"], 0)
        self.assertEqual(error_movie_stat["completion_percentage"], 0)

    def test_get_all_movie_statistics_no_movie_sections(self):
        """Test get_all_movie_statistics with no movie sections."""
        # Mock library sections to return no movie sections
        self.mock_library.sections.return_value = []

        client = PlexClient(self.base_url, self.token)
        stats = client.get_all_movie_statistics()

        # Should return empty list with no movie sections
        self.assertEqual(stats, [])

    def test_get_movie_statistics_history_exception_with_username(self):
        """Test handling of exceptions when retrieving movie history with a username."""
        # Mock movie to raise an exception when retrieving history with a username
        self.mock_movie1.history.side_effect = lambda username=None: (
            exec('raise Exception("Movie history retrieval error")')
            if username
            else [self.mock_history_entry1]
        )

        # Set up movie2 to return history for test user so at least one movie appears in results
        self.mock_movie2.history.side_effect = lambda username=None: (
            [self.mock_history_entry2] if username == "testuser" else []
        )
        # Mark movie2 as watched for the test user
        self.mock_movie2.isWatched = True

        client = PlexClient(self.base_url, self.token)
        stats = client.get_all_movie_statistics(username="testuser")

        # Should still return stats despite the exception
        self.assertEqual(len(stats), 1)  # Only movie2 should be returned

        # Verify the movie that was included has correct stats
        movie_stat = stats[0]
        self.assertEqual(movie_stat["title"], "Movie 2")
        self.assertEqual(movie_stat["watch_count"], 1)
        self.assertTrue(movie_stat["watched"])

    def test_get_movie_statistics_viewoffset_edge_cases(self):
        """Test edge cases in viewOffset handling when getting movie statistics."""
        # Create a movie that doesn't have the viewOffset attribute
        mock_no_viewoffset_movie = MagicMock(spec=Movie)
        mock_no_viewoffset_movie.title = "No ViewOffset Movie"
        mock_no_viewoffset_movie.year = 2023
        mock_no_viewoffset_movie.rating = 8.0
        mock_no_viewoffset_movie.key = "/library/metadata/104"
        mock_no_viewoffset_movie.duration = 110 * 60 * 1000  # 110 minutes in ms
        mock_no_viewoffset_movie.isWatched = False
        mock_no_viewoffset_movie.history.return_value = [self.mock_history_entry1]

        # Create a movie where accessing viewOffset raises an exception
        mock_error_viewoffset_movie = MagicMock(spec=Movie)
        mock_error_viewoffset_movie.title = "Error ViewOffset Movie"
        mock_error_viewoffset_movie.year = 2023
        mock_error_viewoffset_movie.rating = 8.5
        mock_error_viewoffset_movie.key = "/library/metadata/105"
        mock_error_viewoffset_movie.duration = 115 * 60 * 1000  # 115 minutes in ms
        mock_error_viewoffset_movie.isWatched = False
        mock_error_viewoffset_movie.history.return_value = [self.mock_history_entry2]

        # Set up the viewOffset property to raise an exception when accessed
        type(mock_error_viewoffset_movie).viewOffset = PropertyMock(
            side_effect=Exception("ViewOffset error")
        )

        # Update the movies returned by the movie section
        self.mock_movie_section.all.return_value = [
            self.mock_movie1,
            mock_no_viewoffset_movie,
            mock_error_viewoffset_movie,
        ]

        client = PlexClient(self.base_url, self.token)

        # We need to include unwatched movies to see movies without watch history
        stats = client.get_all_movie_statistics(include_unwatched=True)

        # Should return stats for all three movies
        self.assertEqual(len(stats), 3)

        # Find stats for the no-viewOffset movie
        no_viewoffset_stat = next(
            movie for movie in stats if movie["title"] == "No ViewOffset Movie"
        )
        self.assertEqual(
            no_viewoffset_stat["completion_percentage"], 0
        )  # Default for movies without viewOffset
        self.assertEqual(no_viewoffset_stat["view_offset"], 0)  # Should default to 0

        # Find stats for the error-viewOffset movie
        error_viewoffset_stat = next(
            movie for movie in stats if movie["title"] == "Error ViewOffset Movie"
        )
        self.assertEqual(
            error_viewoffset_stat["completion_percentage"], 0
        )  # Should handle the error gracefully
        self.assertEqual(error_viewoffset_stat["view_offset"], 0)  # Should default to 0


class TestPlexClientRecentlyWatched(unittest.TestCase):
    """Test the recently watched functionality of PlexClient."""

    def setUp(self):
        """Set up common test fixtures."""
        self.base_url = "http://localhost:32400"
        self.token = "test_token"

        # Create mock for PlexServer
        self.mock_server = MagicMock(spec=PlexServer)
        # Add friendlyName attribute to prevent AttributeError
        self.mock_server.friendlyName = "Test Plex Server"

        # Set up the patch for PlexServer
        self.plex_server_patcher = patch(
            "plex_history_report.plex_client.PlexServer", return_value=self.mock_server
        )
        self.mock_plex_server = self.plex_server_patcher.start()

        # Create mock history entries
        self.setup_mock_history()

    def setup_mock_history(self):
        """Set up mock history objects for testing."""
        # Mock TV episodes in history
        self.mock_episode1 = MagicMock()
        self.mock_episode1.type = "episode"
        self.mock_episode1.title = "Episode 1"
        self.mock_episode1.seasonNumber = 1
        self.mock_episode1.index = 1
        self.mock_episode1.duration = 30 * 60 * 1000  # 30 minutes in ms
        self.mock_episode1.viewedAt = datetime(2023, 1, 1, 12, 0, 0)
        self.mock_episode1.username = "user1"

        mock_show1 = MagicMock(spec=Show)
        mock_show1.title = "Show 1"
        mock_show1.year = 2020
        mock_show1.key = "/library/metadata/1"
        self.mock_episode1.show.return_value = mock_show1

        self.mock_episode2 = MagicMock()
        self.mock_episode2.type = "episode"
        self.mock_episode2.title = "Episode 2"
        self.mock_episode2.seasonNumber = 1
        self.mock_episode2.index = 2
        self.mock_episode2.duration = 30 * 60 * 1000
        self.mock_episode2.viewedAt = datetime(2023, 1, 2, 12, 0, 0)
        self.mock_episode2.username = "user2"

        mock_show2 = MagicMock(spec=Show)
        mock_show2.title = "Show 2"
        mock_show2.year = 2021
        mock_show2.key = "/library/metadata/2"
        self.mock_episode2.show.return_value = mock_show2

        # Invalid type episode (not really an episode)
        self.mock_invalid = MagicMock()
        self.mock_invalid.type = "clip"

        # Episode that raises an exception when accessing show
        self.mock_error_episode = MagicMock()
        self.mock_error_episode.type = "episode"
        self.mock_error_episode.show.side_effect = Exception("Error accessing show")

        # Mock movies in history
        self.mock_movie1 = MagicMock(spec=Movie)
        self.mock_movie1.type = "movie"
        self.mock_movie1.title = "Movie 1"
        self.mock_movie1.year = 2020
        self.mock_movie1.rating = 8.5
        self.mock_movie1.duration = 120 * 60 * 1000
        self.mock_movie1.key = "/library/metadata/101"
        self.mock_movie1.viewedAt = datetime(2023, 1, 3, 12, 0, 0)
        self.mock_movie1.username = "user1"

        self.mock_movie2 = MagicMock(spec=Movie)
        self.mock_movie2.type = "movie"
        self.mock_movie2.title = "Movie 2"
        self.mock_movie2.year = 2021
        self.mock_movie2.rating = 9.0
        self.mock_movie2.duration = 90 * 60 * 1000
        self.mock_movie2.key = "/library/metadata/102"
        self.mock_movie2.viewedAt = datetime(2023, 1, 4, 12, 0, 0)
        self.mock_movie2.username = "user2"

        # Configure server to return history
        # For TV shows - using underscore for unused arguments
        self.mock_server.history.side_effect = lambda _=None, type=None, _username=None: (
            [self.mock_episode1, self.mock_episode2, self.mock_invalid, self.mock_error_episode]
            if type == "episode"
            else [self.mock_movie1, self.mock_movie2]
        )

    def tearDown(self):
        """Clean up after tests."""
        self.plex_server_patcher.stop()

    def test_get_recently_watched_shows_basic(self):
        """Test basic functionality of get_recently_watched_shows."""
        client = PlexClient(self.base_url, self.token)

        # Call the method with default limit
        shows = client.get_recently_watched_shows()

        # Verify we got the expected results
        self.assertEqual(len(shows), 2)

        # First show
        self.assertEqual(shows[0]["show_title"], "Show 1")
        self.assertEqual(shows[0]["episode_title"], "Episode 1")
        self.assertEqual(shows[0]["season"], 1)
        self.assertEqual(shows[0]["episode"], 1)
        self.assertEqual(shows[0]["duration_minutes"], 30)
        self.assertEqual(shows[0]["viewed_at"], datetime(2023, 1, 1, 12, 0, 0))
        self.assertEqual(shows[0]["user"], "user1")
        self.assertEqual(shows[0]["year"], 2020)

        # Second show
        self.assertEqual(shows[1]["show_title"], "Show 2")
        self.assertEqual(shows[1]["year"], 2021)

    def test_get_recently_watched_shows_with_username(self):
        """Test get_recently_watched_shows with username filtering."""
        # Configure server history with username filtering
        self.mock_server.history.side_effect = lambda _=None, type=None, username=None: (
            [self.mock_episode1]
            if username == "user1" and type == "episode"
            else [self.mock_episode2] if username == "user2" and type == "episode" else []
        )

        client = PlexClient(self.base_url, self.token)

        # Test with user1
        shows_user1 = client.get_recently_watched_shows(username="user1")
        self.assertEqual(len(shows_user1), 1)
        self.assertEqual(shows_user1[0]["show_title"], "Show 1")
        self.assertEqual(shows_user1[0]["user"], "user1")

        # Test with user2
        shows_user2 = client.get_recently_watched_shows(username="user2")
        self.assertEqual(len(shows_user2), 1)
        self.assertEqual(shows_user2[0]["show_title"], "Show 2")
        self.assertEqual(shows_user2[0]["user"], "user2")

    def test_get_recently_watched_shows_limit(self):
        """Test get_recently_watched_shows with limit parameter."""
        # Add more episodes to test limiting
        mock_episode3 = MagicMock()
        mock_episode3.type = "episode"
        mock_episode3.title = "Episode 3"
        mock_episode3.seasonNumber = 1
        mock_episode3.index = 3
        mock_episode3.duration = 45 * 60 * 1000
        mock_episode3.viewedAt = datetime(2023, 1, 5, 12, 0, 0)
        mock_episode3.username = "user1"

        mock_show3 = MagicMock(spec=Show)
        mock_show3.title = "Show 3"
        mock_show3.year = 2022
        mock_show3.key = "/library/metadata/3"
        mock_episode3.show.return_value = mock_show3

        # Configure server to return more episodes
        self.mock_server.history.side_effect = lambda _=None, type=None, _username=None: (
            [self.mock_episode1, self.mock_episode2, mock_episode3] if type == "episode" else []
        )

        client = PlexClient(self.base_url, self.token)

        # Test with limit=2
        shows = client.get_recently_watched_shows(limit=2)
        self.assertEqual(len(shows), 2)

        # Test with limit=1
        shows_limited = client.get_recently_watched_shows(limit=1)
        self.assertEqual(len(shows_limited), 1)

    def test_get_recently_watched_shows_error_handling(self):
        """Test error handling in get_recently_watched_shows."""
        # Configure server to raise exception
        self.mock_server.history.side_effect = Exception("Failed to get history")

        client = PlexClient(self.base_url, self.token)
        shows = client.get_recently_watched_shows()

        # Should return empty list on error
        self.assertEqual(shows, [])

    def test_get_recently_watched_movies_basic(self):
        """Test basic functionality of get_recently_watched_movies."""
        client = PlexClient(self.base_url, self.token)

        # Call the method with default limit
        movies = client.get_recently_watched_movies()

        # Verify we got the expected results
        self.assertEqual(len(movies), 2)

        # First movie
        self.assertEqual(movies[0]["title"], "Movie 1")
        self.assertEqual(movies[0]["year"], 2020)
        self.assertEqual(movies[0]["duration_minutes"], 120)
        self.assertEqual(movies[0]["viewed_at"], datetime(2023, 1, 3, 12, 0, 0))
        self.assertEqual(movies[0]["user"], "user1")
        self.assertEqual(movies[0]["rating"], 8.5)

        # Second movie
        self.assertEqual(movies[1]["title"], "Movie 2")
        self.assertEqual(movies[1]["year"], 2021)
        self.assertEqual(movies[1]["rating"], 9.0)

    def test_get_recently_watched_movies_with_username(self):
        """Test get_recently_watched_movies with username filtering."""
        # Configure server history with username filtering
        self.mock_server.history.side_effect = lambda _=None, type=None, username=None: (
            [self.mock_movie1]
            if username == "user1" and type == "movie"
            else [self.mock_movie2] if username == "user2" and type == "movie" else []
        )

        client = PlexClient(self.base_url, self.token)

        # Test with user1
        movies_user1 = client.get_recently_watched_movies(username="user1")
        self.assertEqual(len(movies_user1), 1)
        self.assertEqual(movies_user1[0]["title"], "Movie 1")
        self.assertEqual(movies_user1[0]["user"], "user1")

        # Test with user2
        movies_user2 = client.get_recently_watched_movies(username="user2")
        self.assertEqual(len(movies_user2), 1)
        self.assertEqual(movies_user2[0]["title"], "Movie 2")
        self.assertEqual(movies_user2[0]["user"], "user2")

    def test_get_recently_watched_movies_limit(self):
        """Test get_recently_watched_movies with limit parameter."""
        # Add more movies to test limiting
        mock_movie3 = MagicMock(spec=Movie)
        mock_movie3.type = "movie"
        mock_movie3.title = "Movie 3"
        mock_movie3.year = 2022
        mock_movie3.rating = 7.5
        mock_movie3.duration = 100 * 60 * 1000
        mock_movie3.key = "/library/metadata/103"
        mock_movie3.viewedAt = datetime(2023, 1, 5, 12, 0, 0)
        mock_movie3.username = "user1"

        # Configure server to return more movies
        self.mock_server.history.side_effect = lambda _=None, type=None, _username=None: (
            [self.mock_movie1, self.mock_movie2, mock_movie3] if type == "movie" else []
        )

        client = PlexClient(self.base_url, self.token)

        # Test with limit=2
        movies = client.get_recently_watched_movies(limit=2)
        self.assertEqual(len(movies), 2)

        # Test with limit=1
        movies_limited = client.get_recently_watched_movies(limit=1)
        self.assertEqual(len(movies_limited), 1)

    def test_get_recently_watched_movies_error_handling(self):
        """Test error handling in get_recently_watched_movies."""
        # Configure server to raise exception
        self.mock_server.history.side_effect = Exception("Failed to get history")

        client = PlexClient(self.base_url, self.token)
        movies = client.get_recently_watched_movies()

        # Should return empty list on error
        self.assertEqual(movies, [])
