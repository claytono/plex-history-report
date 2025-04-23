"""Formatters for displaying Plex statistics.

This module provides various formatters for displaying Plex statistics
in different formats like text tables, JSON, etc.
"""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Dict, List

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)


class BaseFormatter:
    """Base class for formatters."""

    def format_show_statistics(self, stats: List[Dict]) -> str:
        """Format show statistics.

        Args:
            stats: List of show statistics.

        Returns:
            Formatted string representation of the statistics.
        """
        raise NotImplementedError()

    def format_movie_statistics(self, stats: List[Dict]) -> str:
        """Format movie statistics.

        Args:
            stats: List of movie statistics.

        Returns:
            Formatted string representation of the statistics.
        """
        raise NotImplementedError()

    def format_recently_watched(self, stats: List[Dict], media_type: str = "show") -> str:
        """Format recently watched media.

        Args:
            stats: List of recently watched media statistics.
            media_type: Type of media ("show" or "movie").

        Returns:
            Formatted string representation of the recently watched media.
        """
        raise NotImplementedError()


class RichFormatter(BaseFormatter):
    """Formatter using Rich for pretty console output."""

    def __init__(self):
        """Initialize the Rich formatter."""
        self.console = Console()

    def format_show_statistics(self, stats: List[Dict]) -> None:
        """Format show statistics using Rich tables.

        Args:
            stats: List of show statistics.
        """
        if not stats:
            self.console.print(Panel("No TV shows found in your Plex library",
                                     title="TV Show Statistics",
                                     border_style="yellow"))
            return

        # Create a table for show statistics
        table = Table(title="TV Show Statistics")
        table.add_column("Title", style="cyan", no_wrap=True)
        table.add_column("Watched", justify="right", style="green")
        table.add_column("Total", justify="right", style="blue")
        table.add_column("Completion", justify="right", style="magenta")
        table.add_column("Watch Time", justify="right", style="yellow")

        # Add rows for each show
        for show in stats:
            # Format watch time as hours and minutes
            hours = int(show['total_watch_time_minutes'] // 60)
            minutes = int(show['total_watch_time_minutes'] % 60)
            watch_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

            # Format completion percentage, ensuring it's rounded to 1 decimal place
            completion = f"{show['completion_percentage']:.1f}%"

            table.add_row(
                show['title'],
                str(show['watched_episodes']),
                str(show['total_episodes']),
                completion,
                watch_time
            )

        self.console.print(table)

    def format_movie_statistics(self, stats: List[Dict]) -> None:
        """Format movie statistics using Rich tables.

        Args:
            stats: List of movie statistics.
        """
        if not stats:
            self.console.print(Panel("No movies found in your Plex library",
                                     title="Movie Statistics",
                                     border_style="yellow"))
            return

        # Create a table for movie statistics
        table = Table(title="Movie Statistics")
        table.add_column("Title", style="cyan", width=40)  # Limit title width to prevent overflow
        table.add_column("Watch Count", justify="right", style="green", width=12)
        table.add_column("Last Watched", justify="right", style="blue", width=16)
        table.add_column("Duration", justify="right", style="magenta", width=10)
        table.add_column("Rating", justify="right", style="yellow", width=8)

        # Add rows for each movie
        for movie in stats:
            # Format last watched date
            last_watched = movie['last_watched']
            formatted_date = "Never"
            if last_watched:
                # Convert to datetime and format
                if isinstance(last_watched, (int, float)):
                    last_watched = datetime.fromtimestamp(last_watched)
                formatted_date = last_watched.strftime("%Y-%m-%d")  # Shortened date format

            # Format duration as hours and minutes
            hours = int(movie['duration_minutes'] // 60)
            minutes = int(movie['duration_minutes'] % 60)
            duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

            # Format rating
            rating = f"{movie['rating']}" if movie['rating'] else "-"

            table.add_row(
                movie['title'],
                str(movie['watch_count']),
                formatted_date,
                duration,
                rating
            )

        self.console.print(table)

    def format_recently_watched(self, stats: List[Dict], media_type: str = "show") -> None:
        """Format recently watched media using Rich tables.

        Args:
            stats: List of recently watched media statistics.
            media_type: Type of media ("show" or "movie").
        """
        if not stats:
            self.console.print(Panel(f"No recently watched {media_type}s found",
                                     title=f"Recently Watched {media_type.title()}s",
                                     border_style="yellow"))
            return

        # Create a table for recently watched media
        table = Table(title=f"Recently Watched {media_type.title()}s")

        if (media_type == "show"):
            table.add_column("Title", style="cyan", no_wrap=True)
            table.add_column("Last Watched", justify="right", style="green")
            table.add_column("Progress", justify="right", style="magenta")
            table.add_column("Watch Time", justify="right", style="yellow")

            # Add rows for each show
            for show in stats:
                # Format last watched date
                last_watched = show['last_watched']
                formatted_date = "Never"
                if last_watched:
                    # Convert to datetime and format
                    if isinstance(last_watched, (int, float)):
                        last_watched = datetime.fromtimestamp(last_watched)
                    formatted_date = last_watched.strftime("%Y-%m-%d %H:%M")

                # Format watch time as hours and minutes
                hours = int(show['total_watch_time_minutes'] // 60)
                minutes = int(show['total_watch_time_minutes'] % 60)
                watch_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

                # Format completion percentage
                completion = f"{show['watched_episodes']}/{show['total_episodes']} ({show['completion_percentage']:.1f}%)"

                table.add_row(
                    show['title'],
                    formatted_date,
                    completion,
                    watch_time
                )
        else:  # movies
            table.add_column("Title", style="cyan", no_wrap=True)
            table.add_column("Last Watched", justify="right", style="green")
            table.add_column("Watch Count", justify="right", style="magenta")
            table.add_column("Duration", justify="right", style="yellow")

            # Add rows for each movie
            for movie in stats:
                # Format last watched date
                last_watched = movie['last_watched']
                formatted_date = "Never"
                if last_watched:
                    # Convert to datetime and format
                    if isinstance(last_watched, (int, float)):
                        last_watched = datetime.fromtimestamp(last_watched)
                    formatted_date = last_watched.strftime("%Y-%m-%d %H:%M")

                # Format duration as hours and minutes
                hours = int(movie['duration_minutes'] // 60)
                minutes = int(movie['duration_minutes'] % 60)
                duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

                table.add_row(
                    movie['title'],
                    formatted_date,
                    str(movie['watch_count']),
                    duration
                )

        self.console.print(table)

    def format_summary(self, stats: List[Dict], media_type: str = "show") -> None:
        """Format summary statistics.

        Args:
            stats: List of statistics.
            media_type: Type of media ("show" or "movie").
        """
        if not stats:
            return

        if media_type == "show":
            # Calculate show summary statistics
            total_shows = len(stats)
            watched_shows = sum(1 for show in stats if show['watched_episodes'] > 0)
            total_episodes = sum(show['total_episodes'] for show in stats)
            watched_episodes = sum(show['watched_episodes'] for show in stats)
            total_watch_time = sum(show['total_watch_time_minutes'] for show in stats)

            # Format watch time
            hours = int(total_watch_time // 60)
            minutes = int(total_watch_time % 60)

            # Calculate overall completion percentage, rounded to 1 decimal place
            completion_percentage = (watched_episodes / total_episodes * 100) if total_episodes > 0 else 0

            # Create a summary panel
            summary = Panel(
                f"Total Shows: {total_shows}\n"
                f"Watched Shows: {watched_shows}\n"
                f"Total Episodes: {total_episodes}\n"
                f"Watched Episodes: {watched_episodes}\n"
                f"Overall Completion: {completion_percentage:.1f}%\n"
                f"Total Watch Time: {hours} hours, {minutes} minutes",
                title="TV Show Summary",
                border_style="green"
            )
        else:  # movies
            # Calculate movie summary statistics
            total_movies = len(stats)
            watched_movies = sum(1 for movie in stats if movie['watched'])
            watch_count = sum(movie['watch_count'] for movie in stats)
            total_duration = sum(movie['duration_minutes'] for movie in stats)
            watched_duration = sum(movie['duration_minutes'] * movie['watch_count'] for movie in stats if movie['watched'])

            # Format durations
            total_hours = int(total_duration // 60)
            total_minutes = int(total_duration % 60)
            watched_hours = int(watched_duration // 60)
            watched_minutes = int(watched_duration % 60)

            # Calculate completion percentage, rounded to 1 decimal place
            completion_percentage = (watched_movies / total_movies * 100) if total_movies > 0 else 0

            # Create a summary panel
            summary = Panel(
                f"Total Movies: {total_movies}\n"
                f"Watched Movies: {watched_movies}\n"
                f"Completion: {completion_percentage:.1f}%\n"
                f"Total Watch Count: {watch_count}\n"
                f"Total Duration: {total_hours} hours, {total_minutes} minutes\n"
                f"Total Watch Time: {watched_hours} hours, {watched_minutes} minutes",
                title="Movie Summary",
                border_style="green"
            )

        self.console.print(summary)


class JsonFormatter(BaseFormatter):
    """Formatter for JSON output."""

    def _convert_datetime(self, obj):
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
        """Format show statistics as JSON.

        Args:
            stats: List of show statistics.

        Returns:
            JSON string representation of the statistics.
        """
        # Make a deep copy to avoid modifying the original data
        import copy
        stats_copy = copy.deepcopy(stats)

        # Convert all datetime objects to strings recursively
        stats_copy = self._convert_datetime(stats_copy)

        return json.dumps({
            'shows': stats_copy,
            'total_shows': len(stats),
            'watched_shows': sum(1 for show in stats if show['watched_episodes'] > 0),
            'total_episodes': sum(show['total_episodes'] for show in stats),
            'watched_episodes': sum(show['watched_episodes'] for show in stats),
            'total_watch_time_minutes': sum(show['total_watch_time_minutes'] for show in stats),
        }, indent=2)

    def format_movie_statistics(self, stats: List[Dict]) -> str:
        """Format movie statistics as JSON.

        Args:
            stats: List of movie statistics.

        Returns:
            JSON string representation of the statistics.
        """
        # Make a deep copy to avoid modifying the original data
        import copy
        stats_copy = copy.deepcopy(stats)

        # Convert all datetime objects to strings recursively
        stats_copy = self._convert_datetime(stats_copy)

        # Convert genre objects to strings if needed
        for movie in stats_copy:
            if movie.get('genres'):
                movie['genres'] = [str(g) for g in movie['genres']]

        return json.dumps({
            'movies': stats_copy,
            'total_movies': len(stats),
            'watched_movies': sum(1 for movie in stats if movie['watched']),
            'total_watch_count': sum(movie['watch_count'] for movie in stats),
            'total_duration_minutes': sum(movie['duration_minutes'] for movie in stats),
        }, indent=2)

    def format_recently_watched(self, stats: List[Dict], media_type: str = "show") -> str:
        """Format recently watched media as JSON.

        Args:
            stats: List of recently watched media statistics.
            media_type: Type of media ("show" or "movie").

        Returns:
            JSON string representation of the recently watched media.
        """
        # Make a deep copy to avoid modifying the original data
        import copy
        stats_copy = copy.deepcopy(stats)

        # Convert all datetime objects to strings recursively
        stats_copy = self._convert_datetime(stats_copy)

        # Convert genre objects to strings if needed for movies
        if media_type == "movie":
            for movie in stats_copy:
                if movie.get('genres'):
                    movie['genres'] = [str(g) for g in movie['genres']]

        return json.dumps({
            f'recently_watched_{media_type}s': stats_copy,
        }, indent=2)


class YamlFormatter(BaseFormatter):
    """Formatter for YAML output."""

    def _convert_datetime(self, obj):
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
        import copy
        stats_copy = copy.deepcopy(stats)

        # Convert all datetime objects to strings recursively
        stats_copy = self._convert_datetime(stats_copy)

        data = {
            'shows': stats_copy,
            'total_shows': len(stats),
            'watched_shows': sum(1 for show in stats if show['watched_episodes'] > 0),
            'total_episodes': sum(show['total_episodes'] for show in stats),
            'watched_episodes': sum(show['watched_episodes'] for show in stats),
            'total_watch_time_minutes': sum(show['total_watch_time_minutes'] for show in stats),
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
        import copy
        stats_copy = copy.deepcopy(stats)

        # Convert all datetime objects to strings recursively
        stats_copy = self._convert_datetime(stats_copy)

        # Convert genre objects to strings if needed (this would be redundant with the recursive conversion)
        for movie in stats_copy:
            if movie.get('genres'):
                movie['genres'] = [str(g) for g in movie['genres']]

        data = {
            'movies': stats_copy,
            'total_movies': len(stats),
            'watched_movies': sum(1 for movie in stats if movie['watched']),
            'total_watch_count': sum(movie['watch_count'] for movie in stats),
            'total_duration_minutes': sum(movie['duration_minutes'] for movie in stats),
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
        import copy
        stats_copy = copy.deepcopy(stats)

        # Convert all datetime objects to strings recursively
        stats_copy = self._convert_datetime(stats_copy)

        # Convert genre objects to strings if needed for movies (this would be redundant with the recursive conversion)
        if media_type == "movie":
            for movie in stats_copy:
                if movie.get('genres'):
                    movie['genres'] = [str(g) for g in movie['genres']]

        data = {
            f'recently_watched_{media_type}s': stats_copy
        }

        return yaml.dump(data, sort_keys=False, default_flow_style=False)


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
            hours = int(show['total_watch_time_minutes'] // 60)
            minutes = int(show['total_watch_time_minutes'] % 60)
            watch_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

            # Format completion percentage
            completion = f"{show['completion_percentage']:.1f}%"

            # Clean title for markdown table
            title = show['title'].replace('|', '\\|')

            md += f"| {title} | {show['watched_episodes']} | {show['total_episodes']} | {completion} | {watch_time} |\n"

        # Add summary section
        total_shows = len(stats)
        watched_shows = sum(1 for show in stats if show['watched_episodes'] > 0)
        total_episodes = sum(show['total_episodes'] for show in stats)
        watched_episodes = sum(show['watched_episodes'] for show in stats)
        total_watch_time = sum(show['total_watch_time_minutes'] for show in stats)
        hours = int(total_watch_time // 60)
        minutes = int(total_watch_time % 60)
        completion_percentage = (watched_episodes / total_episodes * 100) if total_episodes > 0 else 0

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
            last_watched = movie['last_watched']
            formatted_date = "Never"
            if last_watched:
                # Convert to datetime and format
                if isinstance(last_watched, (int, float)):
                    last_watched = datetime.fromtimestamp(last_watched)
                formatted_date = last_watched.strftime("%Y-%m-%d")

            # Format duration as hours and minutes
            hours = int(movie['duration_minutes'] // 60)
            minutes = int(movie['duration_minutes'] % 60)
            duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

            # Format rating
            rating = f"{movie['rating']}" if movie['rating'] else "-"

            # Clean title for markdown table
            title = movie['title'].replace('|', '\\|')

            md += f"| {title} | {movie['watch_count']} | {formatted_date} | {duration} | {rating} |\n"

        # Add summary section
        total_movies = len(stats)
        watched_movies = sum(1 for movie in stats if movie['watched'])
        watch_count = sum(movie['watch_count'] for movie in stats)
        total_duration = sum(movie['duration_minutes'] for movie in stats)
        watched_duration = sum(movie['duration_minutes'] * movie['watch_count'] for movie in stats if movie['watched'])
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
                last_watched = show['last_watched']
                formatted_date = "Never"
                if last_watched:
                    if isinstance(last_watched, (int, float)):
                        last_watched = datetime.fromtimestamp(last_watched)
                    formatted_date = last_watched.strftime("%Y-%m-%d %H:%M")

                # Format watch time as hours and minutes
                hours = int(show['total_watch_time_minutes'] // 60)
                minutes = int(show['total_watch_time_minutes'] % 60)
                watch_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

                # Format completion percentage
                completion = f"{show['watched_episodes']}/{show['total_episodes']} ({show['completion_percentage']:.1f}%)"

                # Clean title for markdown table
                title = show['title'].replace('|', '\\|')

                md += f"| {title} | {formatted_date} | {completion} | {watch_time} |\n"
        else:  # movies
            md += "| Title | Last Watched | Watch Count | Duration |\n"
            md += "|-------|--------------|-------------|----------|\n"

            for movie in stats:
                # Format last watched date
                last_watched = movie['last_watched']
                formatted_date = "Never"
                if last_watched:
                    if isinstance(last_watched, (int, float)):
                        last_watched = datetime.fromtimestamp(last_watched)
                    formatted_date = last_watched.strftime("%Y-%m-%d %H:%M")

                # Format duration as hours and minutes
                hours = int(movie['duration_minutes'] // 60)
                minutes = int(movie['duration_minutes'] % 60)
                duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

                # Clean title for markdown table
                title = movie['title'].replace('|', '\\|')

                md += f"| {title} | {formatted_date} | {movie['watch_count']} | {duration} |\n"

        return md


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
        writer.writerow(["Title", "Watched Episodes", "Total Episodes", "Completion Percentage",
                         "Watch Time (minutes)", "Year", "Last Watched"])

        # Write data rows
        for show in stats:
            last_watched = ""
            if show['last_watched']:
                if isinstance(show['last_watched'], datetime):
                    last_watched = show['last_watched'].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    last_watched = str(show['last_watched'])

            writer.writerow([
                show['title'],
                show['watched_episodes'],
                show['total_episodes'],
                f"{show['completion_percentage']:.1f}",
                show['total_watch_time_minutes'],
                show['year'] if show['year'] else "",
                last_watched
            ])

        # Write summary rows
        total_shows = len(stats)
        watched_shows = sum(1 for show in stats if show['watched_episodes'] > 0)
        total_episodes = sum(show['total_episodes'] for show in stats)
        watched_episodes = sum(show['watched_episodes'] for show in stats)
        total_watch_time = sum(show['total_watch_time_minutes'] for show in stats)
        completion_percentage = (watched_episodes / total_episodes * 100) if total_episodes > 0 else 0

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
        writer.writerow(["Title", "Year", "Watch Count", "Last Watched",
                         "Duration (minutes)", "Watched", "Rating"])

        # Write data rows
        for movie in stats:
            last_watched = ""
            if movie['last_watched']:
                if isinstance(movie['last_watched'], datetime):
                    last_watched = movie['last_watched'].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    last_watched = str(movie['last_watched'])

            writer.writerow([
                movie['title'],
                movie['year'] if movie['year'] else "",
                movie['watch_count'],
                last_watched,
                movie['duration_minutes'],
                "Yes" if movie['watched'] else "No",
                movie['rating'] if movie['rating'] else ""
            ])

        # Write summary rows
        total_movies = len(stats)
        watched_movies = sum(1 for movie in stats if movie['watched'])
        watch_count = sum(movie['watch_count'] for movie in stats)
        total_duration = sum(movie['duration_minutes'] for movie in stats)
        watched_duration = sum(movie['duration_minutes'] * movie['watch_count'] for movie in stats if movie['watched'])
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
            writer.writerow(["Title", "Last Watched", "Watched Episodes", "Total Episodes",
                           "Completion Percentage", "Watch Time (minutes)"])

            # Write data rows for shows
            for show in stats:
                last_watched = ""
                if show['last_watched']:
                    if isinstance(show['last_watched'], datetime):
                        last_watched = show['last_watched'].strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        last_watched = str(show['last_watched'])

                writer.writerow([
                    show['title'],
                    last_watched,
                    show['watched_episodes'],
                    show['total_episodes'],
                    f"{show['completion_percentage']:.1f}",
                    show['total_watch_time_minutes']
                ])
        else:  # movies
            # Write header row for movies
            writer.writerow(["Title", "Last Watched", "Watch Count", "Duration (minutes)"])

            # Write data rows for movies
            for movie in stats:
                last_watched = ""
                if movie['last_watched']:
                    if isinstance(movie['last_watched'], datetime):
                        last_watched = movie['last_watched'].strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        last_watched = str(movie['last_watched'])

                writer.writerow([
                    movie['title'],
                    last_watched,
                    movie['watch_count'],
                    movie['duration_minutes']
                ])

        return output.getvalue()


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
        lines = ["Title|Watched|Total|WatchTime"]

        # Add rows for each show with minimal separators
        for show in stats:
            # Format watch time compactly
            hours = int(show['total_watch_time_minutes'] // 60)
            minutes = int(show['total_watch_time_minutes'] % 60)
            watch_time = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"

            # Clean title for delimiter use
            title = show['title'].replace('|', '/')

            # Create compact row
            lines.append(f"{title}|{show['watched_episodes']}|{show['total_episodes']}|{watch_time}")

        # Add compact summary (S: for summary)
        total_shows = len(stats)
        watched_shows = sum(1 for show in stats if show['watched_episodes'] > 0)
        total_episodes = sum(show['total_episodes'] for show in stats)
        watched_episodes = sum(show['watched_episodes'] for show in stats)
        total_watch_time = sum(show['total_watch_time_minutes'] for show in stats)

        hours = int(total_watch_time // 60)
        minutes = int(total_watch_time % 60)

        lines.append(f"Summary: TotalShows={total_shows} WatchedShows={watched_shows} Episodes={watched_episodes}/{total_episodes} TotalWatchTime={hours}h{minutes}m")

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
            last_watched = movie['last_watched']
            formatted_date = "-"
            if last_watched:
                # Convert to datetime and format
                if isinstance(last_watched, (int, float)):
                    last_watched = datetime.fromtimestamp(last_watched)
                formatted_date = last_watched.strftime("%y-%m-%d")  # Shorter year format

            # Format duration compactly
            hours = int(movie['duration_minutes'] // 60)
            minutes = int(movie['duration_minutes'] % 60)
            duration = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"

            # Format rating
            rating = f"{movie['rating']}" if movie['rating'] else "-"

            # Clean title for delimiter use
            title = movie['title'].replace('|', '/')

            # Create compact row
            lines.append(f"{title}|{movie['watch_count']}|{formatted_date}|{duration}|{rating}")

        # Add compact summary
        total_movies = len(stats)
        watched_movies = sum(1 for movie in stats if movie['watched'])
        watch_count = sum(movie['watch_count'] for movie in stats)
        total_duration = sum(movie['duration_minutes'] for movie in stats)
        watched_duration = sum(movie['duration_minutes'] * movie['watch_count'] for movie in stats if movie['watched'])

        tot_h = int(total_duration // 60)
        tot_m = int(total_duration % 60)
        wat_h = int(watched_duration // 60)
        wat_m = int(watched_duration % 60)

        lines.append(f"Summary: TotalMovies={total_movies} WatchedMovies={watched_movies} TotalWatches={watch_count} TotalDuration={tot_h}h{tot_m}m WatchedDuration={wat_h}h{wat_m}m")

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
                last_watched = show['last_watched']
                formatted_date = "Never"
                if last_watched:
                    # Convert to datetime and format
                    if isinstance(last_watched, (int, float)):
                        last_watched = datetime.fromtimestamp(last_watched)
                    formatted_date = last_watched.strftime("%y-%m-%d")  # Shorter year format

                # Format watch time compactly
                hours = int(show['total_watch_time_minutes'] // 60)
                minutes = int(show['total_watch_time_minutes'] % 60)
                watch_time = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"

                # Format progress without percentage
                progress = f"{show['watched_episodes']}/{show['total_episodes']}"

                # Clean title for delimiter use
                title = show['title'].replace('|', '/')

                lines.append(f"{title}|{formatted_date}|{progress}|{watch_time}")
        else:  # movies
            # Short but descriptive headers for movies
            lines = ["Title|LastWatched|WatchCount|Duration"]

            for movie in stats:
                # Format last watched date compactly
                last_watched = movie['last_watched']
                formatted_date = "Never"
                if last_watched:
                    # Convert to datetime and format
                    if isinstance(last_watched, (int, float)):
                        last_watched = datetime.fromtimestamp(last_watched)
                    formatted_date = last_watched.strftime("%y-%m-%d")  # Shorter year format

                # Format duration compactly
                hours = int(movie['duration_minutes'] // 60)
                minutes = int(movie['duration_minutes'] % 60)
                duration = f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"

                # Clean title for delimiter use
                title = movie['title'].replace('|', '/')

                lines.append(f"{title}|{formatted_date}|{movie['watch_count']}|{duration}")

        return "\n".join(lines)
