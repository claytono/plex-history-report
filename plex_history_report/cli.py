"""Command-line interface for Plex History Reports.

This module provides the command-line interface for the plex-history-report tool.
"""

import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from plex_history_report.config import (
    CWD_CONFIG_PATH,
    ConfigError,
    create_default_config,
    load_config,
)
from plex_history_report.formatters import FormatterFactory
from plex_history_report.plex_client import PlexClient, PlexClientError
from plex_history_report.utils import PerformanceLogHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

logger = logging.getLogger("plex_history_report")


# Define available sort options for different media types
TV_SORT_OPTIONS = [
    "title",
    "watched_episodes",
    "completion_percentage",
    "last_watched",
    "year",
    "rating",
]
MOVIE_SORT_OPTIONS = ["title", "year", "last_watched", "watch_count", "rating", "duration_minutes"]


def configure_parser() -> argparse.ArgumentParser:
    """Configure the argument parser.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Analyze and display Plex TV show and movie watch statistics."
    )

    # Create a mutually exclusive group for media type selection
    # Changed required to False to allow --list-users and --create-config to work without media flag
    media_group = parser.add_mutually_exclusive_group(required=False)
    media_group.add_argument("--tv", action="store_true", help="Show TV show statistics")
    media_group.add_argument("--movies", action="store_true", help="Show movie statistics")

    # Command line options that can be used without specifying a media type
    utility_group = parser.add_argument_group("utility options")
    utility_group.add_argument(
        "--list-users", action="store_true", help="List available Plex users and exit"
    )
    utility_group.add_argument(
        "--create-config", action="store_true", help="Create a default configuration file"
    )

    parser.add_argument("--config", type=str, help="Path to configuration file")

    # Get available formats from FormatterFactory
    available_formats = FormatterFactory.get_available_formats()
    parser.add_argument(
        "--format",
        type=str,
        choices=available_formats,
        default="table",
        help="Output format (default: table)",
    )

    parser.add_argument(
        "--show-recent",
        action="store_true",
        help="Show recently watched items in addition to overall statistics",
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Enable performance benchmarking and log detailed timing information",
    )

    parser.add_argument(
        "--record",
        choices=["raw-data", "test-data", "both"],
        help="Record Plex API data: raw-data (non-anonymized), test-data (anonymized), or both",
    )

    parser.add_argument(
        "--user",
        type=str,
        help="Filter statistics for a specific Plex user (overrides default_user in config)",
    )

    # Add mutually exclusive group for watching status filtering
    watch_filter_group = parser.add_mutually_exclusive_group()
    watch_filter_group.add_argument(
        "--include-unwatched",
        action="store_true",
        help="Include items with no watches (off by default)",
    )
    watch_filter_group.add_argument(
        "--partially-watched-only",
        action="store_true",
        help="Show only partially watched items (not fully watched or unwatched)",
    )

    parser.add_argument(
        "--sort-by",
        type=str,
        help=f"Field to sort results by. For TV: {', '.join(TV_SORT_OPTIONS)}. For movies: {', '.join(MOVIE_SORT_OPTIONS)}.",
    )

    # For backward compatibility - mark as deprecated
    parser.add_argument(
        "--detailed",
        action="store_true",
        help=argparse.SUPPRESS,  # Hide from help but keep for backward compatibility
    )

    return parser


def run(args: argparse.Namespace) -> int:
    """Run the plex-history-report tool.

    Args:
        args: Command-line arguments.

    Returns:
        Exit code.
    """
    console = Console()
    performance_data = {}

    # Configure logging level
    if args.debug:
        logging.getLogger("plex_history_report").setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Enable performance logging if benchmark mode is enabled
    if args.benchmark:
        logging.getLogger("plex_history_report").setLevel(logging.INFO)
        logger.info("Performance benchmarking enabled")

        # Set the global benchmarking flag
        from plex_history_report.utils import set_benchmarking

        set_benchmarking(True)

        # Add the performance handler
        performance_handler = PerformanceLogHandler(performance_data)
        logging.getLogger("plex_history_report").addHandler(performance_handler)
    else:
        # Ensure benchmarking is disabled
        from plex_history_report.utils import set_benchmarking

        set_benchmarking(False)

    # Create default config if requested
    if args.create_config:
        try:
            config_path = create_default_config()
            console.print(f"Created default configuration file at: {config_path}")
            console.print("Please edit this file to add your Plex server details.")
            return 0
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")
            return 1

    # Load or create configuration
    try:
        # Use specified config path or CWD for config creation/loading
        config_path = Path(args.config) if args.config else CWD_CONFIG_PATH

        # Check if config file exists, create it if it doesn't
        if not config_path.exists() and not args.create_config:
            console.print(f"Configuration file not found at: {config_path}")
            console.print("Creating a default configuration file...")
            create_default_config(config_path)
            console.print(f"Created default configuration file at: {config_path}")
            console.print(
                "Please edit this file with your Plex server details and run the command again."
            )
            return 0

        # This will use the correct priority for loading if no path is specified
        config = load_config(config_path if config_path.exists() else None)
    except ConfigError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        console.print("\nRun with --create-config to create a default configuration file.")
        return 1

    # Initialize formatter using the factory
    try:
        formatter = FormatterFactory.get_formatter(args.format)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1

    try:
        # Connect to Plex server
        plex_config = config["plex"]

        # Set up data recorder if requested
        data_recorder = None
        if args.record:
            from plex_history_report.recorders import PlexDataRecorder

            data_recorder = PlexDataRecorder(mode=args.record)
            logger.info(f"Recording Plex data in '{args.record}' mode")

        client = PlexClient(
            plex_config["base_url"], plex_config["token"], data_recorder=data_recorder
        )

        # List users if requested
        if args.list_users:
            users = client.get_available_users()
            console.print("[bold]Available Plex Users:[/bold]")
            if users:
                for user in users:
                    console.print(f"- {user}")
            else:
                console.print(
                    "No users found or cannot access user information with current token."
                )
            return 0

        # Require either --tv or --movies when not using utility commands
        if not (args.tv or args.movies):
            console.print("[bold red]Error:[/bold red] Either --tv or --movies must be specified.")
            console.print("Run with --help for usage information.")
            return 1

        # Determine media type
        media_type = "show" if args.tv else "movie"

        # Determine sort field
        sort_by = None
        if args.sort_by:
            valid_sort_options = TV_SORT_OPTIONS if args.tv else MOVIE_SORT_OPTIONS
            if args.sort_by not in valid_sort_options:
                console.print(f"[bold red]Invalid sort option:[/bold red] {args.sort_by}")
                console.print(
                    f"Valid sort options for {media_type}s are: {', '.join(valid_sort_options)}"
                )
                return 1
            sort_by = args.sort_by
        else:
            # Use default sort options
            sort_by = "completion_percentage" if args.tv else "last_watched"

        # Determine user to filter by
        username = None
        if args.user:
            # Command-line argument takes precedence
            username = args.user
        elif plex_config.get("default_user"):
            # Use default user from config if available
            username = plex_config["default_user"]
            logger.info(f"Using default user from config: {username}")

        # Get appropriate statistics based on media type
        if args.tv:
            logger.debug(f"Fetching TV show statistics for user: {username}")
            stats = client.get_all_show_statistics(
                username=username, include_unwatched=args.include_unwatched, sort_by=sort_by
            )

            # Filter for partially watched items if requested
            if args.partially_watched_only:
                logger.debug("Filtering for partially watched TV shows")
                stats = [show for show in stats if 0 < show["completion_percentage"] < 100]
                logger.info(f"Filtered to {len(stats)} partially watched TV shows")
        else:  # movies
            logger.debug(f"Fetching movie statistics for user: {username}")
            stats = client.get_all_movie_statistics(
                username=username, include_unwatched=args.include_unwatched, sort_by=sort_by
            )

            # Filter for partially watched movies if requested
            if args.partially_watched_only:
                logger.debug("Filtering for partially watched movies")
                # Consider movies "partially watched" if they're between 0% and 100% complete
                before_count = len(stats)
                stats = [movie for movie in stats if 0 < movie["completion_percentage"] < 100]
                logger.info(
                    f"Filtered to {len(stats)} partially watched movies (removed {before_count - len(stats)} fully watched or unwatched movies)"
                )

        # For backward compatibility, map --detailed to --show-recent
        if args.detailed:
            args.show_recent = True
            logger.warning("The --detailed flag is deprecated. Please use --show-recent instead.")

        # Get recently watched content if needed
        recently_watched = None
        if args.show_recent:
            if args.tv:
                recently_watched = client.get_recently_watched_shows(username=username)
            else:
                recently_watched = client.get_recently_watched_movies(username=username)

        # Skip formatting and displaying output if in record mode
        if args.record:
            logger.info("Record mode active - skipping normal output display")
            return 0

        # Use the standardized format_content method for all formatters
        outputs = formatter.format_content(
            stats,
            media_type=media_type,
            show_recent=args.show_recent,
            recently_watched=recently_watched,
        )

        # Use the standardized display_output method to print to console
        formatter.display_output(console, outputs)

        # Display performance report if benchmark mode is enabled
        if args.benchmark and performance_data:
            console.print("\n[bold]Performance Benchmark Report:[/bold]")
            console.print("=" * 60)

            # Sort functions by total time spent
            total_times = {func: sum(times) for func, times in performance_data.items()}
            sorted_funcs = sorted(total_times.keys(), key=lambda f: total_times[f], reverse=True)

            # Display table of results
            console.print(f"{'Function':<40} {'Calls':<8} {'Total (s)':<12} {'Avg (s)':<12}")
            console.print("-" * 60)

            for func in sorted_funcs:
                times = performance_data[func]
                calls = len(times)
                total = sum(times)
                avg = total / calls
                console.print(f"{func:<40} {calls:<8} {total:<12.2f} {avg:<12.2f}")

            console.print("=" * 60)

        return 0

    except PlexClientError as e:
        console.print(f"[bold red]Plex client error:[/bold red] {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


def main() -> None:
    """Main entry point for the plex-history-report CLI."""
    parser = configure_parser()
    args = parser.parse_args()

    try:
        exit_code = run(args)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
