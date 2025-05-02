# flake8: noqa: N815,ARG005
import json
import random
import re
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from plex_history_report.recorders import PlexDataRecorder


def make_dummy_item():
    class DummyItem:
        def __init__(self):
            self.key = "/test/123"
            self.title = "Test Title"
            self.type = "item"
            self.year = 2022
            self.duration = 120000  # milliseconds
            self.rating = 8.5
            self.viewOffset = 60000  # milliseconds
            self.isWatched = True
            self.viewedAt = datetime(2025, 5, 2, 12, 0, 0)
            self.username = "user1"

        def show(self):
            return SimpleNamespace(title="Show Name")

    return DummyItem()


def test_serialize_basic_item():
    item = make_dummy_item()
    recorder = PlexDataRecorder(mode="raw-data", output_dir=".")
    data = recorder._serialize_plex_item(item)
    assert data["key"] == item.key
    assert data["title"] == item.title
    assert data["year"] == item.year
    assert data["viewOffset"] == item.viewOffset
    assert data["isWatched"] == item.isWatched

    ep = make_dummy_item()
    ep.type = "episode"
    ep.seasonNumber = 1
    ep.index = 2
    data2 = recorder._serialize_plex_item(ep)
    assert data2["seasonNumber"] == 1
    assert data2["index"] == 2
    assert data2.get("showTitle") == "Show Name"


def test_record_raw_and_test_data(tmp_path):
    items = [make_dummy_item() for _ in range(2)]
    outdir = tmp_path / "fixtures"
    recorder = PlexDataRecorder(mode="both", output_dir=str(outdir))

    recorder.record_data("all_shows", items)
    recorder.record_data("recently_watched_shows", items)

    raw_file = outdir / "plex_raw_tv_data.json"
    assert raw_file.exists()
    raw_content = json.loads(raw_file.read_text(encoding="utf-8"))
    assert "all_shows" in raw_content
    assert len(raw_content["all_shows"]) == 2

    test_file = outdir / "plex_test_tv_data.json"
    assert test_file.exists()
    test_content = json.loads(test_file.read_text(encoding="utf-8"))
    assert "all_shows" in test_content
    for entry in test_content["all_shows"]:
        assert isinstance(entry.get("title"), str)


def test_random_anonymized_recent_movies(tmp_path, monkeypatch):
    entries = [object() for _ in range(5)]
    outdir = tmp_path / "fixtures2"
    recorder = PlexDataRecorder(mode="test-data", output_dir=str(outdir))

    monkeypatch.setattr(random, "randint", lambda a, _b: a)  # noqa: ARG005
    monkeypatch.setattr(random, "uniform", lambda a, _b: a)  # noqa: ARG005

    recorder.record_data("recently_watched_movies", entries)
    movie_file = outdir / "plex_test_movie_data.json"
    assert movie_file.exists()
    content = json.loads(movie_file.read_text(encoding="utf-8"))
    recents = content.get("recently_watched_movies", [])
    assert len(recents) == 5
    for idx, m in enumerate(recents, start=1):
        assert m["title"] == f"Recent Movie {idx}"
        assert m["year"] == 2010
        assert "viewed_at" in m


def test_anonymize_item():
    """Test the anonymization of a Plex item."""
    item = make_dummy_item()
    recorder = PlexDataRecorder(mode="test-data", output_dir=".")

    # Test regular anonymization
    anon_data = recorder._anonymize_item(item)
    assert "Anonymized" in anon_data["title"]
    assert anon_data["username"] == "test_user"

    # Test key transformation
    item.key = "/library/metadata/12345"
    anon_data = recorder._anonymize_item(item)
    assert re.search(r"/(\d+)(/|$)", anon_data["key"])
    assert anon_data["key"] != item.key

    # Test error handling with a broken item that still has a type
    class BrokenItem:
        @property
        def type(self):
            return "broken"

        def __getattr__(self, name):
            if name != "type":
                raise AttributeError(f"No {name}")

    broken_item = BrokenItem()
    result = recorder._anonymize_item(broken_item)
    assert result["type"] == "broken"

    # Empty dict case - when an object has no attributes at all
    with patch('logging.Logger.warning'):  # Suppress warning logs
        minimal_obj = object()
        minimal_result = recorder._anonymize_item(minimal_obj)
        assert isinstance(minimal_result, dict)
        assert len(minimal_result) == 0  # Returns an empty dict


