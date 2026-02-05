from typing import TypedDict

from portfotrack.domain.asset import Asset
from portfotrack.domain.target_allocation import TargetAllocation, Tolerance


class ToleranceDTO(TypedDict):
    lower: float
    upper: float


class AssetDTO(TypedDict):
    id: str
    name: str
    purpose: str
    target_ratio: float
    tolerance: ToleranceDTO


class TargetAllocationDTO(TypedDict):
    assets: list[AssetDTO]


def target_to_dto(target: TargetAllocation) -> TargetAllocationDTO:
    """Convert a TargetAllocation domain object into a JSON-serializable DTO.

    This function transforms the domain representation (which may use Asset
    instances as dictionary keys) into a stable, JSON-friendly structure.
    Assets are sorted by asset id to produce deterministic output, which is
    useful for diffs and reproducible file persistence.

    Args:
        target: The TargetAllocation domain object to convert.

    Returns:
        A TargetAllocationDTO dictionary containing a list of assets with
        their id, name, purpose, target_ratio, and tolerance bounds.
    """
    assets: list[AssetDTO] = []

    items = sorted(
        target.target_assets.items(),
        key=lambda kv: kv[0].id,
    )

    for asset, (target_ratio, tolerance) in items:
        asset_dto: AssetDTO = {
            "id": asset.id,
            "name": asset.name,
            "purpose": asset.purpose,
            "target_ratio": target_ratio,
            "tolerance": {"lower": tolerance["lower"], "upper": tolerance["upper"]},
        }
        assets.append(asset_dto)

    return {"assets": assets}


def dto_to_target(dto: TargetAllocationDTO) -> TargetAllocation:
    """Convert a TargetAllocationDTO into a TargetAllocation domain object.

    This function reconstructs domain objects from a DTO, typically loaded
    from a JSON file. It assumes the DTO matches the expected schema.

    Args:
        dto: The TargetAllocationDTO to convert.

    Returns:
        A TargetAllocation domain object reconstructed from the DTO.
    """
    target_allocation = TargetAllocation()

    for asset_dto in dto["assets"]:
        asset_id, asset_name, asset_purpose, target_ratio, tolerance = _parse_asset_dto(
            asset_dto
        )
        asset = Asset(id=asset_id, name=asset_name, purpose=asset_purpose)
        target_allocation.add_asset(asset, target_ratio, tolerance)

    return target_allocation


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
