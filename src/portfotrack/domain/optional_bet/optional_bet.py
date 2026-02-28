import datetime
from dataclasses import dataclass, field

from portfotrack.domain.optional_bet.errors import (
    DuplicateOptionalBetError,
    InvalidCapRatioError,
    OptionalBetAssetNotFoundError,
)


@dataclass(frozen=True)
class OptionalBetItem:
    """A single optional bet holding outside the main portfolio.

    Represents an aggressive investment position that is tracked separately
    from the main portfolio allocation. Each item has an individual cap ratio
    defining the maximum allowed proportion relative to total assets
    (main portfolio + all optional bets).

    Attributes:
        asset_id: Unique identifier for this optional bet asset.
        name: Human-readable display name.
        cap_ratio: Maximum allowed ratio relative to total assets.
            Must be in the open interval (0.0, 1.0).
        amount: Current holding amount in the snapshot currency (KRW).
            Must be non-negative.
    """

    asset_id: str
    name: str
    cap_ratio: float
    amount: int


@dataclass(frozen=True)
class CapBreachResult:
    """Result of a cap breach check for a single optional bet item.

    Attributes:
        asset_id: Identifier of the breaching asset.
        name: Display name of the breaching asset.
        actual_ratio: Current ratio of this asset relative to total assets.
        cap_ratio: Maximum allowed ratio for this asset.
    """

    asset_id: str
    name: str
    actual_ratio: float
    cap_ratio: float


def _validate_cap_ratio(cap_ratio: float) -> None:
    """Validates that cap_ratio is in the open interval (0.0, 1.0).

    Args:
        cap_ratio: The cap ratio value to validate.

    Raises:
        InvalidCapRatioError: If cap_ratio is not in (0.0, 1.0).
    """
    if not (0.0 < cap_ratio < 1.0):
        raise InvalidCapRatioError(cap_ratio=cap_ratio)


def _validate_amount(amount: int) -> None:
    """Validates that amount is non-negative.

    Args:
        amount: The amount value to validate.

    Raises:
        ValueError: If amount is negative (programmer error).
    """
    if amount < 0:
        raise ValueError(f"amount must be non-negative, but got {amount}.")


def check_cap_breaches(
    items: list[OptionalBetItem], *, main_portfolio_total: int
) -> list[CapBreachResult]:
    """Checks which optional bet items exceed their individual cap ratios.

    The actual ratio for each item is calculated as:
        item.amount / (main_portfolio_total + sum of all item amounts)

    An item is considered in breach if its actual ratio strictly exceeds
    its cap_ratio.

    Args:
        items: List of optional bet items to check.
        main_portfolio_total: Total amount of the main portfolio in KRW.

    Returns:
        List of CapBreachResult for items that exceed their cap ratio.
        Empty list if no breaches or if total assets is zero.
    """
    bet_total = sum(item.amount for item in items)
    grand_total = main_portfolio_total + bet_total

    if grand_total == 0:
        return []

    breaches: list[CapBreachResult] = []
    for item in items:
        actual_ratio = item.amount / grand_total
        if actual_ratio > item.cap_ratio:
            breaches.append(
                CapBreachResult(
                    asset_id=item.asset_id,
                    name=item.name,
                    actual_ratio=actual_ratio,
                    cap_ratio=item.cap_ratio,
                )
            )

    return breaches


@dataclass
class OptionalBetSnapshot:
    """A snapshot of all optional bet holdings at a given date.

    Optional bets are aggressive investment positions that are tracked
    separately from the main portfolio. Each item has an individual cap
    ratio limiting its proportion relative to total assets.

    Attributes:
        date: Snapshot date in ISO format (YYYY-MM-DD).
        currency: Currency of all amounts. Defaults to KRW.
        items: List of optional bet items in this snapshot.
    """

    date: str = field(default_factory=lambda: datetime.date.today().isoformat())
    currency: str = "KRW"
    items: list[OptionalBetItem] = field(default_factory=list)

    def add_item(self, asset_id: str, name: str, cap_ratio: float, amount: int) -> None:
        """Adds a new optional bet item to the snapshot.

        Args:
            asset_id: Unique identifier for the asset.
            name: Human-readable display name.
            cap_ratio: Maximum allowed ratio in (0.0, 1.0).
            amount: Holding amount in KRW. Must be non-negative.

        Raises:
            DuplicateOptionalBetError: If asset_id already exists.
            InvalidCapRatioError: If cap_ratio is not in (0.0, 1.0).
            ValueError: If amount is negative.
        """
        _validate_cap_ratio(cap_ratio)
        _validate_amount(amount)

        if any(item.asset_id == asset_id for item in self.items):
            raise DuplicateOptionalBetError(asset_id=asset_id)

        self.items.append(
            OptionalBetItem(
                asset_id=asset_id,
                name=name,
                cap_ratio=cap_ratio,
                amount=amount,
            )
        )

    def remove_item(self, asset_id: str) -> None:
        """Removes an optional bet item by its asset_id.

        Args:
            asset_id: The identifier of the item to remove.

        Raises:
            OptionalBetAssetNotFoundError: If no item with the given
                asset_id exists.
        """
        index = self._find_index(asset_id)
        del self.items[index]

    def update_item(
        self,
        asset_id: str,
        *,
        name: str | None = None,
        cap_ratio: float | None = None,
        amount: int | None = None,
    ) -> None:
        """Updates fields of an existing optional bet item.

        Only the provided keyword arguments are updated; others retain
        their current values. Validation is performed before any mutation.

        Args:
            asset_id: The identifier of the item to update.
            name: New display name, or None to keep current.
            cap_ratio: New cap ratio in (0.0, 1.0), or None to keep current.
            amount: New amount (non-negative), or None to keep current.

        Raises:
            OptionalBetAssetNotFoundError: If no item with the given
                asset_id exists.
            InvalidCapRatioError: If cap_ratio is not in (0.0, 1.0).
            ValueError: If amount is negative.
        """
        index = self._find_index(asset_id)
        current = self.items[index]

        new_name = name if name is not None else current.name
        new_cap_ratio = cap_ratio if cap_ratio is not None else current.cap_ratio
        new_amount = amount if amount is not None else current.amount

        # Validate before mutation
        _validate_cap_ratio(new_cap_ratio)
        _validate_amount(new_amount)

        self.items[index] = OptionalBetItem(
            asset_id=asset_id,
            name=new_name,
            cap_ratio=new_cap_ratio,
            amount=new_amount,
        )

    def total_amount(self) -> int:
        """Calculates the sum of all optional bet item amounts.

        Returns:
            Total amount across all items. Returns 0 if empty.
        """
        return sum(item.amount for item in self.items)

    def _find_index(self, asset_id: str) -> int:
        """Finds the index of an item by its asset_id.

        Args:
            asset_id: The identifier to search for.

        Returns:
            Index of the matching item.

        Raises:
            OptionalBetAssetNotFoundError: If no item with the given
                asset_id exists.
        """
        for i, item in enumerate(self.items):
            if item.asset_id == asset_id:
                return i
        raise OptionalBetAssetNotFoundError(asset_id=asset_id)
