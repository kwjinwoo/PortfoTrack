"""Tests for trend analysis service — load_all_snapshots.

Covers:
- Loading all snapshots from disk sorted by date
- Empty directory returns empty list
- Multiple snapshots sorted ascending
"""

import json
from pathlib import Path

import pytest

import portfotrack.path as path_mod
import portfotrack.services.trend_analysis as trend_svc
import portfotrack.storage.json_store.snapshot_store as snap_store
from portfotrack.domain.snapshot import Snapshot
from portfotrack.services.trend_analysis import load_all_snapshots


@pytest.fixture()
def tmp_snapshots_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect SNAPSHOTS_DIR to a temp directory."""
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()

    monkeypatch.setattr(path_mod, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(snap_store, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(trend_svc, "SNAPSHOTS_DIR", snapshots_dir)

    return snapshots_dir


def _write_snapshot(snapshots_dir: Path, date: str, items: list) -> None:
    """Write a snapshot JSON file to the given directory."""
    dto = {"date": date, "currency": "KRW", "items": items}
    file_name = f"snapshot_{date}_v1.json"
    with open(snapshots_dir / file_name, "w", encoding="utf-8") as f:
        json.dump(dto, f, ensure_ascii=False, indent=2)


class TestLoadAllSnapshots:
    """Tests for load_all_snapshots function."""

    def test_empty_directory_returns_empty_list(
        self, tmp_snapshots_dir: Path
    ) -> None:
        """No snapshot files yields an empty list."""
        result = load_all_snapshots()

        assert result == []

    def test_single_snapshot_returns_one_item(
        self, tmp_snapshots_dir: Path
    ) -> None:
        """One snapshot file yields a list with one Snapshot."""
        _write_snapshot(
            tmp_snapshots_dir,
            "2026-02-12",
            [{"asset_id": "us-etf", "label": "S&P500", "amount": 5_000_000}],
        )

        result = load_all_snapshots()

        assert len(result) == 1
        assert isinstance(result[0], Snapshot)
        assert result[0].date == "2026-02-12"

    def test_multiple_snapshots_sorted_ascending_by_date(
        self, tmp_snapshots_dir: Path
    ) -> None:
        """Multiple snapshots are returned sorted by date ascending."""
        _write_snapshot(
            tmp_snapshots_dir,
            "2026-02-14",
            [{"asset_id": "us-etf", "label": "S&P500", "amount": 5_300_000}],
        )
        _write_snapshot(
            tmp_snapshots_dir,
            "2026-02-12",
            [{"asset_id": "us-etf", "label": "S&P500", "amount": 5_000_000}],
        )
        _write_snapshot(
            tmp_snapshots_dir,
            "2026-02-13",
            [{"asset_id": "us-etf", "label": "S&P500", "amount": 5_100_000}],
        )

        result = load_all_snapshots()

        assert len(result) == 3
        assert result[0].date == "2026-02-12"
        assert result[1].date == "2026-02-13"
        assert result[2].date == "2026-02-14"

    def test_snapshot_items_are_preserved(
        self, tmp_snapshots_dir: Path
    ) -> None:
        """Loaded snapshots contain correct items."""
        _write_snapshot(
            tmp_snapshots_dir,
            "2026-02-12",
            [
                {"asset_id": "us-etf", "label": "S&P500", "amount": 5_000_000},
                {"asset_id": "gold", "label": "GOLD", "amount": 900_000},
            ],
        )

        result = load_all_snapshots()

        assert len(result) == 1
        assert len(result[0].items) == 2
        assert result[0].items[0].asset_id == "us-etf"
        assert result[0].items[1].asset_id == "gold"
