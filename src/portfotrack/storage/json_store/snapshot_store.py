import json
from datetime import datetime
from zoneinfo import ZoneInfo

from portfotrack.path import SNAPSHOTS_DIR
from portfotrack.storage.json_store.errors import SnapshotNotFoundError
from portfotrack.storage.serialization.snapshot_json import SnapshotDTO

CURRENT_SNAPSHOT_SCHEMA_VERSION = 1


def save_to_file(snapshot: SnapshotDTO, file_name: str) -> None:
    """Persist a snapshot to a JSON file with the given file name.

    Writes the snapshot DTO to the snapshots directory using the exact
    file name provided. This enables overwriting a specific existing
    snapshot file (e.g., when editing a historical snapshot).

    The snapshots directory is created automatically if it does not exist.
    Existing files with the same name will be overwritten.

    Args:
        snapshot: Snapshot data transfer object to persist.
        file_name: Target file name within the snapshots directory.
    """
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(SNAPSHOTS_DIR / file_name, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)


def save(snapshot: SnapshotDTO) -> None:
    """Persist a snapshot to a JSON file.

    This function serializes a snapshot DTO and writes it to a versioned
    JSON file under the snapshots directory. The file name is determined
    by the current date in the Asia/Seoul timezone and the current
    snapshot schema version.

    The snapshots directory is created automatically if it does not exist.
    Existing files with the same name will be overwritten.

    Args:
        snapshot: Snapshot data transfer object to persist.
            This object must be JSON-serializable and is expected to be
            represented as a dictionary.
    """
    today = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    file_name = f"snapshot_{today}_v{CURRENT_SNAPSHOT_SCHEMA_VERSION}.json"
    save_to_file(snapshot, file_name)


def load(file_name: str) -> SnapshotDTO:
    """Load a snapshot from a JSON file.

    This function reads a snapshot file from the snapshots directory,
    validates its structure strictly, and returns a ``SnapshotDTO``.
    The file is assumed to be produced by the corresponding save logic;
    any structural deviation is treated as an invariant violation.

    Args:
        file_name: Name of the snapshot file to load.

    Returns:
        A ``SnapshotDTO`` from the file.

    Raises:
        SnapshotNotFoundError: If the snapshot file does not exist.
        RuntimeError: If the JSON structure violates required invariants,
            indicating file corruption or a bug in the save logic.
        TypeError: If any field has an unexpected type.
    """
    file_path = SNAPSHOTS_DIR / file_name
    if not file_path.exists():
        raise SnapshotNotFoundError(file_name=file_name)

    with open(file_path, encoding="utf-8") as f:
        snapshot_dto: SnapshotDTO = json.load(f)

    if not isinstance(snapshot_dto, dict):
        raise RuntimeError(
            "Invariant violated: snapshot file root must be a JSON object. "
            "This indicates a bug in save logic or file corruption."
        )

    for key in ("date", "currency", "items"):
        if key not in snapshot_dto:
            raise RuntimeError(
                f"Invariant violated: missing top-level key '{key}'. "
                "This indicates a bug in save logic."
            )

    items = snapshot_dto["items"]
    if not isinstance(items, list):
        raise TypeError(
            f"Invariant violated: 'items' must be a list, got {type(items).__name__}."
        )

    return snapshot_dto
