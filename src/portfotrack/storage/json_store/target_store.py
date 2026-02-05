import json
from datetime import datetime
from zoneinfo import ZoneInfo

from portfotrack.path import TARGETS_DIR
from portfotrack.storage.json_store.errors import TargetNotFoundError
from portfotrack.storage.serialization.target_json import TargetAllocationDTO

CURRENT_TARGET_SCHEMA_VERSION = 1


def save(target: TargetAllocationDTO) -> None:
    """Persist the current target allocation to a JSON file.

    This function serializes a target allocation DTO and writes it to a
    versioned JSON file under the targets directory. The file name is
    determined by the current date in the Asia/Seoul timezone and the
    current target schema version.

    The targets directory is created automatically if it does not exist.
    Existing files with the same name will be overwritten.

    Args:
        target: Target allocation data transfer object to persist.
            This object must be JSON-serializable and is expected to be
            represented as a dictionary.
    """
    TARGETS_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    file_name = f"target_{today}_v{CURRENT_TARGET_SCHEMA_VERSION}.json"

    with open(TARGETS_DIR / file_name, "w", encoding="utf-8") as f:
        json.dump(target, f, ensure_ascii=False, indent=2)


def load(file_name: str) -> TargetAllocationDTO:
    """Load a target allocation from a JSON file.

    This function reads a target allocation file from the targets directory,
    validates its structure strictly, and return ``TargetAllocationDTO``.
    The file is assumed to be produced by the corresponding
    save logic; any structural deviation is treated as an invariant violation.

    Args:
        file_name: Name of the target allocation file to load.

    Returns:
        A ``TargetAllocationDTO`` from the file.

    Raises:
        TargetNotFoundError: If the target file does not exist.
        RuntimeError: If the JSON structure violates required invariants,
            indicating file corruption or a bug in the save logic.
        TypeError: If any field has an unexpected type.
    """
    file_path = TARGETS_DIR / file_name
    if not file_path.exists():
        raise TargetNotFoundError(file_name=file_name)

    with open(file_path, encoding="utf-8") as f:
        target_dto: TargetAllocationDTO = json.load(f)

    if not isinstance(target_dto, dict):
        raise RuntimeError(
            "Invariant violated: target file root must be a JSON object. "
            "This indicates a bug in save logic or file corruption."
        )

    if "assets" not in target_dto:
        raise RuntimeError(
            "Invariant violated: missing top-level key 'assets'. "
            "This indicates a bug in save logic."
        )

    assets = target_dto["assets"]
    if not isinstance(assets, list):
        raise TypeError(
            f"Invariant violated: 'assets' must be a list, got {type(assets).__name__}."
        )

    return target_dto
