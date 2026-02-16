"""Tests for PortfolioTrend domain model.

Covers:
- PortfolioTrendPoint creation and immutability
- PortfolioTrend creation with asset trends and total data points
- Edge cases: empty asset trends, empty total data points
"""

import pytest

from portfotrack.domain.trend import (
    AssetTrend,
    AssetTrendPoint,
    PortfolioTrend,
    PortfolioTrendPoint,
)


class TestPortfolioTrendPoint:
    """Tests for PortfolioTrendPoint dataclass."""

    def test_create_with_valid_data(self) -> None:
        """PortfolioTrendPoint holds date and total_amount."""
        point = PortfolioTrendPoint(date="2026-02-12", total_amount=60_000_000)

        assert point.date == "2026-02-12"
        assert point.total_amount == 60_000_000

    def test_frozen_cannot_modify_fields(self) -> None:
        """PortfolioTrendPoint is frozen; field assignment raises an error."""
        point = PortfolioTrendPoint(date="2026-02-12", total_amount=60_000_000)

        with pytest.raises(AttributeError):
            point.total_amount = 70_000_000  # type: ignore[misc]

    def test_zero_total_amount(self) -> None:
        """PortfolioTrendPoint accepts zero total_amount."""
        point = PortfolioTrendPoint(date="2026-02-12", total_amount=0)

        assert point.total_amount == 0


class TestPortfolioTrend:
    """Tests for PortfolioTrend dataclass."""

    def test_create_with_asset_trends_and_totals(self) -> None:
        """PortfolioTrend holds asset_trends and total_data_points."""
        asset_trends = [
            AssetTrend(
                asset_id="us-etf",
                asset_name="USStockETF",
                data_points=[
                    AssetTrendPoint(date="2026-02-12", amount=8_000_000, ratio=0.5),
                ],
            ),
            AssetTrend(
                asset_id="gold",
                asset_name="Gold",
                data_points=[
                    AssetTrendPoint(date="2026-02-12", amount=900_000, ratio=0.06),
                ],
            ),
        ]
        totals = [
            PortfolioTrendPoint(date="2026-02-12", total_amount=16_000_000),
        ]

        trend = PortfolioTrend(asset_trends=asset_trends, total_data_points=totals)

        assert len(trend.asset_trends) == 2
        assert trend.asset_trends[0].asset_id == "us-etf"
        assert len(trend.total_data_points) == 1
        assert trend.total_data_points[0].total_amount == 16_000_000

    def test_create_with_empty_data(self) -> None:
        """PortfolioTrend can be created with empty lists."""
        trend = PortfolioTrend(asset_trends=[], total_data_points=[])

        assert trend.asset_trends == []
        assert trend.total_data_points == []

    def test_frozen_cannot_modify_fields(self) -> None:
        """PortfolioTrend is frozen; field assignment raises an error."""
        trend = PortfolioTrend(asset_trends=[], total_data_points=[])

        with pytest.raises(AttributeError):
            trend.asset_trends = []  # type: ignore[misc]
