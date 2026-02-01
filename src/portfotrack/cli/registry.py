from collections.abc import Callable
from dataclasses import dataclass

from portfotrack.cli.errors import InvalidCommandError
from portfotrack.cli.state import ReplState

CommandHandler = Callable[[ReplState, list[str]], None]


@dataclass(frozen=True)
class CommandSpec:
    """Specification for a single CLI command.

    This dataclass describes a command that can be registered in the
    CommandRegistry. It binds a command name to its handler function
    and optional help text.

    Attributes:
        name: Command name as typed by the user (e.g. "add-asset").
        handler: Callable that executes the command logic.
            The handler receives the current REPL state and
            a list of positional arguments.
        help: Optional human-readable description of the command.
            Intended for use by help or documentation commands.
    """

    name: str
    handler: CommandHandler
    help: str = ""


class CommandRegistry:
    def __init__(self) -> None:
        """Initialize an empty command registry."""
        self._commands: dict[str, CommandSpec] = {}

    def register(self, spec: CommandSpec) -> None:
        """Register a new command specification.

        Args:
            spec: CommandSpec describing the command to register.

        Raises:
            ValueError: If a command with the same name is already registered.

        Note:
            Command names must be unique within a registry. Attempting to
            register a duplicate command name is treated as a programmer
            error and results in an exception.
        """
        if spec.name in self._commands:
            raise ValueError(f"Duplicated command name {spec.name}.")
        self._commands[spec.name] = spec

    def dispatch(self, *, raw: str, state: ReplState) -> None:
        """Dispatch a raw command line to the corresponding handler.

        The raw input string is split on whitespace. The first token is
        interpreted as the command name, and the remaining tokens are
        passed as positional arguments to the command handler.

        Args:
            raw: Raw input line entered by the user.
            state: Current REPL state, shared across commands.

        Raises:
            InvalidCommandError: If the command name is not registered.
        """
        tokens = raw.split()
        if not tokens:
            return

        cmd, args = tokens[0], tokens[1:]
        spec = self._commands.get(cmd)
        if spec is None:
            raise InvalidCommandError(command=cmd)

        spec.handler(state, args)

    def list_commands(self) -> list[CommandSpec]:
        """Return all registered commands.

        Returns:
            A list of CommandSpec objects sorted by command name.
        """
        return sorted(self._commands.values(), key=lambda s: s.name)
