from typing import Any

from portfotrack.domain.errors import DomainError
from portfotrack.domain.optional_bet.error_codes import OptionalBetErrorCode


class OptionalBetError(DomainError):
    """Base error for optional bet domain."""


class InvalidCapRatioError(OptionalBetError):
    """Raised when a cap ratio is outside the valid range (0.0, 1.0) exclusive.

    Attributes:
        details: Contains:
            - cap_ratio: The invalid cap ratio value provided.
    """

    def __init__(
        self,
        *,
        cap_ratio: float,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=OptionalBetErrorCode.OPTIONAL_BET_INVALID_CAP_RATIO,
            message=(
                f"cap_ratio must be between 0.0 and 1.0 (exclusive), "
                f"but got {cap_ratio}."
            ),
            details=details,
            cause=cause,
        )
        self.details.update({"cap_ratio": cap_ratio})


class DuplicateOptionalBetError(OptionalBetError):
    """Raised when adding an optional bet item with a duplicate asset_id.

    Attributes:
        details: Contains:
            - asset_id: The identifier of the duplicated asset.
    """

    def __init__(
        self,
        *,
        asset_id: str,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=OptionalBetErrorCode.OPTIONAL_BET_DUPLICATE_ASSET,
            message=(f"Optional bet item with asset_id '{asset_id}' already exists."),
            details=details,
            cause=cause,
        )
        self.details.update({"asset_id": asset_id})


class OptionalBetAssetNotFoundError(OptionalBetError):
    """Raised when an optional bet item is not found by asset_id.

    Attributes:
        details: Contains:
            - asset_id: The identifier of the asset that was not found.
    """

    def __init__(
        self,
        *,
        asset_id: str,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=OptionalBetErrorCode.OPTIONAL_BET_ASSET_NOT_FOUND,
            message=(f"Optional bet item with asset_id '{asset_id}' not found."),
            details=details,
            cause=cause,
        )
        self.details.update({"asset_id": asset_id})
