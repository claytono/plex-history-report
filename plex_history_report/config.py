"""Configuration handler for Plex History Report.

This module handles loading and validating configuration from a YAML file.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Try current working directory first, then package directory
CWD_CONFIG_PATH = Path.cwd() / "config.yaml"
PKG_CONFIG_PATH = PROJECT_ROOT / "config.yaml"

# Use current working directory path if it exists, otherwise use package path
DEFAULT_CONFIG_PATH = CWD_CONFIG_PATH if CWD_CONFIG_PATH.exists() else PKG_CONFIG_PATH


class ConfigError(Exception):
    """Raised when there's an issue with the configuration."""

    pass


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the configuration file. If None, uses the default path.

    Returns:
        Dict containing the configuration.

    Raises:
        ConfigError: If the configuration file doesn't exist or is invalid.
    """
    if config_path is None:
        # Check current working directory first if not explicitly specified
        if CWD_CONFIG_PATH.exists():
            config_path = CWD_CONFIG_PATH
            logger.debug(f"Using config file from current directory: {config_path}")
        else:
            config_path = PKG_CONFIG_PATH
            logger.debug(f"Using config file from package directory: {config_path}")

    try:
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        with config_path.open() as f:
            config = yaml.safe_load(f)

        # Validate configuration
        if not config or not isinstance(config, dict):
            raise ConfigError("Invalid configuration format")

        if "plex" not in config:
            raise ConfigError("Missing 'plex' section in configuration")

        plex_config = config["plex"]
        if "base_url" not in plex_config:
            raise ConfigError("Missing 'base_url' in plex configuration")
        if "token" not in plex_config:
            raise ConfigError("Missing 'token' in plex configuration")

        # User is optional, will be validated but not required
        if "default_user" in plex_config and not isinstance(plex_config["default_user"], str):
            raise ConfigError("'default_user' must be a string")

        return config
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing configuration file: {e}") from e
    except Exception as e:
        raise ConfigError(f"Error loading configuration: {e}") from e


def create_default_config(config_path: Optional[Path] = None) -> Path:
    """Create a default configuration file.

    Args:
        config_path: Path to create the configuration file. If None, uses the default path.

    Returns:
        Path to the created configuration file.
    """
    if config_path is None:
        # Create in current working directory by default
        config_path = CWD_CONFIG_PATH
        logger.debug(f"Creating default config in current directory: {config_path}")

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    default_config = {
        "plex": {
            "base_url": "http://localhost:32400",
            "token": "YOUR_PLEX_TOKEN",
            "default_user": "",  # Empty string means no default user
        }
    }

    with config_path.open("w") as f:
        yaml.dump(default_config, f, default_flow_style=False)

    return config_path
