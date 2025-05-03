"""Tests for the config module."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from plex_history_report.config import (
    ConfigError,
    create_default_config,
    load_config,
)


class TestConfig(unittest.TestCase):
    """Test the config module."""

    def setUp(self):
        """Set up temporary directory and files for testing."""
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def create_test_config(self, config_data, filename="config.yaml"):
        """Create a test configuration file with the given data."""
        config_path = self.temp_path / filename
        with config_path.open("w") as f:
            yaml.dump(config_data, f)
        return config_path

    def test_load_config_valid(self):
        """Test loading a valid configuration."""
        # Create a valid configuration file
        valid_config = {
            "plex": {
                "base_url": "http://plex.example.com:32400",
                "token": "valid_token",
                "default_user": "test_user",
            }
        }
        config_path = self.create_test_config(valid_config)

        # Load the configuration
        loaded_config = load_config(config_path)

        # Verify the configuration was loaded correctly
        self.assertEqual(loaded_config, valid_config)
        self.assertEqual(loaded_config["plex"]["base_url"], "http://plex.example.com:32400")
        self.assertEqual(loaded_config["plex"]["token"], "valid_token")
        self.assertEqual(loaded_config["plex"]["default_user"], "test_user")

    def test_load_config_minimal_valid(self):
        """Test loading a minimal valid configuration (without optional fields)."""
        # Create a minimal valid configuration file
        minimal_config = {
            "plex": {
                "base_url": "http://plex.example.com:32400",
                "token": "valid_token",
            }
        }
        config_path = self.create_test_config(minimal_config)

        # Load the configuration
        loaded_config = load_config(config_path)

        # Verify the configuration was loaded correctly
        self.assertEqual(loaded_config, minimal_config)

    def test_load_config_default_path(self):
        """Test loading configuration from the default path."""
        # Mock the default config path to point to our temp file
        valid_config = {
            "plex": {
                "base_url": "http://plex.example.com:32400",
                "token": "valid_token",
            }
        }
        config_path = self.create_test_config(valid_config)

        with patch("plex_history_report.config.DEFAULT_CONFIG_PATH", config_path):
            # Load the configuration without specifying a path
            loaded_config = load_config()

            # Verify the configuration was loaded correctly
            self.assertEqual(loaded_config, valid_config)

    def test_load_config_file_not_found(self):
        """Test attempting to load a non-existent configuration file."""
        # Use a path that doesn't exist
        non_existent_path = self.temp_path / "non_existent_config.yaml"

        # Attempt to load the configuration
        with self.assertRaises(ConfigError) as context:
            load_config(non_existent_path)

        # Verify the correct error message
        self.assertIn("Configuration file not found", str(context.exception))
        self.assertIn(str(non_existent_path), str(context.exception))

    def test_load_config_invalid_yaml(self):
        """Test loading a configuration with invalid YAML."""
        # Create a file with invalid YAML
        invalid_yaml_path = self.temp_path / "invalid.yaml"
        with invalid_yaml_path.open("w") as f:
            f.write("invalid: yaml: content: [")

        # Attempt to load the configuration
        with self.assertRaises(ConfigError) as context:
            load_config(invalid_yaml_path)

        # Verify the correct error message
        self.assertIn("Error parsing configuration file", str(context.exception))

    def test_load_config_empty_config(self):
        """Test loading an empty configuration."""
        # Create an empty configuration file
        empty_config_path = self.create_test_config(None)

        # Attempt to load the configuration
        with self.assertRaises(ConfigError) as context:
            load_config(empty_config_path)

        # Verify the correct error message
        self.assertIn("Invalid configuration format", str(context.exception))

    def test_load_config_not_dict(self):
        """Test loading a configuration that's not a dictionary."""
        # Create a configuration file with a list instead of a dict
        list_config_path = self.create_test_config(["item1", "item2"])

        # Attempt to load the configuration
        with self.assertRaises(ConfigError) as context:
            load_config(list_config_path)

        # Verify the correct error message
        self.assertIn("Invalid configuration format", str(context.exception))

    def test_load_config_missing_plex_section(self):
        """Test loading a configuration missing the 'plex' section."""
        # Create a configuration file without a plex section
        no_plex_config = {"other_section": {"key": "value"}}
        no_plex_path = self.create_test_config(no_plex_config)

        # Attempt to load the configuration
        with self.assertRaises(ConfigError) as context:
            load_config(no_plex_path)

        # Verify the correct error message
        self.assertIn("Missing 'plex' section in configuration", str(context.exception))

    def test_load_config_missing_base_url(self):
        """Test loading a configuration missing the 'base_url' in plex section."""
        # Create a configuration file without base_url
        no_base_url_config = {
            "plex": {
                "token": "valid_token",
            }
        }
        no_base_url_path = self.create_test_config(no_base_url_config)

        # Attempt to load the configuration
        with self.assertRaises(ConfigError) as context:
            load_config(no_base_url_path)

        # Verify the correct error message
        self.assertIn("Missing 'base_url' in plex configuration", str(context.exception))

    def test_load_config_missing_token(self):
        """Test loading a configuration missing the 'token' in plex section."""
        # Create a configuration file without token
        no_token_config = {
            "plex": {
                "base_url": "http://plex.example.com:32400",
            }
        }
        no_token_path = self.create_test_config(no_token_config)

        # Attempt to load the configuration
        with self.assertRaises(ConfigError) as context:
            load_config(no_token_path)

        # Verify the correct error message
        self.assertIn("Missing 'token' in plex configuration", str(context.exception))

    def test_load_config_invalid_default_user(self):
        """Test loading a configuration with invalid default_user type."""
        # Create a configuration file with non-string default_user
        invalid_user_config = {
            "plex": {
                "base_url": "http://plex.example.com:32400",
                "token": "valid_token",
                "default_user": 123,  # Should be a string
            }
        }
        invalid_user_path = self.create_test_config(invalid_user_config)

        # Attempt to load the configuration
        with self.assertRaises(ConfigError) as context:
            load_config(invalid_user_path)

        # Verify the correct error message
        self.assertIn("'default_user' must be a string", str(context.exception))

    def test_create_default_config_custom_path(self):
        """Test creating a default configuration at a custom path."""
        # Define a custom path
        custom_path = self.temp_path / "custom_config.yaml"

        # Create a default configuration at the custom path
        result_path = create_default_config(custom_path)

        # Verify the returned path matches the input path
        self.assertEqual(result_path, custom_path)

        # Verify the file was created
        self.assertTrue(custom_path.exists())

        # Load and verify the configuration content
        with custom_path.open() as f:
            config = yaml.safe_load(f)

        # Verify the structure of the created config
        self.assertIn("plex", config)
        self.assertIn("base_url", config["plex"])
        self.assertIn("token", config["plex"])
        self.assertIn("default_user", config["plex"])
        self.assertEqual(config["plex"]["base_url"], "http://localhost:32400")
        self.assertEqual(config["plex"]["token"], "YOUR_PLEX_TOKEN")
        self.assertEqual(config["plex"]["default_user"], "")

    def test_create_default_config_default_path(self):
        """Test creating a default configuration at the default path."""
        # Mock DEFAULT_CONFIG_PATH to point to our temp file
        temp_default_config = self.temp_path / "default_config.yaml"

        with patch("plex_history_report.config.DEFAULT_CONFIG_PATH", temp_default_config):
            # Create a default configuration without specifying a path
            result_path = create_default_config()

            # Verify the returned path matches the mocked default path
            self.assertEqual(result_path, temp_default_config)

            # Verify the file was created
            self.assertTrue(temp_default_config.exists())

            # Load and verify the configuration content
            with temp_default_config.open() as f:
                config = yaml.safe_load(f)

            # Verify the structure of the created config
            self.assertIn("plex", config)
            self.assertIn("base_url", config["plex"])
            self.assertIn("token", config["plex"])
            self.assertIn("default_user", config["plex"])

    def test_create_default_config_existing_directory(self):
        """Test creating a default configuration in an existing directory."""
        # Create a nested directory
        nested_dir = self.temp_path / "nested" / "dirs"
        nested_dir.mkdir(parents=True)

        # Define a path inside the nested directory
        config_path = nested_dir / "config.yaml"

        # Create a default configuration
        create_default_config(config_path)

        # Verify the file was created
        self.assertTrue(config_path.exists())

    def test_create_default_config_new_directory(self):
        """Test creating a default configuration in a new directory."""
        # Define a path in a non-existing directory
        new_dir = self.temp_path / "new_dir"
        config_path = new_dir / "config.yaml"

        # Create a default configuration
        create_default_config(config_path)

        # Verify the directory and file were created
        self.assertTrue(new_dir.exists())
        self.assertTrue(config_path.exists())


if __name__ == "__main__":
    unittest.main()
