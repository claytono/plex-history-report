import json
import random
from datetime import datetime
from types import SimpleNamespace

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

    monkeypatch.setattr(random, "randint", lambda a, _b: a)
    monkeypatch.setattr(random, "uniform", lambda a, _b: a)

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


if __name__ == "__main__":
    pytest.main()
