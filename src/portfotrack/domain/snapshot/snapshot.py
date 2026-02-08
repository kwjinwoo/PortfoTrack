from dataclasses import dataclass


@dataclass(frozen=True)
class SnapshotItem:
    """A single line item representing a concrete holding within an asset class.

    A SnapshotItem captures the smallest unit of observation in a snapshot.
    Multiple items may share the same asset_id, allowing detailed breakdowns
    (e.g., S&P500 and Nasdaq100 under the same US equity ETF asset class).

    This class intentionally stores absolute amounts only. Allocation ratios
    are derived later during aggregation and comparison against a target
    allocation.

    Attributes:
        asset_id: Identifier of the asset class this item belongs to.
            Must correspond to an asset_id defined in the target allocation.
        label: Human-readable label for this specific holding
            (e.g., "S&P500", "Nasdaq100", "KRW Cash").
        amount: Absolute amount of this holding in the snapshot currency
            (typically KRW). Must be non-negative.
    """

    asset_id: str
    label: str
    amount: int


@dataclass(frozen=True)
class Snapshot:
    """An immutable snapshot of the portfolio state at a specific point in time.

    A Snapshot represents an observational record of the portfolio, capturing
    what assets are held and in what absolute amounts on a given date.
    It serves as the factual input for progress tracking, drift detection,
    and rebalancing analysis.

    This class is intentionally immutable. Once created and persisted, a
    snapshot must not change, ensuring historical accuracy and reproducibility.
    Asset-level aggregation (by asset_id) and ratio calculations are performed
    in service-layer logic and are not stored in this object.

    Attributes:
        date: Snapshot date in ISO format (YYYY-MM-DD), interpreted in the
            local timezone context (e.g., Asia/Seoul).
        currency: Base currency of the snapshot amounts. Defaults to "KRW".
        items: Collection of snapshot line items representing individual
            holdings. Multiple items may share the same asset_id.
    """

    date: str
    currency: str = "KRW"
    items: tuple[SnapshotItem, ...] = ()
