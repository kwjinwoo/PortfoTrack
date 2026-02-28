from portfotrack.domain.asset.factory import create_asset
from portfotrack.domain.target_allocation import TargetAllocation
from portfotrack.path import TARGETS_DIR
from portfotrack.storage.json_store.target_store import load, save, save_to_file
from portfotrack.storage.serialization.target_json import dto_to_target, target_to_dto


def init_target() -> TargetAllocation:
    """
    Initialize a new, empty TargetAllocation.

    This function acts as the service-layer entry point for creating
    a TargetAllocation instance. It intentionally wraps the direct
    constructor call to provide a stable creation boundary between
    the CLI/application layer and the domain layer.

    In the future, this function may be extended to:
    - Attach metadata (e.g. name, schema version, created_at)
    - Apply default configuration or policies
    - Perform version-aware initialization for backward compatibility

    Returns:
        An empty TargetAllocation instance.
    """
    return TargetAllocation()


def add_asset_to_target(
    target: TargetAllocation,
    asset_id: str,
    asset_name: str,
    purpose: str,
    target_ratio: float,
    lower: float,
    upper: float,
) -> TargetAllocation:
    """
    Add an asset allocation entry to an existing TargetAllocation.

    This function orchestrates the workflow of:
    - Creating an Asset via the asset factory
    - Constructing a tolerance definition
    - Delegating validation and registration to the domain model

    All business rule validation (e.g. ratio bounds, duplicate assets,
    tolerance constraints) is expected to be enforced by
    TargetAllocation.add_asset(). This service function intentionally
    remains thin and free of duplicated domain logic.

    Args:
        target: The TargetAllocation to be updated.
        asset_id: Stable identifier of the asset.
        asset_name: Human-readable name of the asset.
        purpose: High-level investment purpose of the asset.
        target_ratio: Desired allocation ratio (0.0 ~ 1.0).
        lower: Lower bound of the allowed tolerance.
        upper: Upper bound of the allowed tolerance.

    Returns:
        The updated TargetAllocation instance.
    """
    asset = create_asset(asset_id, asset_name, purpose)
    target.add_asset(asset, target_ratio, {"lower": lower, "upper": upper})
    return target


def save_target(target: TargetAllocation) -> None:
    """Save the given target allocation to persistent JSON storage.

    This is a service-layer convenience wrapper that converts the domain
    `TargetAllocation` into a JSON-serializable DTO and delegates the actual
    persistence to the JSON store.

    Args:
        target: Target allocation domain object to persist.

    Returns:
        None
    """
    target_dto = target_to_dto(target)
    save(target_dto)


def save_target_overwrite(target: TargetAllocation, file_name: str) -> None:
    """Save the given target allocation to a specific file, overwriting it.

    This is the service-layer wrapper for overwrite saves. It converts the
    domain `TargetAllocation` into a DTO and delegates to the store's
    `save_to_file`, preserving the original filename.

    Args:
        target: Target allocation domain object to persist.
        file_name: The target file name to overwrite.
    """
    target_dto = target_to_dto(target)
    save_to_file(target_dto, file_name)


def load_latest_target() -> TargetAllocation:
    """Load the most recent target allocation from JSON storage.

    This function scans the targets directory for JSON files and loads the
    newest one (by filename sort order). It then converts the loaded DTO into
    a domain `TargetAllocation`.

    Returns:
        The most recently saved target allocation.

    Raises:
        FileNotFoundError: If no target JSON files exist in the targets directory.
    """
    targets = sorted(TARGETS_DIR.glob("*.json"))

    if not targets:
        raise FileNotFoundError(f"No target files found under: {TARGETS_DIR}")

    latest_target_path = targets[-1]
    latest_target_dto = load(latest_target_path.name)
    return dto_to_target(latest_target_dto)


def get_available_assets_from_target(
    target: TargetAllocation,
) -> list[dict[str, str]]:
    """Returns asset information from a target allocation.

    Each asset is represented as a dict with id, name, and purpose fields.
    This provides the data needed for UI components like dropdowns.

    Args:
        target: The target allocation to extract assets from.

    Returns:
        List of dicts, each containing 'id', 'name', and 'purpose' keys.
        Empty list if no assets are defined.
    """
    return [
        {"id": asset.id, "name": asset.name, "purpose": asset.purpose}
        for asset in target.target_assets
    ]


def validate_asset_id_in_target(target: TargetAllocation, asset_id: str) -> bool:
    """Check whether an asset_id exists in the given target allocation.

    Thin service wrapper around TargetAllocation.is_valid_asset_id.

    Args:
        target: The target allocation to check against.
        asset_id: The asset identifier to validate.

    Returns:
        True if the asset_id exists in the target, False otherwise.
    """
    return target.is_valid_asset_id(asset_id)
