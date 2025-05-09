"""Factory for creating formatters for Plex History Report statistics."""

from typing import ClassVar, Dict, List, Type

from plex_history_report.formatters.base import BaseFormatter
from plex_history_report.formatters.compact_formatter import CompactFormatter
from plex_history_report.formatters.csv_formatter import CsvFormatter
from plex_history_report.formatters.json_formatter import JsonFormatter
from plex_history_report.formatters.markdown_formatter import MarkdownFormatter
from plex_history_report.formatters.rich_formatter import RichFormatter
from plex_history_report.formatters.yaml_formatter import YamlFormatter


class FormatterFactory:
    """Factory for creating formatters based on format name."""

    _formatters: ClassVar[Dict[str, Type[BaseFormatter]]] = {
        "table": RichFormatter,
        "json": JsonFormatter,
        "markdown": MarkdownFormatter,
        "csv": CsvFormatter,
        "yaml": YamlFormatter,
        "compact": CompactFormatter,
    }

    @classmethod
    def get_formatter(cls, format_name: str) -> BaseFormatter:
        """Get a formatter instance based on format name.

        Args:
            format_name: Name of the format (table, json, yaml, etc.)

        Returns:
            An instance of the appropriate formatter.

        Raises:
            ValueError: If format_name is not recognized.
        """
        formatter_class = cls._formatters.get(format_name)
        if formatter_class is None:
            raise ValueError(f"Unknown format: {format_name}")

        return formatter_class()

    @classmethod
    def register_formatter(cls, format_name: str, formatter_class: Type[BaseFormatter]) -> None:
        """Register a new formatter type.

        Args:
            format_name: Name of the format.
            formatter_class: Formatter class to register.
        """
        cls._formatters[format_name] = formatter_class

    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Get a list of available format names.

        Returns:
            List of available format names.
        """
        return list(cls._formatters.keys())
