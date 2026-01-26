from portfotrack.domain.asset.factory import create_asset
from portfotrack.domain.target_allocation import TargetAllocation


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
