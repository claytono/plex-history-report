"""Recorder for capturing Plex data during normal operation.

This module provides functionality for recording Plex API responses
for testing and debugging purposes.
"""

import json
import logging
import random
import re
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PlexDataRecorder:
    """Records Plex API data for testing purposes with different modes."""

    def __init__(self, mode: str = "raw-data", output_dir: str = "tests/fixtures") -> None:
        """Initialize the data recorder.

        Args:
            mode: Recording mode - "raw-data", "test-data", or "both".
            output_dir: Directory where recorded data will be saved.
        """
        self.mode = mode
        self.output_dir = Path(output_dir)
        self.raw_tv_data = {}
        self.raw_movie_data = {}
        self.test_tv_data = {}
        self.test_movie_data = {}

        # Create the output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if mode in ["raw-data", "both"]:
            logger.warning(
                "Recording raw, non-anonymized Plex API data. "
                "This data may contain sensitive information and should not be shared."
            )

    @staticmethod
    def _serialize_plex_item(item: Any) -> Dict:
        """Convert a Plex item to a serializable dictionary.

        Args:
            item: The Plex object to serialize.

        Returns:
            A serializable dictionary representing the Plex object.
        """
        try:
            # Basic serialization of common properties
            result = {}

            # Try to add common properties if they exist
            for prop in [
                "key",
                "title",
                "type",
                "year",
                "duration",
                "rating",
                "viewOffset",
                "isWatched",
            ]:
                if hasattr(item, prop):
                    value = getattr(item, prop)
                    result[prop] = value

            # Handle special properties
            if hasattr(item, "viewedAt") and item.viewedAt:
                result["viewedAt"] = str(item.viewedAt)

            if hasattr(item, "username"):
                result["username"] = item.username

            # For episodes add season and episode info
            if getattr(item, "type", None) == "episode":
                if hasattr(item, "seasonNumber"):
                    result["seasonNumber"] = item.seasonNumber
                if hasattr(item, "index"):
                    result["index"] = item.index
                with suppress(Exception):
                    result["showTitle"] = item.show().title

            return result
        except Exception as e:
            logger.warning(f"Error serializing Plex item: {e}")
            # Return a minimal representation
            return {"error": str(e), "type": getattr(item, "type", "unknown")}

    def _save_raw_tv_data(self) -> None:
        """Save collected raw TV data to a fixed JSON file, overwriting if it exists."""
        if not self.raw_tv_data:
            return

        try:
            # Use a fixed filename for TV data
            filename = self.output_dir / "plex_raw_tv_data.json"

            # Save the data to file (overwrites if exists)
            with filename.open("w", encoding="utf-8") as f:
                json.dump(self.raw_tv_data, f, indent=2, default=str)

            logger.info(f"Saved raw TV data to {filename}")
        except Exception as e:
            logger.error(f"Error saving raw TV data to file: {e}")

    def _store_raw_tv_data(self, data_type: str, data: Any) -> None:
        """Store raw TV data.

        Args:
            data_type: Type identifier for the data being stored.
            data: The data to store.
        """
        if data_type not in self.raw_tv_data:
            self.raw_tv_data[data_type] = []

        # Handle list-like data
        if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
            for item in data:
                self.raw_tv_data[data_type].append(self._serialize_plex_item(item))
        else:
            # Handle single items
            self.raw_tv_data[data_type].append(self._serialize_plex_item(data))

        # Save the data to file
        self._save_raw_tv_data()

    def _save_raw_movie_data(self) -> None:
        """Save collected raw movie data to a fixed JSON file, overwriting if it exists."""
        if not self.raw_movie_data:
            return

        try:
            # Use a fixed filename for movie data
            filename = self.output_dir / "plex_raw_movie_data.json"

            # Save the data to file (overwrites if exists)
            with filename.open("w", encoding="utf-8") as f:
                json.dump(self.raw_movie_data, f, indent=2, default=str)

            logger.info(f"Saved raw movie data to {filename}")
        except Exception as e:
            logger.error(f"Error saving raw movie data to file: {e}")

    def _store_raw_movie_data(self, data_type: str, data: Any) -> None:
        """Store raw movie data.

        Args:
            data_type: Type identifier for the data being stored.
            data: The data to store.
        """
        if data_type not in self.raw_movie_data:
            self.raw_movie_data[data_type] = []

        # Handle list-like data
        if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
            for item in data:
                self.raw_movie_data[data_type].append(self._serialize_plex_item(item))
        else:
            # Handle single items
            self.raw_movie_data[data_type].append(self._serialize_plex_item(data))

        # Save the data to file
        self._save_raw_movie_data()

    def _record_raw_data(self, data_type: str, data: Any) -> None:
        """Record raw Plex API data.

        Args:
            data_type: Type identifier for the data being stored.
            data: The raw data to record.
        """
        try:
            # Determine if this is TV or movie data
            if data_type in ["all_shows", "recently_watched_shows"]:
                self._store_raw_tv_data(data_type, data)
            elif data_type in ["all_movies", "recently_watched_movies"]:
                self._store_raw_movie_data(data_type, data)
            else:
                # For other data types, store in both to ensure it's captured
                self._store_raw_tv_data(data_type, data)
                self._store_raw_movie_data(data_type, data)

        except Exception as e:
            logger.warning(f"Error recording raw data for {data_type}: {e}")

    def _save_test_tv_data(self) -> None:
        """Save anonymized test data for TV shows to a fixed JSON file, overwriting if it exists."""
        if not self.test_tv_data:
            return

        try:
            # Use a fixed filename
            filename = self.output_dir / "plex_test_tv_data.json"

            # Save the data to file (overwrites if exists)
            with filename.open("w", encoding="utf-8") as f:
                json.dump(self.test_tv_data, f, indent=2, default=str)

            logger.info(f"Saved anonymized test TV data to {filename}")
        except Exception as e:
            logger.error(f"Error saving test TV data to file: {e}")

    def _store_test_tv_data(self, data_type: str, data: Any) -> None:
        """Store processed test data for TV shows.

        Args:
            data_type: Type identifier for the data being stored.
            data: The processed data to store.
        """
        if data_type not in self.test_tv_data:
            self.test_tv_data[data_type] = data
        else:
            # Append or merge as appropriate for the data type
            if isinstance(self.test_tv_data[data_type], list) and isinstance(data, list):
                self.test_tv_data[data_type].extend(data)
            elif isinstance(self.test_tv_data[data_type], dict) and isinstance(data, dict):
                self.test_tv_data[data_type].update(data)
            else:
                self.test_tv_data[data_type] = data

        # Save the test data
        self._save_test_tv_data()

    def _save_test_movie_data(self) -> None:
        """Save anonymized test data for movies to a fixed JSON file, overwriting if it exists."""
        if not self.test_movie_data:
            return

        try:
            # Use a fixed filename
            filename = self.output_dir / "plex_test_movie_data.json"

            # Save the data to file (overwrites if exists)
            with filename.open("w", encoding="utf-8") as f:
                json.dump(self.test_movie_data, f, indent=2, default=str)

            logger.info(f"Saved anonymized test movie data to {filename}")
        except Exception as e:
            logger.error(f"Error saving test movie data to file: {e}")

    def _store_test_movie_data(self, data_type: str, data: Any) -> None:
        """Store processed test data for movies.

        Args:
            data_type: Type identifier for the data being stored.
            data: The processed data to store.
        """
        if data_type not in self.test_movie_data:
            self.test_movie_data[data_type] = data
        else:
            # Append or merge as appropriate for the data type
            if isinstance(self.test_movie_data[data_type], list) and isinstance(data, list):
                self.test_movie_data[data_type].extend(data)
            elif isinstance(self.test_movie_data[data_type], dict) and isinstance(data, dict):
                self.test_movie_data[data_type].update(data)
            else:
                self.test_movie_data[data_type] = data

        # Save the test data
        self._save_test_movie_data()

    def _anonymize_item(self, item: Any) -> Dict:
        """Create an anonymized version of a Plex item.

        Args:
            item: The Plex item to anonymize.

        Returns:
            An anonymized dictionary representing the item.
        """
        try:
            # Get basic serialized data
            data = self._serialize_plex_item(item)

            # Anonymize common fields
            if "title" in data:
                data["title"] = f"Anonymized {data.get('type', 'Item')}"

            if "username" in data:
                data["username"] = "test_user"

            if "key" in data:
                # Keep structure but anonymize the ID
                key = data["key"]
                match = re.search(r"/(\d+)(/|$)", key)
                if match:
                    anon_id = int(match.group(1)) % 10000 + 30000
                    data["key"] = key.replace(match.group(1), str(anon_id))

            return data
        except Exception as e:
            logger.warning(f"Error anonymizing item: {e}")
            return {"type": "unknown", "error": "anonymization_failed"}

    def _process_shows_for_test(self, shows) -> List[Dict]:
        """Process show data into an anonymized format suitable for test fixtures.

        Args:
            shows: List of show objects.

        Returns:
            List of anonymized show data dictionaries.
        """
        processed = []

        # Iterate through shows
        for item in shows:
            # Process each item, skipping those that fail
            processed_item = None
            try:
                processed_item = self._anonymize_item(item)
            except Exception as e:
                logger.warning(f"Error processing show for test data: {e}")
                continue

            if processed_item:
                processed.append(processed_item)

        return processed

    def _process_movies_for_test(self, movies) -> List[Dict]:
        """Process movie data into an anonymized format suitable for test fixtures.

        Args:
            movies: List of movie objects.

        Returns:
            List of anonymized movie data dictionaries.
        """
        processed = []

        # Process each movie with anonymized data
        for item in movies:
            # Process each item, skipping those that fail
            processed_item = None
            try:
                processed_item = self._anonymize_item(item)
            except Exception as e:
                logger.warning(f"Error processing movie for test data: {e}")
                continue

            if processed_item:
                processed.append(processed_item)

        return processed

    def _process_recent_shows_for_test(self, entries) -> List[Dict]:
        """Process recently watched show data into anonymized test fixtures.

        Args:
            entries: List of recently watched show entries.

        Returns:
            List of anonymized recently watched show data.
        """
        processed = []

        # Get the number of entries to process, max 10
        num_entries = min(len(entries) if entries else 0, 10)

        # Generate synthetic entries
        for i in range(1, num_entries + 1):
            days_ago = i - 1  # Each show was watched on a different recent day
            processed_entry = None

            try:
                processed_entry = {
                    "show_title": f"Recent Show {i}",
                    "episode_title": f"Episode {random.randint(1, 12)}",
                    "season": random.randint(1, 5),
                    "episode": random.randint(1, 12),
                    "duration_minutes": random.randint(20, 60),
                    "viewed_at": (datetime.now() - timedelta(days=days_ago)).isoformat(),
                    "user": "test_user",
                    "year": random.randint(2010, 2022),
                }
            except Exception as e:
                logger.warning(f"Error processing recent show for test data: {e}")
                continue

            processed.append(processed_entry)

        return processed

    def _process_recent_movies_for_test(self, entries) -> List[Dict]:
        """Process recently watched movie data into anonymized test fixtures.

        Args:
            entries: List of recently watched movie entries.

        Returns:
            List of anonymized recently watched movie data.
        """
        processed = []

        # Get the number of entries to process, max 10
        num_entries = min(len(entries) if entries else 0, 10)

        # Generate synthetic entries
        for i in range(1, num_entries + 1):
            days_ago = i - 1  # Each movie was watched on a different recent day
            processed_entry = None

            try:
                processed_entry = {
                    "title": f"Recent Movie {i}",
                    "year": random.randint(2010, 2022),
                    "duration_minutes": random.randint(85, 180),
                    "viewed_at": (datetime.now() - timedelta(days=days_ago)).isoformat(),
                    "user": "test_user",
                    "rating": (
                        round(random.uniform(5.0, 10.0), 1) if random.random() > 0.3 else None
                    ),
                }
            except Exception as e:
                logger.warning(f"Error processing recent movie for test data: {e}")
                continue

            processed.append(processed_entry)

        return processed

    def _process_for_test_data(self, data_type: str, data: Any) -> Any:
        """Process data into an anonymized format suitable for test fixtures.

        Args:
            data_type: Type identifier for the data being processed.
            data: The data to process.

        Returns:
            Processed data in a format suitable for test fixtures.
        """
        # Process based on data type to generate anonymized test fixtures
        if data_type == "all_shows":
            return self._process_shows_for_test(data)
        elif data_type == "all_movies":
            return self._process_movies_for_test(data)
        elif data_type == "recently_watched_shows":
            return self._process_recent_shows_for_test(data)
        elif data_type == "recently_watched_movies":
            return self._process_recent_movies_for_test(data)
        else:
            # For unknown data types, just return a basic anonymized version
            if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
                return [self._anonymize_item(item) for item in data]
            else:
                return self._anonymize_item(data)

    def _record_test_data(self, data_type: str, data: Any) -> None:
        """Record anonymized test data.

        Args:
            data_type: Type identifier for the data being stored.
            data: The data to anonymize and record.
        """
        try:
            # Process the data into an anonymized format
            if data_type in ["all_shows", "recently_watched_shows"]:
                processed_data = self._process_for_test_data(data_type, data)
                self._store_test_tv_data(data_type, processed_data)
            elif data_type in ["all_movies", "recently_watched_movies"]:
                processed_data = self._process_for_test_data(data_type, data)
                self._store_test_movie_data(data_type, processed_data)
            else:
                # For other data types, store in both to ensure it's captured
                processed_data = self._process_for_test_data(data_type, data)
                self._store_test_tv_data(data_type, processed_data)
                self._store_test_movie_data(data_type, processed_data)

        except Exception as e:
            logger.warning(f"Error recording test data for {data_type}: {e}")

    def record_data(self, data_type: str, data: Any) -> None:
        """Record Plex data of a specified type.

        Args:
            data_type: Type identifier for the data being stored (e.g., 'all_shows').
            data: The Plex data to record.
        """
        try:
            if self.mode in ["raw-data", "both"]:
                self._record_raw_data(data_type, data)

            if self.mode in ["test-data", "both"]:
                self._record_test_data(data_type, data)
        except Exception as e:
            logger.warning(f"Error recording data for {data_type}: {e}")
