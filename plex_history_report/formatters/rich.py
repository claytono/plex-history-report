"""Rich formatter for displaying Plex History Report statistics with tables."""

from datetime import datetime
from typing import Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from plex_history_report.formatters.base import BaseFormatter


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
