"""Compact formatter for displaying Plex History Report statistics in minimal format."""

from datetime import datetime
from typing import Dict, List

from plex_history_report.formatters.base import BaseFormatter


class CompactFormatter(BaseFormatter):
    """Formatter for ultra-compact output to reduce token consumption.

    This formatter produces minimal output to reduce token usage when
    using the output as input to LLMs like ChatGPT.
    """

    def format_show_statistics(self, stats: List[Dict]) -> str:
        """Format show statistics in a compact format.

        Args:
            stats: List of show statistics.

        Returns:
            Compact string representation of the statistics.
        """
        if not stats:
            return "NoShows"

        # Use short but descriptive column headers
        lines = ["Title|WatchedEps|TotalEps|WatchTime"]

        # Add rows for each show with minimal separators
        for show in stats:
            # Format watch time compactly
            hours = int(show["total_watch_time_minutes"] // 60)
            minutes = int(show["total_watch_time_minutes"] % 60)
            watch_time = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"

            # Clean title for delimiter use
            title = show["title"].replace("|", "/")

            # Create compact row
            lines.append(
                f"{title}|{show['watched_episodes']}|{show['total_episodes']}|{watch_time}"
            )

        return "\n".join(lines)

    def format_movie_statistics(self, stats: List[Dict]) -> str:
        """Format movie statistics in a compact format.

        Args:
            stats: List of movie statistics.

        Returns:
            Compact string representation of the statistics.
        """
        if not stats:
            return "NoMovies"

        # Use short but descriptive column headers
        lines = ["Title|WatchCount|LastWatched|Duration|Rating"]

        # Add rows for each movie
        for movie in stats:
            # Format last watched date compactly
            last_watched = movie["last_watched"]
            formatted_date = "-"
            if last_watched:
                # Convert to datetime and format
                if isinstance(last_watched, (int, float)):
                    last_watched = datetime.fromtimestamp(last_watched)
                formatted_date = last_watched.strftime("%y-%m-%d")  # Shorter year format

            # Format duration compactly
            hours = int(movie["duration_minutes"] // 60)
            minutes = int(movie["duration_minutes"] % 60)
            duration = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"

            # Format rating
            rating = f"{movie['rating']}" if movie["rating"] else "-"

            # Clean title for delimiter use
            title = movie["title"].replace("|", "/")

            # Create compact row
            lines.append(f"{title}|{movie['watch_count']}|{formatted_date}|{duration}|{rating}")

        return "\n".join(lines)

    def format_recently_watched(self, stats: List[Dict], media_type: str = "show") -> str:
        """Format recently watched media in a compact format.

        Args:
            stats: List of recently watched media statistics.
            media_type: Type of media ("show" or "movie").

        Returns:
            Compact string representation of the recently watched media.
        """
        if not stats:
            return f"NoRecent{media_type.title()}s"

        if media_type == "show":
            # Short but descriptive headers for shows
            lines = ["Title|LastWatched|Progress|WatchTime"]

            for show in stats:
                # Format last watched date compactly
                last_watched = show["last_watched"]
                formatted_date = "Never"
                if last_watched:
                    # Convert to datetime and format
                    if isinstance(last_watched, (int, float)):
                        last_watched = datetime.fromtimestamp(last_watched)
                    formatted_date = last_watched.strftime("%y-%m-%d")  # Shorter year format

                # Format watch time compactly
                hours = int(show["total_watch_time_minutes"] // 60)
                minutes = int(show["total_watch_time_minutes"] % 60)
                watch_time = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"

                # Format progress without percentage
                progress = f"{show['watched_episodes']}/{show['total_episodes']}"

                # Clean title for delimiter use
                title = show["title"].replace("|", "/")

                lines.append(f"{title}|{formatted_date}|{progress}|{watch_time}")
        else:  # movies
            # Short but descriptive headers for movies
            lines = ["Title|LastWatched|WatchCount|Duration"]

            for movie in stats:
                # Format last watched date compactly
                last_watched = movie["last_watched"]
                formatted_date = "Never"
                if last_watched:
                    # Convert to datetime and format
                    if isinstance(last_watched, (int, float)):
                        last_watched = datetime.fromtimestamp(last_watched)
                    formatted_date = last_watched.strftime("%y-%m-%d")  # Shorter year format

                # Format duration compactly
                hours = int(movie["duration_minutes"] // 60)
                minutes = int(movie["duration_minutes"] % 60)
                duration = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"

                # Clean title for delimiter use
                title = movie["title"].replace("|", "/")

                lines.append(f"{title}|{formatted_date}|{movie['watch_count']}|{duration}")

        return "\n".join(lines)
