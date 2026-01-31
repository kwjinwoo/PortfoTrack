from typing import Any

from portfotrack.cli.error_codes import CliErrorCode
from portfotrack.common.errors import AppError


class CliError(AppError):
    """Base class for cli-layer errors."""

    pass


# --- Command Errors ---
class InvalidCommandError(CliError):
    """
    Error raised when an unknown or unsupported command is entered
    in the interactive CLI.
    """

    def __init__(
        self,
        *,
        command: str,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=CliErrorCode.CLI_INVALID_COMMAND,
            message=f"Invalid command: '{command}'. Type 'help' to see available commands.",
            details=details,
            cause=cause,
        )
        self.details.update({"command": command})


# --- Parsing Errors ---
class InvalidFlagError(CliError):
    """Raised when a flag is syntactically invalid or not recognized.

    This error is used for malformed flags (e.g. '--' without a name),
    unsupported flags, or flags that do not conform to the expected
    command-line syntax.

    Attributes:
        flag: The raw flag token that caused the error.
        reason: Optional human-readable explanation describing why the
            flag is considered invalid.
    """

    def __init__(
        self,
        *,
        flag: str,
        reason: str | None = None,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        message = f"Invalid flag {flag}."
        if reason is not None:
            message += f" {reason}"
        super().__init__(
            code=CliErrorCode.CLI_INVALID_FLAG,
            message=message,
            details=details,
            cause=cause,
        )
        self.details.update({"flag": flag})


class DuplicatedFlagError(CliError):
    """Raised when the same flag is specified more than once.

    This error indicates that a flag was provided multiple times in a
    single command invocation where duplication is not allowed.

    Attributes:
        flag: The duplicated flag name (without leading dashes).
    """

    def __init__(
        self,
        *,
        flag: str,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=CliErrorCode.CLI_DUPLICATED_FLAG,
            message=f"Duplicate flag '--{flag}'.",
            details=details,
            cause=cause,
        )
        self.details.update({"flag": flag})


class MissingFlagValueError(CliError):
    """Raised when a flag that requires a value is missing one.

    This error is used when a flag is provided without an accompanying
    value, or when the next token is not a valid value (e.g. another flag).

    Attributes:
        flag: The flag name that requires a value.
        value: The token that was encountered instead of a valid value,
            if available.
    """

    def __init__(
        self,
        *,
        flag: str,
        value: str | None = None,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        message = f"Flag '--{flag}' requires a value."
        if value is not None:
            message += f" but got '{value}'."

        super().__init__(
            code=CliErrorCode.CLI_MISSING_FLAG_VALUE,
            message=message,
            details=details,
            cause=cause,
        )
        self.details.update({"flag": flag})
        if value is not None:
            self.details.update({"value": value})


class MissingRequiredFlagError(CliError):
    def __init__(
        self,
        *,
        flag: str,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            code=CliErrorCode.CLI_MISSING_REQUIRED_FLAG,
            message=f"Missing required flag '--{flag}'.",
            details=details,
            cause=cause,
        )
        self.details.update({"flag": flag})


class InvalidValueTypeError(CliError):
    def __init__(
        self,
        *,
        flag: str,
        required_type: str,
        wrong_value: str | None = None,
        details: dict[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        message = f"Flag '--{flag}' must be {required_type}."
        if wrong_value is not None:
            message += f" but got '{wrong_value}'."
        super().__init__(
            code=CliErrorCode.CLI_INVALID_VALUE_TYPE,
            message=message,
            details=details,
            cause=cause,
        )
        self.details.update(
            {"flag": flag, "required_type": required_type, "wrong_value": wrong_value}
        )
