"""CSV formatter for displaying Plex History Report statistics."""

import csv
import io
from datetime import datetime
from typing import Dict, List

from plex_history_report.formatters.base import BaseFormatter


class CsvFormatter(BaseFormatter):
    """Formatter for CSV output."""

    def format_show_statistics(self, stats: List[Dict]) -> str:
        """Format show statistics as CSV.

        Args:
            stats: List of show statistics.

        Returns:
            CSV string representation of the statistics.
        """
        if not stats:
            return "No TV shows found in your Plex library."

        # Use StringIO to create a CSV string
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header row
        writer.writerow(
            [
                "Title",
                "Watched Episodes",
                "Total Episodes",
                "Completion Percentage",
                "Watch Time (minutes)",
                "Year",
                "Last Watched",
            ]
        )

        # Write data rows
        for show in stats:
            last_watched = ""
            if show["last_watched"]:
                if isinstance(show["last_watched"], datetime):
                    last_watched = show["last_watched"].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    last_watched = str(show["last_watched"])

            writer.writerow(
                [
                    show["title"],
                    show["watched_episodes"],
                    show["total_episodes"],
                    f"{show['completion_percentage']:.1f}",
                    show["total_watch_time_minutes"],
                    show["year"] if show["year"] else "",
                    last_watched,
                ]
            )

        # Write summary rows
        total_shows = len(stats)
        watched_shows = sum(1 for show in stats if show["watched_episodes"] > 0)
        total_episodes = sum(show["total_episodes"] for show in stats)
        watched_episodes = sum(show["watched_episodes"] for show in stats)
        total_watch_time = sum(show["total_watch_time_minutes"] for show in stats)
        completion_percentage = (
            (watched_episodes / total_episodes * 100) if total_episodes > 0 else 0
        )

        # Add a blank line before summary
        writer.writerow([])
        writer.writerow(["Summary", "", "", "", "", "", ""])
        writer.writerow(["Total Shows", total_shows, "", "", "", "", ""])
        writer.writerow(["Watched Shows", watched_shows, "", "", "", "", ""])
        writer.writerow(["Total Episodes", total_episodes, "", "", "", "", ""])
        writer.writerow(["Watched Episodes", watched_episodes, "", "", "", "", ""])
        writer.writerow(["Overall Completion", f"{completion_percentage:.1f}%", "", "", "", "", ""])
        writer.writerow(["Total Watch Time (minutes)", total_watch_time, "", "", "", "", ""])

        return output.getvalue()

    def format_movie_statistics(self, stats: List[Dict]) -> str:
        """Format movie statistics as CSV.

        Args:
            stats: List of movie statistics.

        Returns:
            CSV string representation of the statistics.
        """
        if not stats:
            return "No movies found in your Plex library."

        # Use StringIO to create a CSV string
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header row
        writer.writerow(
            [
                "Title",
                "Year",
                "Watch Count",
                "Last Watched",
                "Duration (minutes)",
                "Watched",
                "Rating",
            ]
        )

        # Write data rows
        for movie in stats:
            last_watched = ""
            if movie["last_watched"]:
                if isinstance(movie["last_watched"], datetime):
                    last_watched = movie["last_watched"].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    last_watched = str(movie["last_watched"])

            writer.writerow(
                [
                    movie["title"],
                    movie["year"] if movie["year"] else "",
                    movie["watch_count"],
                    last_watched,
                    movie["duration_minutes"],
                    "Yes" if movie["watched"] else "No",
                    movie["rating"] if movie["rating"] else "",
                ]
            )

        # Write summary rows
        total_movies = len(stats)
        watched_movies = sum(1 for movie in stats if movie["watched"])
        watch_count = sum(movie["watch_count"] for movie in stats)
        total_duration = sum(movie["duration_minutes"] for movie in stats)
        watched_duration = sum(
            movie["duration_minutes"] * movie["watch_count"] for movie in stats if movie["watched"]
        )
        completion_percentage = (watched_movies / total_movies * 100) if total_movies > 0 else 0

        # Add a blank line before summary
        writer.writerow([])
        writer.writerow(["Summary", "", "", "", "", "", ""])
        writer.writerow(["Total Movies", total_movies, "", "", "", "", ""])
        writer.writerow(["Watched Movies", watched_movies, "", "", "", "", ""])
        writer.writerow(["Completion", f"{completion_percentage:.1f}%", "", "", "", "", ""])
        writer.writerow(["Total Watch Count", watch_count, "", "", "", "", ""])
        writer.writerow(["Total Duration (minutes)", total_duration, "", "", "", "", ""])
        writer.writerow(["Total Watch Time (minutes)", watched_duration, "", "", "", "", ""])

        return output.getvalue()

    def format_recently_watched(self, stats: List[Dict], media_type: str = "show") -> str:
        """Format recently watched media as CSV.

        Args:
            stats: List of recently watched media statistics.
            media_type: Type of media ("show" or "movie").

        Returns:
            CSV string representation of the recently watched media.
        """
        if not stats:
            return f"No recently watched {media_type}s found."

        # Use StringIO to create a CSV string
        output = io.StringIO()
        writer = csv.writer(output)

        if media_type == "show":
            # Write header row for shows
            writer.writerow(
                [
                    "Title",
                    "Last Watched",
                    "Watched Episodes",
                    "Total Episodes",
                    "Completion Percentage",
                    "Watch Time (minutes)",
                ]
            )

            # Write data rows for shows
            for show in stats:
                last_watched = ""
                if show["last_watched"]:
                    if isinstance(show["last_watched"], datetime):
                        last_watched = show["last_watched"].strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        last_watched = str(show["last_watched"])

                writer.writerow(
                    [
                        show["title"],
                        last_watched,
                        show["watched_episodes"],
                        show["total_episodes"],
                        f"{show['completion_percentage']:.1f}",
                        show["total_watch_time_minutes"],
                    ]
                )
        else:  # movies
            # Write header row for movies
            writer.writerow(["Title", "Last Watched", "Watch Count", "Duration (minutes)"])

            # Write data rows for movies
            for movie in stats:
                last_watched = ""
                if movie["last_watched"]:
                    if isinstance(movie["last_watched"], datetime):
                        last_watched = movie["last_watched"].strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        last_watched = str(movie["last_watched"])

                writer.writerow(
                    [movie["title"], last_watched, movie["watch_count"], movie["duration_minutes"]]
                )

        return output.getvalue()
