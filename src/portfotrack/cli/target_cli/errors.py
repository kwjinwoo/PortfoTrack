from typing import Any

from portfotrack.cli.errors import CliError
from portfotrack.cli.target_cli.error_codes import CliErrorCode


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
