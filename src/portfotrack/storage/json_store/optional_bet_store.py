import json
from datetime import datetime
from zoneinfo import ZoneInfo

from portfotrack.path import OPTIONAL_BETS_DIR
from portfotrack.storage.json_store.errors import OptionalBetNotFoundError
from portfotrack.storage.serialization.optional_bet_json import OptionalBetSnapshotDTO

CURRENT_OPTIONAL_BET_SCHEMA_VERSION = 1


def save_to_file(dto: OptionalBetSnapshotDTO, file_name: str) -> None:
    """Persist an optional bet snapshot to a JSON file with the given name.

    Writes the DTO to the optional bets directory using the exact file name
    provided. The directory is created automatically if it does not exist.

    Args:
        dto: Optional bet snapshot DTO to persist.
        file_name: Target file name within the optional bets directory.
    """
    OPTIONAL_BETS_DIR.mkdir(parents=True, exist_ok=True)

    with open(OPTIONAL_BETS_DIR / file_name, "w", encoding="utf-8") as f:
        json.dump(dto, f, ensure_ascii=False, indent=2)


def save(dto: OptionalBetSnapshotDTO) -> None:
    """Persist an optional bet snapshot to a versioned JSON file.

    The file name is determined by the current date in Asia/Seoul timezone
    and the current schema version.

    Args:
        dto: Optional bet snapshot DTO to persist.
    """
    today = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    file_name = f"optional_bet_{today}_v{CURRENT_OPTIONAL_BET_SCHEMA_VERSION}.json"
    save_to_file(dto, file_name)


def load(file_name: str) -> OptionalBetSnapshotDTO:
    """Load an optional bet snapshot from a JSON file.

    Reads and validates the structure of the file. The file is assumed to
    be produced by the corresponding save logic.

    Args:
        file_name: Name of the optional bet file to load.

    Returns:
        An OptionalBetSnapshotDTO from the file.

    Raises:
        OptionalBetNotFoundError: If the file does not exist.
        RuntimeError: If the JSON structure violates required invariants.
        TypeError: If any field has an unexpected type.
    """
    file_path = OPTIONAL_BETS_DIR / file_name
    if not file_path.exists():
        raise OptionalBetNotFoundError(file_name=file_name)

    with open(file_path, encoding="utf-8") as f:
        dto: OptionalBetSnapshotDTO = json.load(f)

    if not isinstance(dto, dict):
        raise RuntimeError(
            "Invariant violated: optional bet file root must be a JSON object. "
            "This indicates a bug in save logic or file corruption."
        )

    for key in ("date", "currency", "items"):
        if key not in dto:
            raise RuntimeError(
                f"Invariant violated: missing top-level key '{key}'. "
                "This indicates a bug in save logic."
            )

    items = dto["items"]
    if not isinstance(items, list):
        raise TypeError(
            f"Invariant violated: 'items' must be a list, "
            f"got {type(items).__name__}."
        )

    return dto
