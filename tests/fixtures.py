"""Test fixtures for Plex History Report tests."""

from datetime import datetime
from unittest.mock import MagicMock, PropertyMock

from plexapi.library import LibrarySection
from plexapi.server import PlexServer
from plexapi.video import Movie, Show


def create_mock_server(friendly_name="Test Plex Server"):
    """Create a mock PlexServer."""
    mock_server = MagicMock(spec=PlexServer)
    mock_server.friendlyName = friendly_name
    mock_library = MagicMock()
    mock_server.library = mock_library
    return mock_server


def create_mock_section(section_type="show", title="TV Shows"):
    """Create a mock LibrarySection.

    Args:
        section_type: Type of section ("show" or "movie").
        title: Title for the section.

    Returns:
        Mock LibrarySection object.
    """
    mock_section = MagicMock(spec=LibrarySection)
    mock_section.type = section_type
    mock_section.title = title
    return mock_section


def create_mock_show(
    title="Test Show",
    year=2020,
    rating=8.5,
    key="/library/metadata/1",
    episodes=None,
    history_entries=None,
):
    """Create a mock Show.

    Args:
        title: Show title.
        year: Year the show was released.
        rating: Show rating.
        key: Plex library key.
        episodes: List of episodes or None to create an empty list.
        history_entries: List of history entries for the show or None.

    Returns:
        Mock Show object.
    """
    mock_show = MagicMock(spec=Show)
    mock_show.title = title
    mock_show.year = year
    mock_show.rating = rating
    mock_show.key = key

    # Configure episodes
    if episodes is not None:
        mock_show.episodes.return_value = episodes
    else:
        mock_show.episodes.return_value = []

    # Configure history if provided
    if history_entries is not None:

        def show_history(username=None, maxresults=None):
            entries = history_entries
            if username:
                entries = [
                    entry
                    for entry in entries
                    if hasattr(entry, "username") and entry.username == username
                ]
            if maxresults is not None:
                entries = entries[:maxresults]
            return entries

        mock_show.history = show_history

    return mock_show


def create_mock_episode(
    title="Test Episode",
    is_watched=True,
    view_count=1,
    duration=30 * 60 * 1000,  # 30 minutes in ms
    grandparent_key="1",
    episode_index=1,
    season_number=1,
    history_entries=None,
):
    """Create a mock Episode.

    Args:
        title: Episode title.
        is_watched: Whether the episode has been watched.
        view_count: Number of times the episode has been watched.
        duration: Episode duration in milliseconds.
        grandparent_key: Key of the parent show.
        episode_index: Episode number.
        season_number: Season number.
        history_entries: List of history entries for the episode or None.

    Returns:
        Mock Episode object.
    """
    mock_episode = MagicMock()
    mock_episode.title = title
    mock_episode.isWatched = is_watched
    type(mock_episode).viewCount = PropertyMock(return_value=view_count)
    mock_episode.duration = duration
    mock_episode.grandparentRatingKey = grandparent_key
    mock_episode.index = episode_index
    mock_episode.seasonNumber = season_number

    # Configure history if provided
    if history_entries is not None:

        def episode_history(_username=None, maxresults=None):
            entries = history_entries
            if maxresults is not None:
                entries = entries[:maxresults]
            return entries

        mock_episode.history = episode_history

    return mock_episode


def create_mock_movie(
    title="Test Movie",
    year=2020,
    rating=8.5,
    key="/library/metadata/101",
    duration=120 * 60 * 1000,  # 120 minutes in ms
    is_watched=True,
    view_count=1,
    view_offset=0,
    history_entries=None,
):
    """Create a mock Movie.

    Args:
        title: Movie title.
        year: Year the movie was released.
        rating: Movie rating.
        key: Plex library key.
        duration: Movie duration in milliseconds.
        is_watched: Whether the movie has been watched.
        view_count: Number of times the movie has been watched.
        view_offset: Current view position in milliseconds.
        history_entries: List of history entries for the movie or None.

    Returns:
        Mock Movie object.
    """
    mock_movie = MagicMock(spec=Movie)
    mock_movie.title = title
    mock_movie.year = year
    mock_movie.rating = rating
    mock_movie.key = key
    mock_movie.duration = duration
    mock_movie.isWatched = is_watched
    type(mock_movie).viewCount = PropertyMock(return_value=view_count)
    type(mock_movie).viewOffset = PropertyMock(return_value=view_offset)

    # Configure history if provided
    if history_entries is not None:

        def movie_history(_username=None, maxresults=None):
            entries = history_entries
            if maxresults is not None:
                entries = entries[:maxresults]
            return entries

        mock_movie.history = movie_history

    return mock_movie


def create_history_entry(
    viewed_at=None,
    grandparent_rating_key=None,
    index=None,
    username=None,
):
    """Create a mock history entry.

    Args:
        viewed_at: Datetime when the item was viewed.
        grandparent_rating_key: Key of the parent show.
        index: Episode index.
        username: Username who viewed the item.

    Returns:
        Mock history entry.
    """
    if viewed_at is None:
        viewed_at = datetime.now()

    entry = MagicMock()
    entry.viewedAt = viewed_at

    if grandparent_rating_key:
        entry.grandparentRatingKey = grandparent_rating_key

    if index:
        entry.index = index

    if username:
        entry.username = username

    return entry
