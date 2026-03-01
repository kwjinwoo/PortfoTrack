"""Tests for optional bet trend analysis service.

Covers:
- compute_optional_bet_asset_trends: per-asset time-series computation
- compute_optional_bet_trend: full optional bet trend with totals
"""

import pytest

from portfotrack.domain.optional_bet import OptionalBetSnapshot
from portfotrack.services.optional_bet_trend_analysis import (
    compute_optional_bet_asset_trends,
    compute_optional_bet_trend,
)


class TestComputeOptionalBetAssetTrends:
    """Tests for compute_optional_bet_asset_trends function."""

    def test_empty_snapshots_returns_empty_list(self) -> None:
        """No snapshots yields an empty asset trends list."""
        result = compute_optional_bet_asset_trends([])

        assert result == []

    def test_single_snapshot_single_asset(self) -> None:
        """One snapshot with one asset produces one AssetTrend with one point."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        result = compute_optional_bet_asset_trends([snapshot])

        assert len(result) == 1
        assert result[0].asset_id == "bitcoin"
        assert result[0].asset_name == "Bitcoin"
        assert len(result[0].data_points) == 1
        assert result[0].data_points[0].date == "2026-03-01"
        assert result[0].data_points[0].amount == 1_000_000
        assert result[0].data_points[0].ratio == 1.0

    def test_single_snapshot_multiple_assets_ratios_sum_to_one(self) -> None:
        """Multiple assets in one snapshot have ratios summing to 1.0."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 6_000_000)
        snapshot.add_item("ethereum", "Ethereum", 0.03, 4_000_000)

        result = compute_optional_bet_asset_trends([snapshot])

        assert len(result) == 2
        ratios = [t.data_points[0].ratio for t in result]
        assert sum(ratios) == pytest.approx(1.0)
        bitcoin = next(t for t in result if t.asset_id == "bitcoin")
        assert bitcoin.data_points[0].ratio == pytest.approx(0.6)
        ethereum = next(t for t in result if t.asset_id == "ethereum")
        assert ethereum.data_points[0].ratio == pytest.approx(0.4)

    def test_multiple_snapshots_tracks_amount_changes(self) -> None:
        """Two snapshots track amount changes over time for each asset."""
        snap1 = OptionalBetSnapshot(date="2026-03-01")
        snap1.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
        snap1.add_item("ethereum", "Ethereum", 0.03, 500_000)

        snap2 = OptionalBetSnapshot(date="2026-03-02")
        snap2.add_item("bitcoin", "Bitcoin", 0.05, 1_200_000)
        snap2.add_item("ethereum", "Ethereum", 0.03, 600_000)

        result = compute_optional_bet_asset_trends([snap1, snap2])

        bitcoin = next(t for t in result if t.asset_id == "bitcoin")
        assert len(bitcoin.data_points) == 2
        assert bitcoin.data_points[0].amount == 1_000_000
        assert bitcoin.data_points[1].amount == 1_200_000

    def test_asset_missing_in_later_snapshot_gets_zero(self) -> None:
        """An asset present in one snapshot but absent in another gets zero."""
        snap1 = OptionalBetSnapshot(date="2026-03-01")
        snap1.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
        snap1.add_item("ethereum", "Ethereum", 0.03, 500_000)

        snap2 = OptionalBetSnapshot(date="2026-03-02")
        snap2.add_item("bitcoin", "Bitcoin", 0.05, 1_200_000)
        # ethereum is absent in snap2

        result = compute_optional_bet_asset_trends([snap1, snap2])

        ethereum = next(t for t in result if t.asset_id == "ethereum")
        assert len(ethereum.data_points) == 2
        assert ethereum.data_points[0].amount == 500_000
        assert ethereum.data_points[1].amount == 0
        assert ethereum.data_points[1].ratio == pytest.approx(0.0)

    def test_asset_trends_sorted_by_asset_id(self) -> None:
        """Returned asset trends are sorted by asset_id for consistency."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("ethereum", "Ethereum", 0.03, 500_000)
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        result = compute_optional_bet_asset_trends([snapshot])

        asset_ids = [t.asset_id for t in result]
        assert asset_ids == sorted(asset_ids)

    def test_asset_name_uses_item_name(self) -> None:
        """Asset name is derived from the optional bet item name field."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "비트코인", 0.05, 1_000_000)

        result = compute_optional_bet_asset_trends([snapshot])

        assert result[0].asset_name == "비트코인"

    def test_asset_name_uses_latest_name(self) -> None:
        """When name changes across snapshots, uses the most recent one."""
        snap1 = OptionalBetSnapshot(date="2026-03-01")
        snap1.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        snap2 = OptionalBetSnapshot(date="2026-03-02")
        snap2.add_item("bitcoin", "비트코인", 0.05, 1_200_000)

        result = compute_optional_bet_asset_trends([snap1, snap2])

        assert result[0].asset_name == "비트코인"


