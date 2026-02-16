"""Tests for AssetTrend domain model.

Covers:
- AssetTrendPoint creation and immutability
- AssetTrend creation with data points
- Edge cases: empty data points
"""

import pytest

from portfotrack.domain.trend import AssetTrend, AssetTrendPoint


class TestAssetTrendPoint:
    """Tests for AssetTrendPoint dataclass."""

    def test_create_with_valid_data(self) -> None:
        """AssetTrendPoint can be instantiated with date, amount, and ratio."""
        point = AssetTrendPoint(date="2026-02-12", amount=5_000_000, ratio=0.5)

        assert point.date == "2026-02-12"
        assert point.amount == 5_000_000
        assert point.ratio == 0.5

    def test_frozen_cannot_modify_fields(self) -> None:
        """AssetTrendPoint is frozen; field assignment raises an error."""
        point = AssetTrendPoint(date="2026-02-12", amount=5_000_000, ratio=0.5)

        with pytest.raises(AttributeError):
            point.date = "2026-02-14"  # type: ignore[misc]

    def test_zero_amount_and_ratio(self) -> None:
        """AssetTrendPoint accepts zero values for amount and ratio."""
        point = AssetTrendPoint(date="2026-02-12", amount=0, ratio=0.0)

        assert point.amount == 0
        assert point.ratio == 0.0


class TestAssetTrend:
    """Tests for AssetTrend dataclass."""

    def test_create_with_data_points(self) -> None:
        """AssetTrend can be created with asset_id, name, and data points."""
        points = [
            AssetTrendPoint(date="2026-02-12", amount=5_000_000, ratio=0.5),
            AssetTrendPoint(date="2026-02-14", amount=5_300_000, ratio=0.52),
        ]
        trend = AssetTrend(
            asset_id="us-etf", asset_name="USStockETF", data_points=points
        )

        assert trend.asset_id == "us-etf"
        assert trend.asset_name == "USStockETF"
        assert len(trend.data_points) == 2
        assert trend.data_points[0].date == "2026-02-12"
        assert trend.data_points[1].date == "2026-02-14"

    def test_create_with_empty_data_points(self) -> None:
        """AssetTrend can be created with an empty data_points list."""
        trend = AssetTrend(asset_id="gold", asset_name="Gold", data_points=[])

        assert trend.asset_id == "gold"
        assert trend.data_points == []

    def test_frozen_cannot_modify_fields(self) -> None:
        """AssetTrend is frozen; field assignment raises an error."""
        trend = AssetTrend(asset_id="gold", asset_name="Gold", data_points=[])

        with pytest.raises(AttributeError):
            trend.asset_id = "bond"  # type: ignore[misc]
