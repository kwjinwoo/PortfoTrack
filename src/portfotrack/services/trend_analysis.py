"""Trend analysis service.

Loads all snapshots from disk and computes time-series trend data
for per-asset and portfolio-level analysis.
"""

from portfotrack.domain.snapshot import Snapshot
from portfotrack.path import SNAPSHOTS_DIR
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
