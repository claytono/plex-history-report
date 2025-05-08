"""Main entry point for direct module execution.

This file enables running the module directly with various methods:
- python -m plex_history_report
- uvx git+https://github.com/claytono/plex-history-report

It allows the tool to be run directly without installation.
"""

from .cli import main

if __name__ == "__main__":
    main()
