"""Formatters for displaying Plex History Report statistics.

This package provides various formatters for displaying Plex statistics
in different formats like text tables, JSON, etc.
"""

from plex_history_report.formatters.base import BaseFormatter
from plex_history_report.formatters.compact_formatter import CompactFormatter
from plex_history_report.formatters.csv_formatter import CsvFormatter
from plex_history_report.formatters.factory import FormatterFactory
from plex_history_report.formatters.json_formatter import JsonFormatter
from plex_history_report.formatters.markdown_formatter import MarkdownFormatter
from plex_history_report.formatters.rich_formatter import RichFormatter
from plex_history_report.formatters.yaml_formatter import YamlFormatter

__all__ = [
    "BaseFormatter",
    "CompactFormatter",
    "CsvFormatter",
    "FormatterFactory",
    "JsonFormatter",
    "MarkdownFormatter",
    "RichFormatter",
    "YamlFormatter",
]
