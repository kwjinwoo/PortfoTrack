from typing import TypedDict

from portfotrack.domain.asset import Asset
from portfotrack.domain.target_allocation import TargetAllocation


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
        asset = Asset(
            id=asset_dto["id"], name=asset_dto["name"], purpose=asset_dto["purpose"]
        )
        target_ratio = asset_dto["target_ratio"]
        tolerance = asset_dto["tolerance"]
        target_allocation.add_asset(asset, target_ratio, tolerance)

    return target_allocation
