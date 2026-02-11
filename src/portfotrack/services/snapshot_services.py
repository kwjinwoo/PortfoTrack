from collections import defaultdict

from portfotrack.domain.snapshot import Snapshot
from portfotrack.path import SNAPSHOTS_DIR
from portfotrack.storage.json_store.errors import SnapshotNotFoundError
from portfotrack.storage.json_store.snapshot_store import load as store_load
from portfotrack.storage.json_store.snapshot_store import save as store_save
from portfotrack.storage.serialization.snapshot_json import (
    dto_to_snapshot,
    snapshot_to_dto,
)


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


def save_snapshot(snapshot: Snapshot) -> None:
    """Persist a snapshot to disk.

    Converts the Snapshot domain object to a DTO and delegates to the
    storage layer to save it as a JSON file. The file name is determined
    by the snapshot's date and the current schema version.

    Args:
        snapshot: The Snapshot object to persist.
    """
    dto = snapshot_to_dto(snapshot)
    store_save(dto)


def load_latest_snapshot() -> Snapshot:
    """Load the most recent snapshot from disk.

    Scans the snapshots directory for all snapshot files matching the
    pattern `snapshot_*.json`, sorts them by filename in descending order
    (which aligns with date order due to YYYY-MM-DD format), and loads
    the most recent one.

    Returns:
        The Snapshot object loaded from the latest file by date.

    Raises:
        SnapshotNotFoundError: If no snapshot file exists in the directory.
            This error is raised by this function and propagates
            to the caller (including CLI handlers).
        RuntimeError: If the snapshot file structure is invalid.
        TypeError: If snapshot data has unexpected types.
    """
    snapshot_files = sorted(SNAPSHOTS_DIR.glob("snapshot_*.json"), reverse=True)

    if not snapshot_files:
        raise SnapshotNotFoundError(file_name="snapshot_*.json")

    latest_file_name = snapshot_files[0].name
    dto = store_load(latest_file_name)
    return dto_to_snapshot(dto)


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
