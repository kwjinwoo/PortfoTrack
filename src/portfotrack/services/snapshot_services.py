from collections import defaultdict

from portfotrack.domain.snapshot import Snapshot


def init_snapshot() -> Snapshot:
    """Create a new, empty Snapshot.

    Returns:
        A fresh `Snapshot` instance ready for items to be added.
    """
    return Snapshot()


def add_item_to_snapshot(
    snapshot: Snapshot, asset_id: str, label: str, amount: int
) -> Snapshot:
    """Add an item to `snapshot` and return the same snapshot.

    This is a thin convenience wrapper around `Snapshot.add_snapshot_item`.

    Args:
        snapshot: The `Snapshot` to modify.
        asset_id: Asset class identifier for the new item.
        label: Human-readable label for the holding.
        amount: Absolute amount in the snapshot currency.

    Returns:
        The same `Snapshot` instance passed in (mutated).
    """
    snapshot.add_snapshot_item(asset_id, label, amount)
    return snapshot


def aggregate_snapshot(snapshot: Snapshot) -> dict[str, int]:
    """Aggregate snapshot items by asset_id, summing their amounts.

    Multiple SnapshotItems may share the same asset_id (e.g., several
    holdings within one asset class). This function collapses them into
    a single total per asset_id, producing the asset-class-level view
    needed for allocation comparison and drift detection.

    Args:
        snapshot: An immutable portfolio snapshot containing line items
            to aggregate.

    Returns:
        A mapping from asset_id to the summed amount across all items
        sharing that id. Returns an empty dict if the snapshot has no items.
    """
    totals: dict[str, int] = defaultdict(int)
    for item in snapshot.items:
        totals[item.asset_id] += item.amount
    return dict(totals)