def test_process_shows_for_test():
    """Test processing show data for test fixtures."""
    recorder = PlexDataRecorder(mode="test-data", output_dir=".")

    # Mock show data
    shows = [make_dummy_item() for _ in range(3)]

    # Patch the _anonymize_item method to control its output
    with patch.object(recorder, '_anonymize_item') as mock_anonymize:
        mock_anonymize.return_value = {"title": "Anonymous Show", "type": "show"}

        # Call the method
        result = recorder._process_shows_for_test(shows)

        # Check processed result
        assert isinstance(result, list)
        # Test error handling by mocking a failure
        mock_anonymize.side_effect = Exception("Test error")

        # Should handle exceptions gracefully
        result = recorder._process_shows_for_test(shows)
        assert isinstance(result, list)
        assert len(result) == 0  # No items added due to exceptions


def test_process_movies_for_test():
    """Test processing movie data for test fixtures."""
    recorder = PlexDataRecorder(mode="test-data", output_dir=".")

    # Mock movie data
    movies = [make_dummy_item() for _ in range(3)]

    # Patch the _anonymize_item method to control its output
    with patch.object(recorder, '_anonymize_item') as mock_anonymize:
        mock_anonymize.return_value = {"title": "Anonymous Movie", "type": "movie"}

        # Call the method
        result = recorder._process_movies_for_test(movies)

        # Check processed result
        assert isinstance(result, list)
        # Test error handling by mocking a failure
        mock_anonymize.side_effect = Exception("Test error")

        # Should handle exceptions gracefully
        result = recorder._process_movies_for_test(movies)
        assert isinstance(result, list)
        assert len(result) == 0  # No items added due to exceptions


def test_error_handling_in_record_data():
    """Test error handling in record_data method."""
    recorder = PlexDataRecorder(mode="both", output_dir=".")

    # Mock raw_data method to raise exception
    with patch.object(recorder, '_record_raw_data') as mock_raw:
        mock_raw.side_effect = Exception("Raw data error")

        # This should not raise an exception but log a warning
        with patch('logging.Logger.warning') as mock_warning:
            recorder.record_data("test_type", [1, 2, 3])

            # Verify the method was called and exception was logged
            mock_raw.assert_called_once()
            mock_warning.assert_called_with("Error recording data for test_type: Raw data error")


def test_raw_data_for_unknown_type(tmp_path):
    """Test handling of unknown data types in raw data recording."""
    outdir = tmp_path / "fixtures3"
    recorder = PlexDataRecorder(mode="raw-data", output_dir=str(outdir))

    # Use an unknown data type
    unknown_data = [make_dummy_item()]
    recorder.record_data("unknown_type", unknown_data)

    # Check that it was stored in both TV and movie data
    tv_file = outdir / "plex_raw_tv_data.json"
    movie_file = outdir / "plex_raw_movie_data.json"

    assert tv_file.exists()
    assert movie_file.exists()

    tv_data = json.loads(tv_file.read_text(encoding="utf-8"))
    movie_data = json.loads(movie_file.read_text(encoding="utf-8"))

    assert "unknown_type" in tv_data
    assert "unknown_type" in movie_data


def test_test_data_for_unknown_type(tmp_path):
    """Test handling of unknown data types in test data recording."""
    outdir = tmp_path / "fixtures4"
    recorder = PlexDataRecorder(mode="test-data", output_dir=str(outdir))

    # Use an unknown data type
    unknown_data = [make_dummy_item()]
    recorder.record_data("unknown_type", unknown_data)

    # Check that it was stored in both TV and movie data
    tv_file = outdir / "plex_test_tv_data.json"
    movie_file = outdir / "plex_test_movie_data.json"

    assert tv_file.exists()
    assert movie_file.exists()

    tv_data = json.loads(tv_file.read_text(encoding="utf-8"))
    movie_data = json.loads(movie_file.read_text(encoding="utf-8"))

    assert "unknown_type" in tv_data
    assert "unknown_type" in movie_data


def test_serialize_plex_item_error_handling():
    """Test error handling in _serialize_plex_item method."""
    recorder = PlexDataRecorder()

    # Create an object that will raise AttributeError when accessing a key
    class ErrorObject:
        @property
        def type(self):
            return "error_test"

        def __getattr__(self, name):
            if name != "type":
                raise AttributeError(f"No {name}")

    error_obj = ErrorObject()

    # The serialize method should handle the exception and return a dict with the type preserved
    result = recorder._serialize_plex_item(error_obj)
    assert "type" in result
    assert result["type"] == "error_test"


if __name__ == "__main__":
    pytest.main()
