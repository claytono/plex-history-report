"""Markdown formatter for displaying Plex History Report statistics."""

from datetime import datetime
from typing import Dict, List

from plex_history_report.formatters.base import BaseFormatter


class MarkdownFormatter(BaseFormatter):
    """Formatter for Markdown output."""

    def format_show_statistics(self, stats: List[Dict]) -> str:
        """Format show statistics as Markdown.

        Args:
            stats: List of show statistics.

        Returns:
            Markdown string representation of the statistics.
        """
        if not stats:
            return "# TV Show Statistics\n\nNo TV shows found in your Plex library.\n"

        # Generate the title and header row
        md = "# TV Show Statistics\n\n"
        md += "| Title | Watched | Total | Completion | Watch Time |\n"
        md += "|-------|---------|-------|------------|------------|\n"

        # Add rows for each show
        for show in stats:
            # Format watch time as hours and minutes
            hours = int(show["total_watch_time_minutes"] // 60)
            minutes = int(show["total_watch_time_minutes"] % 60)
            watch_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

            # Format completion percentage
            completion = f"{show['completion_percentage']:.1f}%"

            # Clean title for markdown table
            title = show["title"].replace("|", "\\|")

            md += f"| {title} | {show['watched_episodes']} | {show['total_episodes']} | {completion} | {watch_time} |\n"

        # Add summary section
        total_shows = len(stats)
        watched_shows = sum(1 for show in stats if show["watched_episodes"] > 0)
        total_episodes = sum(show["total_episodes"] for show in stats)
        watched_episodes = sum(show["watched_episodes"] for show in stats)
        total_watch_time = sum(show["total_watch_time_minutes"] for show in stats)
        hours = int(total_watch_time // 60)
        minutes = int(total_watch_time % 60)
        completion_percentage = (
            (watched_episodes / total_episodes * 100) if total_episodes > 0 else 0
        )

        md += "\n## Summary\n\n"
        md += f"- **Total Shows:** {total_shows}\n"
        md += f"- **Watched Shows:** {watched_shows}\n"
        md += f"- **Total Episodes:** {total_episodes}\n"
        md += f"- **Watched Episodes:** {watched_episodes}\n"
        md += f"- **Overall Completion:** {completion_percentage:.1f}%\n"
        md += f"- **Total Watch Time:** {hours} hours, {minutes} minutes\n"

        return md

    def format_movie_statistics(self, stats: List[Dict]) -> str:
        """Format movie statistics as Markdown.

        Args:
            stats: List of movie statistics.

        Returns:
            Markdown string representation of the statistics.
        """
        if not stats:
            return "# Movie Statistics\n\nNo movies found in your Plex library.\n"

        # Generate the title and header row
        md = "# Movie Statistics\n\n"
        md += "| Title | Watch Count | Last Watched | Duration | Rating |\n"
        md += "|-------|-------------|--------------|----------|--------|\n"

        # Add rows for each movie
        for movie in stats:
            # Format last watched date
            last_watched = movie["last_watched"]
            formatted_date = "Never"
            if last_watched:
                # Convert to datetime and format
                if isinstance(last_watched, (int, float)):
                    last_watched = datetime.fromtimestamp(last_watched)
                formatted_date = last_watched.strftime("%Y-%m-%d")

            # Format duration as hours and minutes
            hours = int(movie["duration_minutes"] // 60)
            minutes = int(movie["duration_minutes"] % 60)
            duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

            # Format rating
            rating = f"{movie['rating']}" if movie["rating"] else "-"

            # Clean title for markdown table
            title = movie["title"].replace("|", "\\|")

            md += (
                f"| {title} | {movie['watch_count']} | {formatted_date} | {duration} | {rating} |\n"
            )

        # Add summary section
        total_movies = len(stats)
        watched_movies = sum(1 for movie in stats if movie["watched"])
        watch_count = sum(movie["watch_count"] for movie in stats)
        total_duration = sum(movie["duration_minutes"] for movie in stats)
        watched_duration = sum(
            movie["duration_minutes"] * movie["watch_count"] for movie in stats if movie["watched"]
        )
        total_hours = int(total_duration // 60)
        total_minutes = int(total_duration % 60)
        watched_hours = int(watched_duration // 60)
        watched_minutes = int(watched_duration % 60)
        completion_percentage = (watched_movies / total_movies * 100) if total_movies > 0 else 0

        md += "\n## Summary\n\n"
        md += f"- **Total Movies:** {total_movies}\n"
        md += f"- **Watched Movies:** {watched_movies}\n"
        md += f"- **Completion:** {completion_percentage:.1f}%\n"
        md += f"- **Total Watch Count:** {watch_count}\n"
        md += f"- **Total Duration:** {total_hours} hours, {total_minutes} minutes\n"
        md += f"- **Total Watch Time:** {watched_hours} hours, {watched_minutes} minutes\n"

        return md

    def format_recently_watched(self, stats: List[Dict], media_type: str = "show") -> str:
        """Format recently watched media as Markdown.

        Args:
            stats: List of recently watched media statistics.
            media_type: Type of media ("show" or "movie").

        Returns:
            Markdown string representation of the recently watched media.
        """
        if not stats:
            return f"# Recently Watched {media_type.title()}s\n\nNo recently watched {media_type}s found.\n"

        md = f"# Recently Watched {media_type.title()}s\n\n"

        if media_type == "show":
            md += "| Title | Last Watched | Progress | Watch Time |\n"
            md += "|-------|--------------|----------|------------|\n"

            for show in stats:
                # Format last watched date
                last_watched = show["last_watched"]
                formatted_date = "Never"
                if last_watched:
                    if isinstance(last_watched, (int, float)):
                        last_watched = datetime.fromtimestamp(last_watched)
                    formatted_date = last_watched.strftime("%Y-%m-%d %H:%M")

                # Format watch time as hours and minutes
                hours = int(show["total_watch_time_minutes"] // 60)
                minutes = int(show["total_watch_time_minutes"] % 60)
                watch_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

                # Format completion percentage
                completion = f"{show['watched_episodes']}/{show['total_episodes']} ({show['completion_percentage']:.1f}%)"

                # Clean title for markdown table
                title = show["title"].replace("|", "\\|")

                md += f"| {title} | {formatted_date} | {completion} | {watch_time} |\n"
        else:  # movies
            md += "| Title | Last Watched | Watch Count | Duration |\n"
            md += "|-------|--------------|-------------|----------|\n"

            for movie in stats:
                # Format last watched date
                last_watched = movie["last_watched"]
                formatted_date = "Never"
                if last_watched:
                    if isinstance(last_watched, (int, float)):
                        last_watched = datetime.fromtimestamp(last_watched)
                    formatted_date = last_watched.strftime("%Y-%m-%d %H:%M")

                # Format duration as hours and minutes
                hours = int(movie["duration_minutes"] // 60)
                minutes = int(movie["duration_minutes"] % 60)
                duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

                # Clean title for markdown table
                title = movie["title"].replace("|", "\\|")

                md += f"| {title} | {formatted_date} | {movie['watch_count']} | {duration} |\n"

        return md
