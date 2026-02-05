import json
from datetime import datetime
from zoneinfo import ZoneInfo

from portfotrack.domain.asset import Asset
from portfotrack.domain.target_allocation import TargetAllocation, Tolerance
from portfotrack.path import TARGETS_DIR
from portfotrack.storage.json_store.errors import TargetNotFoundError
from portfotrack.storage.serialization.target_json import AssetDTO, TargetAllocationDTO

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


def load(file_name: str) -> TargetAllocation:
    """Load a target allocation from a JSON file.

    This function reads a target allocation file from the targets directory,
    validates its structure strictly, and reconstructs a ``TargetAllocation``
    domain object. The file is assumed to be produced by the corresponding
    save logic; any structural deviation is treated as an invariant violation.

    Args:
        file_name: Name of the target allocation file to load.

    Returns:
        A ``TargetAllocation`` instance reconstructed from the file.

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
        target_dto = json.load(f)

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

    target = TargetAllocation()
    for asset_dto in assets:
        asset_id, asset_name, asset_purpose, target_ratio, tolerance = _parse_asset_dto(
            asset_dto
        )
        asset = Asset(asset_id, asset_name, asset_purpose)
        target.add_asset(asset, target_ratio, tolerance)

    return target


def _parse_asset_dto(asset_dto: AssetDTO) -> tuple[str, str, str, float, Tolerance]:
    """Parse and validate a single asset DTO from a target file.

    This function validates the structure and types of an asset DTO loaded
    from JSON and extracts the fields required to construct an ``Asset`` and
    register it in a ``TargetAllocation``. All checks are strict and treated
    as invariants, as the DTO is expected to originate from trusted save logic.

    Args:
        asset_dto: A dictionary representing a serialized asset target.

    Returns:
        A tuple containing:
            - asset_id: Asset identifier.
            - asset_name: Human-readable asset name.
            - asset_purpose: Asset purpose/category.
            - target_ratio: Target allocation ratio as a float.
            - tolerance: Tolerance configuration for the asset.

    Raises:
        TypeError: If the DTO or any of its fields has an unexpected type.
        RuntimeError: If required keys are missing, indicating a bug in the
            save logic.
    """
    if not isinstance(asset_dto, dict):
        raise TypeError(
            f"Invariant violated: asset dto must be a dict, got {type(asset_dto).__name__}."
        )

    for key in ("id", "name", "purpose", "target_ratio", "tolerance"):
        if key not in asset_dto:
            raise RuntimeError(
                f"Invariant violated: asset dto missing key '{key}'. "
                "This indicates a bug in save logic."
            )

    asset_id = asset_dto["id"]
    asset_name = asset_dto["name"]
    asset_purpose = asset_dto["purpose"]
    target_ratio = asset_dto["target_ratio"]
    tolerance = asset_dto["tolerance"]

    if not isinstance(asset_id, str) or not asset_id:
        raise TypeError("Invariant violated: 'id' must be a non-empty string.")
    if not isinstance(asset_name, str) or not asset_name:
        raise TypeError("Invariant violated: 'name' must be a non-empty string.")
    if not isinstance(asset_purpose, str) or not asset_purpose:
        raise TypeError("Invariant violated: 'purpose' must be a non-empty string.")
    if not isinstance(target_ratio, (int, float)) or isinstance(target_ratio, bool):
        raise TypeError("Invariant violated: 'target_ratio' must be a number.")
    if not isinstance(tolerance, dict):
        raise TypeError("Invariant violated: 'tolerance' must be a dict.")

    return (asset_id, asset_name, asset_purpose, float(target_ratio), tolerance)
