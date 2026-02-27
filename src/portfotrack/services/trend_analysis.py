"""Trend analysis service.

Loads all snapshots from disk and computes time-series trend data
for per-asset and portfolio-level analysis.
"""

from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.trend import (
    AssetTrend,
    AssetTrendPoint,
    PortfolioTrend,
    PortfolioTrendPoint,
    compute_change_pct,
)
from portfotrack.path import SNAPSHOTS_DIR
from portfotrack.services.snapshot_services import aggregate_snapshot
from portfotrack.storage.json_store.snapshot_store import load as store_load
from portfotrack.storage.serialization.snapshot_json import dto_to_snapshot


def load_all_snapshots() -> list[Snapshot]:
    """Load all snapshots from disk, sorted by date ascending.

    Scans the snapshots directory for files matching the
    ``snapshot_*.json`` glob pattern, loads each one, and returns
    them ordered chronologically.

    Returns:
        A list of Snapshot domain objects sorted by date ascending.
        Returns an empty list if no snapshot files exist.
    """
    snapshot_files = sorted(SNAPSHOTS_DIR.glob("snapshot_*.json"))

    snapshots: list[Snapshot] = []
    for file_path in snapshot_files:
        dto = store_load(file_path.name)
        snapshot = dto_to_snapshot(dto)
        snapshots.append(snapshot)

    return snapshots


def compute_asset_trends(snapshots: list[Snapshot]) -> list[AssetTrend]:
    """Compute per-asset time-series trend data from a list of snapshots.

    For each snapshot, items are aggregated by asset_id. Each asset's
    amount and allocation ratio are tracked across all snapshot dates.
    Assets that appear in some snapshots but not others receive a zero
    amount and zero ratio for the missing dates.

    Args:
        snapshots: Chronologically ordered list of snapshots.

    Returns:
        A list of AssetTrend objects sorted by asset_id, each containing
        one data point per snapshot date. Returns an empty list if no
        snapshots are provided.
    """
    if not snapshots:
        return []

    # Collect all unique asset_ids across all snapshots
    all_asset_ids: set[str] = set()
    aggregated: list[dict[str, int]] = []
    totals: list[int] = []

    for snapshot in snapshots:
        agg = aggregate_snapshot(snapshot)
        aggregated.append(agg)
        all_asset_ids.update(agg.keys())
        totals.append(sum(agg.values()))

    sorted_asset_ids = sorted(all_asset_ids)

    # Build per-asset trend data
    asset_trends: list[AssetTrend] = []
    for asset_id in sorted_asset_ids:
        data_points: list[AssetTrendPoint] = []
        for i, snapshot in enumerate(snapshots):
            amount = aggregated[i].get(asset_id, 0)
            total = totals[i]
            ratio = amount / total if total > 0 else 0.0
            data_points.append(
                AssetTrendPoint(date=snapshot.date, amount=amount, ratio=ratio)
            )

        # Derive asset_name from the first snapshot item that has this asset_id
        asset_name = _resolve_asset_name(asset_id, snapshots)
        asset_trends.append(
            AssetTrend(
                asset_id=asset_id, asset_name=asset_name, data_points=data_points
            )
        )

    return asset_trends


def _resolve_asset_name(asset_id: str, snapshots: list[Snapshot]) -> str:
    """Resolve a human-readable name for an asset_id from snapshot items.

    Uses the asset_id itself as the name since snapshots do not carry
    asset-level metadata beyond label. This keeps the domain pure;
    richer names can be derived from target allocations at the web layer.

    Args:
        asset_id: The asset class identifier.
        snapshots: Available snapshots (unused in current implementation).

    Returns:
        The asset_id string as a fallback name.
    """
    return asset_id


def compute_portfolio_trend(snapshots: list[Snapshot]) -> PortfolioTrend:
    """Compute complete portfolio trend data from a list of snapshots.

    Combines per-asset trends with total portfolio value observations
    to produce a single PortfolioTrend suitable for rendering all
    three chart types (asset percentage, asset amount, total amount).

    Args:
        snapshots: Chronologically ordered list of snapshots.

    Returns:
        A PortfolioTrend containing per-asset trends and total
        portfolio data points. Returns empty collections if no
        snapshots are provided.
    """
    asset_trends = compute_asset_trends(snapshots)

    total_data_points: list[PortfolioTrendPoint] = []
    prev_total = 0
    for i, snapshot in enumerate(snapshots):
        agg = aggregate_snapshot(snapshot)
        total = sum(agg.values())
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
