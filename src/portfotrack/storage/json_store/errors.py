from typing import Any

from portfotrack.storage.errors import StorageError
from portfotrack.storage.json_store.error_codes import StoreJsonErrorcodes


class TargetNotFoundError(StorageError):
    """Raised when a target allocation file cannot be found.

    This error indicates that a requested target file does not exist in the
    storage location. Unlike schema or invariant violations, this error is
    considered user-facing and typically results from an invalid file name
    or an attempt to load a target that has not been created yet.

    Attributes:
        file_name: Name of the target file that could not be found.
    """

    def __init__(
        self,
        *,
        file_name: str,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=StoreJsonErrorcodes.STORE_TARGET_NOT_FOUND,
            message=f"Target file '{file_name}' was not found.",
            details=details,
            cause=cause,
        )
        self.details.update({"file_name": file_name})
