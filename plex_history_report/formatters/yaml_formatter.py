"""YAML formatter for displaying Plex History Report statistics."""

import copy
from datetime import datetime
from typing import Any, Dict, List

import yaml

from plex_history_report.formatters.base import BaseFormatter


class YamlFormatter(BaseFormatter):
    """Formatter for YAML output."""

    def _convert_datetime(self, obj: Any) -> Any:
        """Helper method to convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()

        # Handle nested dictionaries
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Round completion percentage to one decimal place
                if key == 'completion_percentage':
                    obj[key] = round(value, 1)
                else:
                    obj[key] = self._convert_datetime(value)

        # Handle nested lists/arrays
        if isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._convert_datetime(item)

        return obj

    def format_show_statistics(self, stats: List[Dict]) -> str:
        """Format show statistics as YAML.

        Args:
            stats: List of show statistics.

        Returns:
            YAML string representation of the statistics.
        """
        # Make a deep copy to avoid modifying the original data
        stats_copy = copy.deepcopy(stats)

        # Convert all datetime objects to strings recursively
        stats_copy = self._convert_datetime(stats_copy)

        data = {
            'shows': stats_copy,
            'summary': {
                'total_shows': len(stats),
                'watched_shows': sum(1 for show in stats if show['watched_episodes'] > 0),
                'total_episodes': sum(show['total_episodes'] for show in stats),
                'watched_episodes': sum(show['watched_episodes'] for show in stats),
                'total_watch_time_minutes': sum(show['total_watch_time_minutes'] for show in stats),
            }
        }

        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    def format_movie_statistics(self, stats: List[Dict]) -> str:
        """Format movie statistics as YAML.

        Args:
            stats: List of movie statistics.

        Returns:
            YAML string representation of the statistics.
        """
        # Make a deep copy to avoid modifying the original data
        stats_copy = copy.deepcopy(stats)

        # Convert all datetime objects to strings recursively
        stats_copy = self._convert_datetime(stats_copy)

        # Convert genre objects to strings if needed
        for movie in stats_copy:
            if movie.get('genres'):
                movie['genres'] = [str(g) for g in movie['genres']]

        data = {
            'movies': stats_copy,
            'summary': {
                'total_movies': len(stats),
                'watched_movies': sum(1 for movie in stats if movie['watched']),
                'total_watch_count': sum(movie['watch_count'] for movie in stats),
                'total_duration_minutes': sum(movie['duration_minutes'] for movie in stats),
                'total_watched_duration_minutes': sum(
                    movie['duration_minutes'] * movie['watch_count'] for movie in stats if movie['watched']
                ),
            }
        }

        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    def format_recently_watched(self, stats: List[Dict], media_type: str = "show") -> str:
        """Format recently watched media as YAML.

        Args:
            stats: List of recently watched media statistics.
            media_type: Type of media ("show" or "movie").

        Returns:
            YAML string representation of the recently watched media.
        """
        # Make a deep copy to avoid modifying the original data
        stats_copy = copy.deepcopy(stats)

        # Convert all datetime objects to strings recursively
        stats_copy = self._convert_datetime(stats_copy)

        # Convert genre objects to strings if needed for movies
        if media_type == "movie":
            for movie in stats_copy:
                if movie.get('genres'):
                    movie['genres'] = [str(g) for g in movie['genres']]

        data = {
            f'recently_watched_{media_type}s': stats_copy
        }

        return yaml.dump(data, sort_keys=False, default_flow_style=False)
