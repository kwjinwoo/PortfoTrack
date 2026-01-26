from portfotrack.domain.asset import Asset


def create_asset(asset_id: str, asset_name: str, purpose: str) -> Asset:
    """
    Create an Asset instance from raw input values.

    This factory function serves as the single creation entry point for
    Asset objects within the application. Although it currently delegates
    directly to the Asset constructor, it intentionally exists to
    centralize asset creation logic.

    In the future, this function may be extended to handle:
    - Asset ID normalization or alias resolution
    - Lookup from a predefined asset catalog or registry
    - Default name or purpose inference
    - Backward compatibility for persisted asset definitions

    Args:
        asset_id: Stable identifier of the asset (used for equality and persistence).
        asset_name: Human-readable name of the asset.
        purpose: High-level investment purpose (e.g. growth, income, hedge).

    Returns:
        A newly created Asset instance.
    """
    return Asset(asset_id, asset_name, purpose)