class TestComputeOptionalBetTrend:
    """Tests for compute_optional_bet_trend function."""

    def test_empty_snapshots_returns_empty_trend(self) -> None:
        """No snapshots yields empty asset_trends and total_data_points."""
        result = compute_optional_bet_trend([])

        assert result.asset_trends == []
        assert result.total_data_points == []

    def test_single_snapshot_total_amount(self) -> None:
        """One snapshot produces one total data point with correct sum."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
        snapshot.add_item("ethereum", "Ethereum", 0.03, 500_000)

        result = compute_optional_bet_trend([snapshot])

        assert len(result.total_data_points) == 1
        assert result.total_data_points[0].date == "2026-03-01"
        assert result.total_data_points[0].total_amount == 1_500_000

    def test_multiple_snapshots_track_total_changes(self) -> None:
        """Multiple snapshots track total optional bet value over time."""
        snap1 = OptionalBetSnapshot(date="2026-03-01")
        snap1.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
        snap1.add_item("ethereum", "Ethereum", 0.03, 500_000)

        snap2 = OptionalBetSnapshot(date="2026-03-02")
        snap2.add_item("bitcoin", "Bitcoin", 0.05, 1_200_000)
        snap2.add_item("ethereum", "Ethereum", 0.03, 600_000)

        result = compute_optional_bet_trend([snap1, snap2])

        assert len(result.total_data_points) == 2
        assert result.total_data_points[0].total_amount == 1_500_000
        assert result.total_data_points[1].total_amount == 1_800_000

    def test_includes_asset_trends(self) -> None:
        """PortfolioTrend includes per-asset trends alongside totals."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
        snapshot.add_item("ethereum", "Ethereum", 0.03, 500_000)

        result = compute_optional_bet_trend([snapshot])

        assert len(result.asset_trends) == 2
        asset_ids = [t.asset_id for t in result.asset_trends]
        assert "bitcoin" in asset_ids
        assert "ethereum" in asset_ids

    def test_single_snapshot_change_pct_is_zero(self) -> None:
        """First (and only) snapshot has change_pct of 0.0."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        result = compute_optional_bet_trend([snapshot])

        assert result.total_data_points[0].change_pct == pytest.approx(0.0)

    def test_multi_snapshot_change_pct(self) -> None:
        """change_pct reflects percentage change from previous snapshot total."""
        snap1 = OptionalBetSnapshot(date="2026-03-01")
        snap1.add_item("bitcoin", "Bitcoin", 0.05, 100)

        snap2 = OptionalBetSnapshot(date="2026-03-02")
        snap2.add_item("bitcoin", "Bitcoin", 0.05, 120)

        snap3 = OptionalBetSnapshot(date="2026-03-03")
        snap3.add_item("bitcoin", "Bitcoin", 0.05, 90)

        result = compute_optional_bet_trend([snap1, snap2, snap3])

        assert result.total_data_points[0].change_pct == pytest.approx(0.0)
        assert result.total_data_points[1].change_pct == pytest.approx(20.0)
        assert result.total_data_points[2].change_pct == pytest.approx(-25.0)

    def test_zero_total_snapshot_change_pct(self) -> None:
        """change_pct is 0.0 when previous snapshot total is zero."""
        snap1 = OptionalBetSnapshot(date="2026-03-01")
        # Empty snapshot has total 0

        snap2 = OptionalBetSnapshot(date="2026-03-02")
        snap2.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        result = compute_optional_bet_trend([snap1, snap2])

        assert result.total_data_points[0].change_pct == pytest.approx(0.0)
        assert result.total_data_points[1].change_pct == pytest.approx(0.0)
