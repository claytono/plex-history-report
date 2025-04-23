"""Plex client module for retrieving statistics."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from plexapi.exceptions import Unauthorized
from plexapi.library import LibrarySection
from plexapi.server import PlexServer
from plexapi.video import Movie, Show

logger = logging.getLogger(__name__)


class PlexClientError(Exception):
    """Exception raised for Plex client errors."""
    pass


class PlexClient:
    """Client for interacting with a Plex server."""

    def __init__(self, base_url: str, token: str):
        """Initialize the Plex client.

        Args:
            base_url: Base URL for the Plex server.
            token: Authentication token for the Plex server.

        Raises:
            PlexClientError: If connection to the Plex server fails.
        """
        self.base_url = base_url
        self.token = token

        try:
            logger.debug(f"Connecting to Plex server at {base_url}")
            self.server = PlexServer(base_url, token)
            logger.debug(f"Connected to Plex server: {self.server.friendlyName}")
        except Exception as e:
            raise PlexClientError(f"Failed to connect to Plex server: {e}") from e

    def get_available_users(self) -> List[str]:
        """Get a list of available Plex users.

        Returns:
            List of usernames.
        """
        try:
            users = []

            # Add the admin user (owner)
            users.append("admin")

            # Add shared users (if available)
            try:
                for user in self.server.myPlexAccount().users():
                    users.append(user.username)
            except Unauthorized:
                logger.warning("Unauthorized to access myPlex account users. "
                              "This may be expected if using a managed user token.")
                pass

            return users
        except Exception as e:
            logger.warning(f"Failed to get user list: {e}")
            return []

    def get_library_sections(self) -> List[LibrarySection]:
        """Get all library sections from the Plex server.

        Returns:
            List of library sections.
        """
        return self.server.library.sections()

    def get_all_show_statistics(
        self,
        username: Optional[str] = None,
        include_unwatched: bool = False,
        partially_watched_only: bool = False,
        sort_by: str = 'title'
    ) -> List[Dict]:
        """Get statistics for all TV shows.

        Args:
            username: Filter statistics for a specific user.
            include_unwatched: Include shows with no watched episodes.
            partially_watched_only: Only include shows that are partially watched.
            sort_by: Field to sort results by.

        Returns:
            List of show statistics.
        """
        logger.debug(f"Getting show statistics (user={username}, include_unwatched={include_unwatched}, "
                    f"partially_watched_only={partially_watched_only})")

        # Get all TV library sections
        tv_sections = [section for section in self.server.library.sections() if section.type == 'show']

        if not tv_sections:
            logger.warning("No TV library sections found")
            return []

        # Fetch all shows from all TV sections
        all_shows = []
        for section in tv_sections:
            all_shows.extend(section.all())

        # Process each show
        show_stats = []
        for show in all_shows:
            stat = self._get_show_statistics(show, username)

            # Handle filtering conditions
            if not include_unwatched and stat['watched_episodes'] == 0:
                # Skip unwatched shows
                continue

            # Only keep partially watched shows if requested
            if partially_watched_only and not (0 < stat['completion_percentage'] < 100):
                # Skip fully watched or completely unwatched shows
                continue

            show_stats.append(stat)

        # Sort results
        if sort_by == 'title':
            show_stats.sort(key=lambda x: x['title'].lower())
        elif sort_by == 'watched_episodes':
            show_stats.sort(key=lambda x: x['watched_episodes'], reverse=True)
        elif sort_by == 'completion_percentage':
            show_stats.sort(key=lambda x: x['completion_percentage'], reverse=True)
        elif sort_by == 'last_watched':
            # Sort by last_watched, placing None values at the end
            show_stats.sort(
                key=lambda x: datetime.min if x['last_watched'] is None else x['last_watched'],
                reverse=True
            )
        elif sort_by == 'year':
            # Sort by year, placing None values at the end
            show_stats.sort(
                key=lambda x: 0 if x['year'] is None else x['year'],
                reverse=True
            )
        elif sort_by == 'rating':
            # Sort by rating, placing None values at the end
            show_stats.sort(
                key=lambda x: 0 if x['rating'] is None else x['rating'],
                reverse=True
            )

        return show_stats

    def _get_show_statistics(self, show: Show, username: Optional[str] = None) -> Dict:
        """Get statistics for a single show.

        Args:
            show: Plex Show object.
            username: Filter statistics for a specific user.

        Returns:
            Dictionary with show statistics.
        """
        try:
            logger.debug(f"Getting statistics for show: {show.title}")

            # Get all episodes for this show
            episodes = show.episodes()
            total_episodes = len(episodes)

            # Track statistics
            watched_episodes = 0
            total_watch_time = 0
            last_watched_date = None

            # Process each episode
            for episode in episodes:
                # Check if this episode has been watched by the specified user
                watched = False

                if username:
                    # Get watch history for specific user
                    try:
                        history = episode.history(username=username)
                        watched = bool(history)

                        # Update last watched date if needed
                        if watched and history:
                            for entry in history:
                                watch_date = entry.viewedAt
                                if watch_date and (last_watched_date is None or watch_date > last_watched_date):
                                    last_watched_date = watch_date

                                # Add watch time to total
                                if episode.duration:
                                    total_watch_time += episode.duration / 60000  # Convert ms to minutes
                    except Exception as e:
                        logger.debug(f"Error getting history for episode: {e}")
                else:
                    # Check if episode is marked as watched globally
                    watched = episode.isWatched

                    # Get history for all users
                    try:
                        history = episode.history()
                        if history:
                            for entry in history:
                                watch_date = entry.viewedAt
                                if watch_date and (last_watched_date is None or watch_date > last_watched_date):
                                    last_watched_date = watch_date

                                # Add watch time to total (ms to minutes)
                                if episode.duration:
                                    total_watch_time += episode.duration / 60000
                    except Exception as e:
                        logger.debug(f"Error getting history for episode: {e}")

                if watched:
                    watched_episodes += 1

            # Calculate completion percentage
            completion_percentage = 0
            if total_episodes > 0:
                completion_percentage = (watched_episodes / total_episodes) * 100

            # Build the statistics dictionary
            return {
                'title': show.title,
                'total_episodes': total_episodes,
                'watched_episodes': watched_episodes,
                'unwatched_episodes': total_episodes - watched_episodes,
                'completion_percentage': completion_percentage,
                'total_watch_time_minutes': total_watch_time,
                'last_watched': last_watched_date,
                'year': show.year,
                'rating': show.rating,
                'key': show.key
            }

        except Exception as e:
            logger.error(f"Error processing show {show.title}: {e}")
            # Return a minimal statistics dictionary on error
            return {
                'title': show.title,
                'total_episodes': 0,
                'watched_episodes': 0,
                'unwatched_episodes': 0,
                'completion_percentage': 0,
                'total_watch_time_minutes': 0,
                'last_watched': None,
                'year': None,
                'rating': None,
                'key': show.key,
                'error': str(e)
            }

    def get_all_movie_statistics(
        self,
        username: Optional[str] = None,
        include_unwatched: bool = False,
        partially_watched_only: bool = False,
        sort_by: str = 'title'
    ) -> List[Dict]:
        """Get statistics for all movies.

        Args:
            username: Filter statistics for a specific user.
            include_unwatched: Include unwatched movies.
            partially_watched_only: Only include partially watched movies.
            sort_by: Field to sort results by.

        Returns:
            List of movie statistics.
        """
        logger.debug(f"Getting movie statistics (user={username}, include_unwatched={include_unwatched}, "
                    f"partially_watched_only={partially_watched_only})")

        # Get all movie library sections
        movie_sections = [section for section in self.server.library.sections() if section.type == 'movie']

        if not movie_sections:
            logger.warning("No movie library sections found")
            return []

        # Fetch all movies from all movie sections
        all_movies = []
        for section in movie_sections:
            all_movies.extend(section.all())

        # Process each movie
        movie_stats = []
        for movie in all_movies:
            stat = self._get_movie_statistics(movie, username)

            # Apply filtering based on watch status
            if not include_unwatched and not stat['watched']:
                # Skip unwatched movies
                continue

            # Filter for partially watched movies if requested
            if partially_watched_only and not (0 < stat['completion_percentage'] < 100):
                # Skip fully watched or completely unwatched movies
                continue

            movie_stats.append(stat)

        # Sort results
        if sort_by == 'title':
            movie_stats.sort(key=lambda x: x['title'].lower())
        elif sort_by == 'year':
            movie_stats.sort(key=lambda x: 0 if x['year'] is None else x['year'], reverse=True)
        elif sort_by == 'last_watched':
            movie_stats.sort(
                key=lambda x: datetime.min if x['last_watched'] is None else x['last_watched'],
                reverse=True
            )
        elif sort_by == 'watch_count':
            movie_stats.sort(key=lambda x: x['watch_count'], reverse=True)
        elif sort_by == 'rating':
            movie_stats.sort(
                key=lambda x: 0 if x['rating'] is None else x['rating'],
                reverse=True
            )
        elif sort_by == 'duration_minutes':
            movie_stats.sort(key=lambda x: x['duration_minutes'], reverse=True)

        return movie_stats

    def _get_movie_statistics(self, movie: Movie, username: Optional[str] = None) -> Dict:
        """Get statistics for a single movie.

        Args:
            movie: Plex Movie object.
            username: Filter statistics for a specific user.

        Returns:
            Dictionary with movie statistics.
        """
        try:
            logger.debug(f"Getting statistics for movie: {movie.title}")

            # Get watch history
            watch_count = 0
            last_watched_date = None
            view_offset = 0  # Track view offset to determine if partially watched
            watched = False

            # Convert duration from milliseconds to minutes
            duration_minutes = movie.duration / 60000 if movie.duration else 0

            if username:
                # Get history for specific user
                try:
                    history = movie.history(username=username)
                    watch_count = len(history)
                    watched = bool(history)

                    # Get last watched date
                    if history:
                        for entry in history:
                            if entry.viewedAt and (last_watched_date is None or entry.viewedAt > last_watched_date):
                                last_watched_date = entry.viewedAt
                except Exception as e:
                    logger.debug(f"Error getting history for movie '{movie.title}': {e}")

                # Check if movie is partially watched
                try:
                    # Try to get view offset for this user
                    if hasattr(movie, 'viewOffset'):
                        view_offset = movie.viewOffset
                        logger.debug(f"Movie '{movie.title}' has viewOffset: {view_offset} out of {movie.duration} ({(view_offset / movie.duration * 100):.1f}% watched)")
                except Exception as e:
                    logger.debug(f"Error getting viewOffset for movie '{movie.title}': {e}")
            else:
                # Check if movie is marked as watched globally
                watched = movie.isWatched

                # Get history for all users
                try:
                    history = movie.history()
                    watch_count = len(history)

                    # Get last watched date across all users
                    if history:
                        for entry in history:
                            if entry.viewedAt and (last_watched_date is None or entry.viewedAt > last_watched_date):
                                last_watched_date = entry.viewedAt
                except Exception as e:
                    logger.debug(f"Error getting history for movie '{movie.title}': {e}")

                # Check if movie is partially watched
                try:
                    # Try to get view offset
                    if hasattr(movie, 'viewOffset'):
                        view_offset = movie.viewOffset
                        logger.debug(f"Movie '{movie.title}' has viewOffset: {view_offset} out of {movie.duration} ({(view_offset / movie.duration * 100):.1f}% watched)")
                except Exception as e:
                    logger.debug(f"Error getting viewOffset for movie '{movie.title}': {e}")

            # Calculate completion percentage if partially watched
            completion_percentage = 0
            if view_offset > 0 and movie.duration:
                completion_percentage = (view_offset / movie.duration) * 100
                logger.debug(f"Movie '{movie.title}' completion: {completion_percentage:.1f}%")
            elif watched:
                completion_percentage = 100
                logger.debug(f"Movie '{movie.title}' marked as fully watched")
            else:
                logger.debug(f"Movie '{movie.title}' is unwatched")

            # Build the statistics dictionary
            return {
                'title': movie.title,
                'year': movie.year,
                'duration_minutes': duration_minutes,
                'watched': watched,
                'watch_count': watch_count,
                'last_watched': last_watched_date,
                'rating': movie.rating,
                'view_offset': view_offset,
                'completion_percentage': completion_percentage,
                'key': movie.key
            }

        except Exception as e:
            logger.error(f"Error processing movie {movie.title}: {e}")
            # Return a minimal statistics dictionary on error
            return {
                'title': movie.title,
                'year': None,
                'duration_minutes': 0,
                'watched': False,
                'watch_count': 0,
                'last_watched': None,
                'rating': None,
                'view_offset': 0,
                'completion_percentage': 0,
                'key': movie.key,
                'error': str(e)
            }

    def get_recently_watched_shows(self, username: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get recently watched TV show episodes.

        Args:
            username: Filter for a specific user.
            limit: Maximum number of results to return.

        Returns:
            List of recently watched episodes with their show details.
        """
        logger.debug(f"Getting recently watched shows (user={username}, limit={limit})")

        try:
            # Get recently watched episodes
            if (username):
                history = self.server.history(limit=limit * 3, type='episode', username=username)
            else:
                history = self.server.history(limit=limit * 3, type='episode')

            if not history:
                return []

            # Process history entries
            results = []
            shows_seen = set()  # Track shows we've already added to avoid duplicates

            for entry in history:
                # Skip if not an episode
                if entry.type != 'episode':
                    continue

                try:
                    # Get the episode and parent show
                    episode = entry
                    show = episode.show()

                    # Skip if we've already added this show
                    if show.key in shows_seen:
                        continue

                    # Add to results and mark as seen
                    results.append({
                        'show_title': show.title,
                        'episode_title': episode.title,
                        'season': episode.seasonNumber,
                        'episode': episode.index,
                        'duration_minutes': episode.duration / 60000 if episode.duration else 0,
                        'viewed_at': entry.viewedAt,
                        'user': entry.username,
                        'year': show.year
                    })
                    shows_seen.add(show.key)

                    # Stop if we've reached the limit
                    if len(results) >= limit:
                        break

                except Exception as e:
                    logger.debug(f"Error processing history entry: {e}")

            return results

        except Exception as e:
            logger.error(f"Error getting recently watched shows: {e}")
            return []

    def get_recently_watched_movies(self, username: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get recently watched movies.

        Args:
            username: Filter for a specific user.
            limit: Maximum number of results to return.

        Returns:
            List of recently watched movies.
        """
        logger.debug(f"Getting recently watched movies (user={username}, limit={limit})")

        try:
            # Get recently watched movies
            if username:
                history = self.server.history(limit=limit, type='movie', username=username)
            else:
                history = self.server.history(limit=limit, type='movie')

            if not history:
                return []

            # Process history entries
            results = []
            movies_seen = set()  # Track movies we've already added to avoid duplicates

            for entry in history:
                # Skip if not a movie
                if entry.type != 'movie':
                    continue

                try:
                    # Skip if we've already added this movie
                    if entry.key in movies_seen:
                        continue

                    # Add to results and mark as seen
                    results.append({
                        'title': entry.title,
                        'year': entry.year,
                        'duration_minutes': entry.duration / 60000 if entry.duration else 0,
                        'viewed_at': entry.viewedAt,
                        'user': entry.username,
                        'rating': entry.rating
                    })
                    movies_seen.add(entry.key)

                    # Stop if we've reached the limit
                    if len(results) >= limit:
                        break

                except Exception as e:
                    logger.debug(f"Error processing history entry: {e}")

            return results

        except Exception as e:
            logger.error(f"Error getting recently watched movies: {e}")
            return []
