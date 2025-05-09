"""Base formatter for displaying Plex History Report statistics."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from rich.console import Console

logger = logging.getLogger(__name__)


class BaseFormatter(ABC):
    """Base class for formatters."""

    @abstractmethod
    def format_show_statistics(self, stats: List[Dict]) -> str:
        """Format show statistics.

        Args:
            stats: List of show statistics.

        Returns:
            Formatted string representation of the statistics.
        """
        pass

    @abstractmethod
    def format_movie_statistics(self, stats: List[Dict]) -> str:
        """Format movie statistics.

        Args:
            stats: List of movie statistics.

        Returns:
            Formatted string representation of the statistics.
        """
        pass

    @abstractmethod
    def format_recently_watched(self, stats: List[Dict], media_type: str = "show") -> str:
        """Format recently watched media.

        Args:
            stats: List of recently watched media statistics.
            media_type: Type of media ("show" or "movie").

        Returns:
            Formatted string representation of the recently watched media.
        """
        pass

    def format_content(
        self,
        stats: List[Dict],
        media_type: str,
        show_recent: bool = False,
        recently_watched: Optional[List[Dict]] = None,
    ) -> List[str]:
        """Format content based on media type and whether to show recent content.

        This is a convenience method to standardize output handling across formatters.

        Args:
            stats: List of statistics for the main content.
            media_type: Type of media ("show" or "movie").
            show_recent: Whether to include recently watched content.
            recently_watched: List of recently watched media statistics.

        Returns:
            List of formatted strings to be displayed.
        """
        outputs = []

        # Format main statistics (each formatter now includes summary data in these methods)
        if media_type == "show":
            outputs.append(self.format_show_statistics(stats))
        else:
            outputs.append(self.format_movie_statistics(stats))

        # Format recently watched content if requested
        if show_recent and recently_watched is not None:
            outputs.append(self.format_recently_watched(recently_watched, media_type=media_type))

        return outputs

    def display_output(self, console: Console, outputs: List[str]) -> None:
        """Display formatted outputs to the console.

        Args:
            console: Rich console to print to.
            outputs: List of formatted strings to display.
        """
        for output in outputs:
            if output:  # Only display non-empty output
                console.print(output)
