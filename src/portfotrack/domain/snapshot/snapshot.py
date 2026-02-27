import datetime
from dataclasses import dataclass, field


@dataclass(frozen=True, eq=False)
class SnapshotItem:
    """A single line item representing a concrete holding within an asset class.

    A SnapshotItem captures the smallest unit of observation in a snapshot.
    Multiple items may share the same asset_id, allowing detailed breakdowns
    (e.g., S&P500 and Nasdaq100 under the same US equity ETF asset class).

    This class intentionally stores absolute amounts only. Allocation ratios
    are derived later during aggregation and comparison against a target
    allocation.

    Equality is determined by asset_id and label only. Two items with the
    same asset_id and label are considered equal regardless of amount,
    supporting the merge-on-add pattern in Snapshot.

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

    def __eq__(self, other: object) -> bool:
        """Compare equality based on asset_id and label only.

        Amount is excluded from comparison so that items representing the
        same holding can be identified for merge-on-add regardless of their
        amount values.

        Args:
            other: Object to compare against.

        Returns:
            True if other is a SnapshotItem with the same asset_id and label.
        """
        if not isinstance(other, SnapshotItem):
            return NotImplemented
        return self.asset_id == other.asset_id and self.label == other.label


@dataclass
class Snapshot:
    """A snapshot of the portfolio state at a specific point in time.

    A Snapshot represents an observational record of the portfolio, capturing
    what assets are held and in what absolute amounts on a given date.
    It serves as the factual input for progress tracking, drift detection,
    and rebalancing analysis.

    Snapshots are built incrementally by adding SnapshotItems. The date is
    automatically set to today when instantiated. Once persisted to storage,
    historical snapshots should not be modified to ensure reproducibility.
    Asset-level aggregation (by asset_id) and ratio calculations are performed
    in service-layer logic and are not stored in this object.

    Attributes:
        date: Snapshot date in ISO format (YYYY-MM-DD), automatically set
            to today in the local timezone context (e.g., Asia/Seoul).
        currency: Base currency of the snapshot amounts. Defaults to "KRW".
        items: Collection of snapshot line items representing individual
            holdings. Multiple items may share the same asset_id.
    """

    date: str = datetime.date.today().isoformat()
    currency: str = "KRW"
    items: list[SnapshotItem] = field(default_factory=list)

    def add_snapshot_item(self, asset_id: str, label: str, amount: int) -> None:
        """Add a new line item to this snapshot, merging if a matching item exists.

        If an item with the same asset_id and label already exists, the amount
        is accumulated into the existing item. Otherwise, a new item is appended.

        Args:
            asset_id: Identifier of the asset class this item belongs to.
            label: Human-readable label for this specific holding.
            amount: Absolute amount in the snapshot currency.
        """
        new_item = SnapshotItem(asset_id, label, amount)
        for idx, existing in enumerate(self.items):
            if existing == new_item:
                self.items[idx] = SnapshotItem(
                    asset_id, label, existing.amount + amount
                )
                return
        self.items.append(new_item)

    def remove_item(self, index: int) -> None:
        """Remove the snapshot item at the given index.

        Only non-negative indices are accepted. Negative indices are
        rejected to prevent ambiguous reverse-indexing in user-facing
        edit operations.

        Args:
            index: Zero-based position of the item to remove.
                Must be a non-negative integer within range.

        Raises:
            IndexError: If index is negative or out of range.
        """
        if index < 0 or index >= len(self.items):
            raise IndexError(
                f"Item index {index} out of range for snapshot "
                f"with {len(self.items)} items."
            )
        self.items.pop(index)

    def replace_item(self, index: int, asset_id: str, label: str, amount: int) -> None:
        """Replace the snapshot item at the given index with new values.

        Creates a new SnapshotItem from the provided fields and places it
        at the specified position. Only non-negative indices are accepted.

        Args:
            index: Zero-based position of the item to replace.
                Must be a non-negative integer within range.
            asset_id: Identifier of the asset class for the replacement item.
            label: Human-readable label for the replacement item.
            amount: Absolute amount in the snapshot currency.

        Raises:
            IndexError: If index is negative or out of range.
        """
        if index < 0 or index >= len(self.items):
            raise IndexError(
                f"Item index {index} out of range for snapshot "
                f"with {len(self.items)} items."
            )
        self.items[index] = SnapshotItem(asset_id, label, amount)
