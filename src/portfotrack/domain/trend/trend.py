"""Trend domain models for tracking portfolio changes over time.

Provides immutable data structures for representing asset-level and
portfolio-level time-series data derived from snapshots.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetTrendPoint:
    """A single observation of an asset class at a specific point in time.

    Captures the absolute amount and allocation ratio for one asset
    class in one snapshot. Multiple AssetTrendPoints ordered by date
    form a time series for that asset.

    Attributes:
        date: ISO-format date string (YYYY-MM-DD) of the observation.
        amount: Absolute amount in the snapshot currency (KRW).
        ratio: Allocation ratio within the total portfolio (0.0–1.0).
    """

    date: str
    amount: int
    ratio: float


@dataclass(frozen=True)
class AssetTrend:
    """Time-series trend data for a single asset class.

    Aggregates multiple AssetTrendPoints across snapshots to represent
    how a specific asset class has evolved over time in both absolute
    amount and relative allocation.

    Attributes:
        asset_id: Stable identifier of the asset class.
        asset_name: Human-readable name of the asset class.
        data_points: Chronologically ordered list of observations.
    """

    asset_id: str
    asset_name: str
    data_points: list[AssetTrendPoint]
