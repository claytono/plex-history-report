"""Plex client module for retrieving Plex History Report statistics."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from plexapi.exceptions import Unauthorized
from plexapi.library import LibrarySection
from plexapi.server import PlexServer
from plexapi.video import Movie, Show

from plex_history_report.utils import timing_decorator

logger = logging.getLogger(__name__)


class PlexClientError(Exception):
    """Exception raised for Plex client errors."""

    pass


class PlexClient:
    """Client for interacting with a Plex server."""

    def __init__(
        self,
        base_url: str,
        token: str,
        data_recorder: Optional[Any] = None,
    ):
        """Initialize the Plex client.

        Args:
            base_url: Base URL for the Plex server.
            token: Authentication token for the Plex server.
            data_recorder: Optional callback for recording Plex data.

        Raises:
            PlexClientError: If connection to the Plex server fails.
        """
        self.base_url = base_url
        self.token = token
        self.data_recorder = data_recorder

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
            logger.debug("Added admin user to list")

            # Add shared users (if available)
            try:
                logger.debug("Attempting to fetch Plex account users...")
                account = self.server.myPlexAccount()
                logger.debug(f"Successfully fetched Plex account: {account.title} ({account.username})")
                
                # Try to add the server owner (if different from admin)
                if account.username and account.username.strip() and account.username != "admin":
                    logger.debug(f"Adding server owner: {account.username}")
                    users.append(account.username)
                
                # Get all shared users
                all_users = account.users()
                logger.debug(f"Found {len(all_users)} shared users from Plex API")
                
                for user in all_users:
                    # Try multiple attributes to get the user's identity
                    user_id = None
                    
                    # First try username
                    if hasattr(user, 'username') and user.username and user.username.strip():
                        user_id = user.username
                        logger.debug(f"Adding user with username: {user_id}")
                    # Then try title
                    elif hasattr(user, 'title') and user.title and user.title.strip():
                        user_id = user.title
                        logger.debug(f"Adding user with title: {user_id}")
                    # Then try id or any other identifier
                    elif hasattr(user, 'id') and user.id:
                        user_id = f"user_{user.id}"
                        logger.debug(f"Adding user with ID: {user_id}")
                    # Try name
                    elif hasattr(user, 'name') and user.name and user.name.strip():
                        user_id = user.name
                        logger.debug(f"Adding user with name: {user_id}")
                    
                    # Add the user if we found a valid identifier
                    if user_id:
                        users.append(user_id)
                    else:
                        # Get object representation to show all attributes
                        try:
                            logger.debug(f"User info: {vars(user)}")
                        except:
                            pass
                        logger.debug(f"Skipping user with no valid identifier: {user}")
                        
                        # Extract title from string representation as last resort
                        user_str = str(user)
                        if ':' in user_str:
                            parts = user_str.split(':')
                            if len(parts) >= 3:
                                potential_name = parts[2].strip('>')
                                if potential_name:
                                    logger.debug(f"Extracted name '{potential_name}' from {user_str}")
                                    users.append(potential_name)
                        
                # Check for managed/home users if available
                try:
                    home_users = account.homeUsers() if hasattr(account, 'homeUsers') else []
                    logger.debug(f"Found {len(home_users)} home users")
                    
                    for user in home_users:
                        if hasattr(user, 'title') and user.title and user.title.strip():
                            logger.debug(f"Adding home user: {user.title}")
                            users.append(user.title)
                except Exception as e:
                    logger.debug(f"Error fetching home users: {e}")
                    
            except Unauthorized:
                logger.warning(
                    "Unauthorized to access myPlex account users. "
                    "This may be expected if using a managed user token."
                )
            except Exception as e:
                logger.warning(f"Error retrieving myPlex account users: {e}")
                return []  # Return empty list for general myPlex account exceptions

            # Return only unique non-empty usernames
            unique_users = sorted(set(filter(None, users)))
            logger.debug(f"Final user list ({len(unique_users)} users): {unique_users}")
            return unique_users
        except Exception as e:
            logger.warning(f"Failed to get user list: {e}")
            return []  # Return empty list for general exceptions

    @timing_decorator
    def get_library_sections(self) -> List[LibrarySection]:
        """Get all library sections from the Plex server.

        Returns:
            List of library sections.
        """
        return self.server.library.sections()

    @timing_decorator
    def get_all_show_statistics(
        self,
        username: Optional[str] = None,
        include_unwatched: bool = False,
        partially_watched_only: bool = False,
        sort_by: str = "title",
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
        logger.debug(
            f"Getting show statistics (user={username}, include_unwatched={include_unwatched}, "
            f"partially_watched_only={partially_watched_only})"
        )

        # Get all TV library sections
        tv_sections = [
            section for section in self.server.library.sections() if section.type == "show"
        ]

        if not tv_sections:
            logger.warning("No TV library sections found")
            return []

        # Fetch all shows from all TV sections with minimal fields
        all_shows = []
        for section in tv_sections:
            # Get all shows in this section
            shows = section.all()
            all_shows.extend(shows)

        # Record data if a recorder is provided
        if self.data_recorder:
            self.data_recorder.record_data("all_shows", all_shows)

        # Process each show
        show_stats = []
        for show in all_shows:
            stat = self._get_show_statistics(show, username)

            # Handle filtering conditions
            if not include_unwatched and stat["watched_episodes"] == 0:
                # Skip unwatched shows
                continue

            # Only keep partially watched shows if requested
            if partially_watched_only and not (0 < stat["completion_percentage"] < 100):
                # Skip fully watched or completely unwatched shows
                continue

            show_stats.append(stat)

        # Sort results
        if sort_by == "title":
            show_stats.sort(key=lambda x: x["title"].lower())
        elif sort_by == "watched_episodes":
            show_stats.sort(key=lambda x: x["watched_episodes"], reverse=True)
        elif sort_by == "completion_percentage":
            show_stats.sort(key=lambda x: x["completion_percentage"], reverse=True)
        elif sort_by == "last_watched":
            # Debug the last_watched values to understand what's happening
            for show in show_stats:
                logger.debug(f"Show '{show['title']}' has last_watched: {show['last_watched']}")

            # Sort by last_watched, placing None values at the end
            # Use a dummy date in the past for entries with None
            def last_watched_key(item):
                if item["last_watched"] is None:
                    return datetime(1900, 1, 1)  # Very old date for None values
                return item["last_watched"]

            # First sort by title for stable sorting of equal dates
            show_stats.sort(key=lambda x: x["title"].lower())
            # Then sort by last_watched date in descending order (newest first)
            show_stats.sort(key=last_watched_key, reverse=True)

            # Debug the sorted order
            logger.debug("Shows sorted by last_watched:")
            for show in show_stats:
                logger.debug(f"  {show['title']}: {show['last_watched']}")
        elif sort_by == "year":
            # Sort by year, placing None values at the end
            show_stats.sort(key=lambda x: 0 if x["year"] is None else x["year"], reverse=True)
        elif sort_by == "rating":
            # Sort by rating, placing None values at the end
            show_stats.sort(key=lambda x: 0 if x["rating"] is None else x["rating"], reverse=True)

        return show_stats

    @timing_decorator
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

            # Fetch recent history once for the show instead of per episode
            show_history = None
            if username:
                try:
                    # Get the most recent 50 history entries for the show
                    # This is more efficient than getting history for each episode
                    show_history = show.history(username=username, maxresults=50)
                except Exception as e:
                    logger.debug(f"Error getting show history: {e}")

            # Process each episode
            for episode in episodes:
                # Check if this episode has been watched by the specified user
                watched = False

                if username:
                    # Use viewCount property or isWatched first (most efficient)
                    if hasattr(episode, "viewCount") and episode.viewCount is not None:
                        watched = episode.viewCount > 0
                    elif hasattr(episode, "isWatched"):
                        watched = episode.isWatched
                    else:
                        # Last resort: check episode in show history
                        if show_history:
                            for entry in show_history:
                                if (
                                    hasattr(entry, "grandparentRatingKey")
                                    and hasattr(episode, "grandparentRatingKey")
                                    and hasattr(entry, "index")
                                    and hasattr(episode, "index")
                                    and entry.grandparentRatingKey == episode.grandparentRatingKey
                                    and entry.index == episode.index
                                ):
                                    watched = True
                                    # Update last watched date from history if needed
                                    if entry.viewedAt and (
                                        last_watched_date is None
                                        or entry.viewedAt > last_watched_date
                                    ):
                                        last_watched_date = entry.viewedAt
                                    break

                    # Add watch time to total when episode is watched
                    if watched and episode.duration:
                        total_watch_time += episode.duration / 60000  # Convert ms to minutes
                else:
                    # Check if episode is marked as watched globally
                    if hasattr(episode, "viewCount") and episode.viewCount is not None:
                        watched = episode.viewCount > 0
                    else:
                        watched = episode.isWatched if hasattr(episode, "isWatched") else False

                    # Add watch time to total when episode is marked as watched
                    if watched and episode.duration:
                        total_watch_time += episode.duration / 60000  # Convert ms to minutes

                if watched:
                    watched_episodes += 1

            # If we didn't find a last watched date from episode history, try to get it from show history
            if last_watched_date is None and show_history:
                for entry in show_history:
                    if entry.viewedAt and (
                        last_watched_date is None or entry.viewedAt > last_watched_date
                    ):
                        last_watched_date = entry.viewedAt

            # Calculate completion percentage
            completion_percentage = 0
            if total_episodes > 0:
                completion_percentage = (watched_episodes / total_episodes) * 100

            # Build the statistics dictionary
            return {
                "title": show.title,
                "total_episodes": total_episodes,
                "watched_episodes": watched_episodes,
                "unwatched_episodes": total_episodes - watched_episodes,
                "completion_percentage": completion_percentage,
                "total_watch_time_minutes": total_watch_time,
                "last_watched": last_watched_date,
                "year": show.year,
                "rating": show.rating,
                "key": show.key,
            }

        except Exception as e:
            logger.error(f"Error processing show {show.title}: {e}")
            # Return a minimal statistics dictionary on error
            return {
                "title": show.title,
                "total_episodes": 0,
                "watched_episodes": 0,
                "unwatched_episodes": 0,
                "completion_percentage": 0,
                "total_watch_time_minutes": 0,
                "last_watched": None,
                "year": None,
                "rating": None,
                "key": show.key,
                "error": str(e),
            }

    @timing_decorator
    def get_all_movie_statistics(
        self,
        username: Optional[str] = None,
        include_unwatched: bool = False,
        partially_watched_only: bool = False,
        sort_by: str = "title",
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
        logger.debug(
            f"Getting movie statistics (user={username}, include_unwatched={include_unwatched}, "
            f"partially_watched_only={partially_watched_only})"
        )

        # Get all movie library sections
        movie_sections = [
            section for section in self.server.library.sections() if section.type == "movie"
        ]

        if not movie_sections:
            logger.warning("No movie library sections found")
            return []

        # Fetch all movies from all movie sections
        all_movies = []
        for section in movie_sections:
            # Get all movies in this section
            movies = section.all()
            all_movies.extend(movies)

        # Record data if a recorder is provided
        if self.data_recorder:
            self.data_recorder.record_data("all_movies", all_movies)

        # Process each movie
        movie_stats = []
        for movie in all_movies:
            stat = self._get_movie_statistics(movie, username)

            # Apply filtering based on watch status
            if not include_unwatched and not stat["watched"]:
                # Skip unwatched movies
                continue

            # Filter for partially watched movies if requested
            if partially_watched_only and not (0 < stat["completion_percentage"] < 100):
                # Skip fully watched or completely unwatched movies
                continue

            movie_stats.append(stat)

        # Sort results
        if sort_by == "title":
            movie_stats.sort(key=lambda x: x["title"].lower())
        elif sort_by == "year":
            movie_stats.sort(key=lambda x: 0 if x["year"] is None else x["year"], reverse=True)
        elif sort_by == "last_watched":
            movie_stats.sort(
                key=lambda x: datetime.min if x["last_watched"] is None else x["last_watched"],
                reverse=True,
            )
        elif sort_by == "watch_count":
            movie_stats.sort(key=lambda x: x["watch_count"], reverse=True)
        elif sort_by == "rating":
            movie_stats.sort(key=lambda x: 0 if x["rating"] is None else x["rating"], reverse=True)
        elif sort_by == "duration_minutes":
            movie_stats.sort(key=lambda x: x["duration_minutes"], reverse=True)

        return movie_stats

    @timing_decorator
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

            # Initialize statistics
            watch_count = 0
            last_watched_date = None
            view_offset = 0
            watched = False

            # Convert duration from milliseconds to minutes
            duration_minutes = movie.duration / 60000 if movie.duration else 0

            # Get view offset if available (for partial watch tracking)
            if hasattr(movie, "viewOffset"):
                view_offset = movie.viewOffset
                if view_offset > 0:
                    logger.debug(
                        f"Movie '{movie.title}' has viewOffset: {view_offset} out of {movie.duration} "
                        f"({(view_offset / movie.duration * 100):.1f}% watched)"
                    )

            # Most efficient way: first check viewCount and isWatched properties
            if hasattr(movie, "viewCount") and movie.viewCount is not None:
                watch_count = movie.viewCount
                watched = watch_count > 0
            else:
                watched = movie.isWatched if hasattr(movie, "isWatched") else False
                # If it's marked as watched but we don't have a count, set to at least 1
                if watched:
                    watch_count = 1

            # Always attempt to get last watched date for watched movies
            # This is needed even if no specific username is provided
            if watched:
                if username:
                    # Minimal history retrieval - just enough for last watched date
                    try:
                        # Try with maxresults parameter first, but handle case where it's not supported
                        try:
                            history = movie.history(username=username, maxresults=5)
                        except TypeError:
                            # Fall back to calling without maxresults for test compatibility
                            history = movie.history(username=username)

                        if history:
                            for entry in history:
                                if entry.viewedAt and (
                                    last_watched_date is None or entry.viewedAt > last_watched_date
                                ):
                                    last_watched_date = entry.viewedAt
                    except Exception as e:
                        logger.debug(f"Error getting history for last watched date: {e}")
                else:
                    # If no username provided, get global watch history
                    try:
                        # Try with maxresults parameter first, but handle case where it's not supported
                        try:
                            history = movie.history(maxresults=5)
                        except TypeError:
                            # Fall back to calling without maxresults for test compatibility
                            history = movie.history()

                        if history:
                            for entry in history:
                                if entry.viewedAt and (
                                    last_watched_date is None or entry.viewedAt > last_watched_date
                                ):
                                    last_watched_date = entry.viewedAt
                    except Exception as e:
                        logger.debug(f"Error getting global history for last watched date: {e}")

            # Calculate completion percentage
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
                "title": movie.title,
                "year": movie.year,
                "duration_minutes": duration_minutes,
                "watched": watched,
                "watch_count": watch_count,
                "last_watched": last_watched_date,
                "rating": movie.rating,
                "view_offset": view_offset,
                "completion_percentage": completion_percentage,
                "key": movie.key,
            }

        except Exception as e:
            logger.error(f"Error processing movie {movie.title}: {e}")
            # Return a minimal statistics dictionary on error
            return {
                "title": movie.title,
                "year": None,
                "duration_minutes": 0,
                "watched": False,
                "watch_count": 0,
                "last_watched": None,
                "rating": None,
                "view_offset": 0,
                "completion_percentage": 0,
                "key": movie.key,
                "error": str(e),
            }

    def get_recently_watched_shows(
        self, username: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
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
            # Request 3x the limit to account for duplicates that will be filtered
            query_limit = limit * 3

            if username:
                history = self.server.history(
                    limit=query_limit,
                    type="episode",
                    username=username,
                )
            else:
                history = self.server.history(limit=query_limit, type="episode")

            if not history:
                return []

            # Record data if a recorder is provided
            if self.data_recorder:
                self.data_recorder.record_data("recently_watched_shows", history)

            # Process history entries
            results = []
            shows_seen = set()  # Track shows we've already added to avoid duplicates

            for entry in history:
                # Skip if not an episode
                if entry.type != "episode":
                    continue

                try:
                    # Get the episode and parent show
                    episode = entry
                    show = episode.show()

                    # Skip if we've already added this show
                    if show.key in shows_seen:
                        continue

                    # Add to results and mark as seen
                    results.append(
                        {
                            "show_title": show.title,
                            "episode_title": episode.title,
                            "season": episode.seasonNumber,
                            "episode": episode.index,
                            "duration_minutes": episode.duration / 60000 if episode.duration else 0,
                            "viewed_at": entry.viewedAt,
                            "user": entry.username,
                            "year": show.year,
                        }
                    )
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

    def get_recently_watched_movies(
        self, username: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
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
                history = self.server.history(limit=limit, type="movie", username=username)
            else:
                history = self.server.history(limit=limit, type="movie")

            if not history:
                return []

            # Record data if a recorder is provided
            if self.data_recorder:
                self.data_recorder.record_data("recently_watched_movies", history)

            # Process history entries
            results = []
            movies_seen = set()  # Track movies we've already added to avoid duplicates

            for entry in history:
                # Skip if not a movie
                if entry.type != "movie":
                    continue

                try:
                    # Skip if we've already added this movie
                    if entry.key in movies_seen:
                        continue

                    # Make sure we have valid duration data
                    duration = 0
                    if hasattr(entry, "duration") and entry.duration:
                        duration = entry.duration / 60000  # Convert ms to minutes

                    # Check if we have watch history data
                    watch_count = 0
                    try:
                        # Use viewCount property if available (much more efficient)
                        if hasattr(entry, "viewCount") and entry.viewCount is not None:
                            watch_count = entry.viewCount
                        else:
                            # Fall back to history if viewCount not available
                            movie_history = entry.history()
                            watch_count = len(movie_history)
                    except Exception as e:
                        logger.debug(
                            f"Error getting detailed history for movie '{entry.title}': {e}"
                        )
                        # If we can't get history, at least we know it was watched once
                        watch_count = 1

                    # Add to results and mark as seen
                    results.append(
                        {
                            "title": entry.title,
                            "year": entry.year,
                            "duration_minutes": duration,
                            "viewed_at": entry.viewedAt,
                            "user": entry.username,
                            "rating": entry.rating,
                            "watch_count": watch_count,
                        }
                    )
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
