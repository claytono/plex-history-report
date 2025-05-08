"""Main entry point for direct module execution.

This file enables running the module directly with: python -m plex_history_report
or with uvx: uvx -m plex_history_report

It's particularly useful for running the tool directly from GitHub with uvx.
"""

from .cli import main

if __name__ == "__main__":
    main()
