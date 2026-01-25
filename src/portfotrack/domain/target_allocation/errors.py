from typing import Any

from portfotrack.domain.errors import DomainError
from portfotrack.domain.target_allocation.error_codes import TargetErrorCode


class TargetAllocationError(DomainError):
    """Base error for target allocation domain."""


class DuplicateAssetError(TargetAllocationError):
    """Raised when attempting to add an asset that already exists in the target allocation.

    Attributes:
        details: Contains:
            - asset_id: The identifier of the duplicated asset.
            - asset_name: The display name of the duplicated asset.
    """

    def __init__(
        self,
        *,
        asset_id: str,
        asset_name: str,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=TargetErrorCode.TARGET_DUPLICATE_ASSET,
            message=f"Asset {asset_id}-{asset_name}is already present in the target allocation.",
            details=details,
            cause=cause,
        )
        self.details.update({"asset_id": asset_id, "asset_name": asset_name})


class InvalidTargetRatioError(TargetAllocationError):
    """Raised when a target allocation ratio is outside the valid range.

    A target ratio must be within the inclusive range [0.0, 1.0].

    Attributes:
        details: Contains:
            - target_ratio: The invalid ratio value provided.
    """

    def __init__(
        self,
        *,
        target_ratio: float,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=TargetErrorCode.TARGET_INVALID_RATIO,
            message=f"target_ratio must be between 0 and 1, but got {target_ratio}.",
            details=details,
            cause=cause,
        )
        self.details.update({"target_ratio": target_ratio})


class InvalidToleranceBoundsError(TargetAllocationError):
    """Raised when tolerance bounds are invalid.

    Tolerance bounds must satisfy:
        - lower <= upper
        - lower and upper are within the inclusive range [0.0, 1.0]

    Attributes:
        details: Contains:
            - lower: The provided lower bound.
            - upper: The provided upper bound.
    """

    def __init__(
        self,
        *,
        lower: float,
        upper: float,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=TargetErrorCode.TARGET_INVALID_TOLERANCE_BOUNDS,
            message="tolerance bounds must satisfy lower <= upper and be within [0, 1], "
            f"but got llower={lower}, upper={upper}",
            details=details,
            cause=cause,
        )
        self.details.update({"lower": lower, "upper": upper})


class TotalRatioMismatchError(TargetAllocationError):
    """Raised when the sum of all target ratios does not match the expected total.

    This error typically indicates that the target allocation is incomplete or
    inconsistent (e.g., missing assets or ratios not summing to 1.0). An epsilon
    tolerance is commonly used to account for floating-point rounding.

    Attributes:
        details: Contains:
            - total: The computed sum of target ratios.
            - expected: The expected total (default: 1.0).
            - eps: The numerical tolerance used for the comparison.
    """

    def __init__(
        self,
        *,
        total: float,
        expected: float = 1.0,
        eps: float = 1e-6,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=TargetErrorCode.TARGET_TOTAL_MISMATCH,
            message="Total target ratio must match the expected value within tolerance, "
            f"but total target ratio is {total}",
            details=details,
            cause=cause,
        )
        self.details.update({"total": total, "expected": expected, "eps": eps})
