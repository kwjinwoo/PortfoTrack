"""Optional bet trend analysis service.

Computes time-series trend data for per-asset and total-level
analysis from multiple optional bet snapshots.
Reuses the existing AssetTrend / PortfolioTrend domain models.
"""

from portfotrack.domain.optional_bet import OptionalBetSnapshot
from portfotrack.domain.trend import (
    AssetTrend,
    AssetTrendPoint,
    PortfolioTrend,
    PortfolioTrendPoint,
    compute_change_pct,
)


def compute_optional_bet_asset_trends(
    snapshots: list[OptionalBetSnapshot],
) -> list[AssetTrend]:
    """Compute per-asset time-series trend data from optional bet snapshots.

    For each snapshot, items are indexed by ``asset_id``. Each asset's
    amount and allocation ratio are tracked across all snapshot dates.
    Assets that appear in some snapshots but not others receive a zero
    amount and zero ratio for the missing dates.

    Args:
        snapshots: Chronologically ordered list of optional bet snapshots.

    Returns:
        A list of AssetTrend objects sorted by asset_id, each containing
        one data point per snapshot date. Returns an empty list if no
        snapshots are provided.
    """
    if not snapshots:
        return []

    # Collect all unique asset_ids and per-snapshot data
    all_asset_ids: set[str] = set()
    per_snapshot_amounts: list[dict[str, int]] = []
    totals: list[int] = []
    asset_names: dict[str, str] = {}

    for snapshot in snapshots:
        amounts: dict[str, int] = {}
        for item in snapshot.items:
            amounts[item.asset_id] = item.amount
            asset_names[item.asset_id] = item.name
        all_asset_ids.update(amounts.keys())
        per_snapshot_amounts.append(amounts)
        totals.append(snapshot.total_amount())

    sorted_asset_ids = sorted(all_asset_ids)

    # Build per-asset trend data
    asset_trends: list[AssetTrend] = []
    for asset_id in sorted_asset_ids:
        data_points: list[AssetTrendPoint] = []
        for i, snapshot in enumerate(snapshots):
            amount = per_snapshot_amounts[i].get(asset_id, 0)
            total = totals[i]
            ratio = amount / total if total > 0 else 0.0
            data_points.append(
                AssetTrendPoint(date=snapshot.date, amount=amount, ratio=ratio)
            )

        asset_trends.append(
            AssetTrend(
                asset_id=asset_id,
                asset_name=asset_names[asset_id],
                data_points=data_points,
            )
        )

    return asset_trends


def compute_optional_bet_trend(
    snapshots: list[OptionalBetSnapshot],
) -> PortfolioTrend:
    """Compute complete optional bet trend data from a list of snapshots.

    Combines per-asset trends with total optional bet value observations
    to produce a single PortfolioTrend suitable for rendering charts.

    Args:
        snapshots: Chronologically ordered list of optional bet snapshots.

    Returns:
        A PortfolioTrend containing per-asset trends and total
        data points. Returns empty collections if no snapshots are
        provided.
    """
    asset_trends = compute_optional_bet_asset_trends(snapshots)

    total_data_points: list[PortfolioTrendPoint] = []
    prev_total = 0
    for i, snapshot in enumerate(snapshots):
        total = snapshot.total_amount()
        change_pct = compute_change_pct(prev_total, total) if i > 0 else 0.0
        total_data_points.append(
            PortfolioTrendPoint(
                date=snapshot.date, total_amount=total, change_pct=change_pct
            )
        )
        prev_total = total

    return PortfolioTrend(
        asset_trends=asset_trends, total_data_points=total_data_points
    )
