from dataclasses import dataclass, field
from typing import TypedDict

from portfotrack.domain.asset.asset import Asset


class Tolerance(TypedDict):
    """Defines an acceptable allocation range for an asset.

    The tolerance represents absolute allocation bounds, not relative
    deviations. For example, a target of 0.30 with a tolerance of
    {lower: 0.25, upper: 0.35} allows the allocation to drift within
    that range without triggering rebalancing.

    Keys:
        lower: Lower bound of acceptable allocation ratio (inclusive).
        upper: Upper bound of acceptable allocation ratio (inclusive).
    """

    lower: float
    upper: float


@dataclass
class TargetAllocation:
    """Represents the target asset allocation of the portfolio.

    This class defines the desired allocation ratios for each asset,
    along with acceptable tolerance ranges. It is used as an immutable
    snapshot reference for progress tracking and drift detection.

    On initialization, the internal target asset mapping is defensively
    copied to prevent external mutation from affecting this instance.

    Attributes:
        target_assets: Mapping of Asset to a tuple of
            (target_ratio, tolerance). The mapping is copied on
            initialization and is not shared with external callers.
    """

    target_assets: dict[Asset, tuple[float, Tolerance]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Defensively copies the target asset mapping.

        This prevents external mutation of the dictionary passed at
        construction time from affecting the internal state.
        """
        self.target_assets = dict(self.target_assets)

    def add_asset(
        self, asset: Asset, target_ratio: float, tolerance: Tolerance
    ) -> None:
        """Adds a new asset target to the allocation.

        This method registers a target allocation ratio and tolerance
        range for a given asset. It performs basic validation but does
        not enforce that the total allocation sums to 1.0.

        Args:
            asset: Asset to add to the target allocation.
            target_ratio: Desired allocation ratio for the asset,
                expressed as a float between 0.0 and 1.0.
            tolerance: Acceptable allocation bounds for the asset.

        Raises:
            ValueError: If the asset already exists in the allocation.
            ValueError: If target_ratio is outside [0.0, 1.0].
            ValueError: If tolerance.lower is greater than tolerance.upper.
            ValueError: If tolerance bounds are outside [0.0, 1.0].
        """
        if asset in self.target_assets:
            raise ValueError(
                f"Asset {asset.id}-{asset.name} is already in Target Portfolio."
            )

        if not (0.0 <= target_ratio <= 1.0):
            raise ValueError("target_ratio must be between 0 and 1")

        lo, hi = tolerance["lower"], tolerance["upper"]
        if lo > hi:
            raise ValueError("tolerance.lower must be <= tolerance.upper")
        if lo < 0.0 or hi > 1.0:
            raise ValueError("tolerance bounds must be within [0, 1]")

        self.target_assets[asset] = (target_ratio, tolerance)

    def total_ratio(self) -> float:
        """Calculates the sum of all target allocation ratios.

        Returns:
            Sum of target ratios across all assets.
        """
        return sum(r for r, _ in self.target_assets.values())

    def validate_total(self, eps: float = 1e-6) -> None:
        """Validates that total target allocation sums to 1.0.

        This method should be called once the target allocation is
        fully defined. A small epsilon is used to account for floating-
        point precision errors.

        Args:
            eps: Allowed numerical tolerance when comparing against 1.0.

        Raises:
            ValueError: If the total allocation deviates from 1.0 beyond eps.
        """
        total = self.total_ratio()
        if abs(total - 1.0) > eps:
            raise ValueError(f"Total target ratio must be 1.0 (got {total})")
