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
from portfotrack.services.trend_analysis import compute_asset_trends, load_all_snapshots


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

    def test_empty_directory_returns_empty_list(self, tmp_snapshots_dir: Path) -> None:
        """No snapshot files yields an empty list."""
        result = load_all_snapshots()

        assert result == []

    def test_single_snapshot_returns_one_item(self, tmp_snapshots_dir: Path) -> None:
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

    def test_snapshot_items_are_preserved(self, tmp_snapshots_dir: Path) -> None:
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


class TestComputeAssetTrends:
    """Tests for compute_asset_trends function."""

    def test_empty_snapshots_returns_empty_list(self) -> None:
        """No snapshots yields an empty asset trends list."""
        result = compute_asset_trends([])

        assert result == []

    def test_single_snapshot_single_asset(self) -> None:
        """One snapshot with one asset produces one AssetTrend with one point."""
        snapshot = Snapshot(date="2026-02-12")
        snapshot.add_snapshot_item("us-etf", "S&P500", 5_000_000)

        result = compute_asset_trends([snapshot])

        assert len(result) == 1
        assert result[0].asset_id == "us-etf"
        assert len(result[0].data_points) == 1
        assert result[0].data_points[0].date == "2026-02-12"
        assert result[0].data_points[0].amount == 5_000_000
        assert result[0].data_points[0].ratio == 1.0

    def test_single_snapshot_multiple_assets_ratios_sum_to_one(self) -> None:
        """Multiple assets in one snapshot have ratios summing to 1.0."""
        snapshot = Snapshot(date="2026-02-12")
        snapshot.add_snapshot_item("us-etf", "S&P500", 6_000_000)
        snapshot.add_snapshot_item("gold", "GOLD", 4_000_000)

        result = compute_asset_trends([snapshot])

        assert len(result) == 2
        ratios = [t.data_points[0].ratio for t in result]
        assert sum(ratios) == pytest.approx(1.0)
        # us-etf: 6M / 10M = 0.6
        us_etf = next(t for t in result if t.asset_id == "us-etf")
        assert us_etf.data_points[0].ratio == pytest.approx(0.6)
        # gold: 4M / 10M = 0.4
        gold = next(t for t in result if t.asset_id == "gold")
        assert gold.data_points[0].ratio == pytest.approx(0.4)

    def test_multiple_snapshots_tracks_amount_changes(self) -> None:
        """Two snapshots track amount changes over time for each asset."""
        snap1 = Snapshot(date="2026-02-12")
        snap1.add_snapshot_item("us-etf", "S&P500", 5_000_000)
        snap1.add_snapshot_item("gold", "GOLD", 1_000_000)

        snap2 = Snapshot(date="2026-02-14")
        snap2.add_snapshot_item("us-etf", "S&P500", 5_500_000)
        snap2.add_snapshot_item("gold", "GOLD", 1_200_000)

        result = compute_asset_trends([snap1, snap2])

        us_etf = next(t for t in result if t.asset_id == "us-etf")
        assert len(us_etf.data_points) == 2
        assert us_etf.data_points[0].amount == 5_000_000
        assert us_etf.data_points[1].amount == 5_500_000

    def test_aggregates_multiple_items_same_asset_id(self) -> None:
        """Multiple items with same asset_id are aggregated before trend calc."""
        snapshot = Snapshot(date="2026-02-12")
        snapshot.add_snapshot_item("us-etf", "S&P500", 3_000_000)
        snapshot.add_snapshot_item("us-etf", "Nasdaq100", 2_000_000)
        snapshot.add_snapshot_item("gold", "GOLD", 5_000_000)

        result = compute_asset_trends([snapshot])

        us_etf = next(t for t in result if t.asset_id == "us-etf")
        assert us_etf.data_points[0].amount == 5_000_000
        assert us_etf.data_points[0].ratio == pytest.approx(0.5)

    def test_asset_missing_in_later_snapshot_gets_zero(self) -> None:
        """An asset present in one snapshot but absent in another gets zero."""
        snap1 = Snapshot(date="2026-02-12")
        snap1.add_snapshot_item("us-etf", "S&P500", 5_000_000)
        snap1.add_snapshot_item("gold", "GOLD", 1_000_000)

        snap2 = Snapshot(date="2026-02-14")
        snap2.add_snapshot_item("us-etf", "S&P500", 6_000_000)
        # gold is absent in snap2

        result = compute_asset_trends([snap1, snap2])

        gold = next(t for t in result if t.asset_id == "gold")
        assert len(gold.data_points) == 2
        assert gold.data_points[0].amount == 1_000_000
        assert gold.data_points[1].amount == 0
        assert gold.data_points[1].ratio == pytest.approx(0.0)

    def test_asset_trends_sorted_by_asset_id(self) -> None:
        """Returned asset trends are sorted by asset_id for consistency."""
        snapshot = Snapshot(date="2026-02-12")
        snapshot.add_snapshot_item("gold", "GOLD", 1_000_000)
        snapshot.add_snapshot_item("bond-etf", "Treasury", 2_000_000)
        snapshot.add_snapshot_item("us-etf", "S&P500", 3_000_000)

        result = compute_asset_trends([snapshot])

        asset_ids = [t.asset_id for t in result]
        assert asset_ids == sorted(asset_ids)
