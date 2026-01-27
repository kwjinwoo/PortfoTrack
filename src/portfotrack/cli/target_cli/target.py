from collections.abc import Callable

from portfotrack.cli.io import print_banner, print_help
from portfotrack.cli.state import ReplState
from portfotrack.cli.target_cli.errors import InvalidCommandError
from portfotrack.common.errors import AppError
from portfotrack.services.target_services import init_target

PROMPT = "portfotrack> "
CommandHandler = Callable[[ReplState, list[str]], None]


def run_repl() -> int:
    """
    Run the interactive PortfoTrack command loop.
    """

    state = ReplState()
    print_banner()

    while True:
        try:
            raw = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return 0

        if raw in {"quit", "exit"}:
            print("Bye.")
            return 0

        if raw in {"help", "?"}:
            print_help()
            continue

        try:
            handle_command(raw, state)
        except AppError as e:
            print(e)


def _run_init_target(state: ReplState, args: list[str]) -> None:
    """Initialize and set the active target allocation in REPL state."""
    state.target = init_target()
    print("Target initialized.")


def _run_add_asset(state: ReplState, args: list[str]) -> None:
    pass


COMMAND_DICT: dict[str, CommandHandler] = {
    "init-target": _run_init_target,
    "add-asset": _run_add_asset,
}


def handle_command(raw: str, state: ReplState) -> None:
    tokens = raw.split()
    cmd, args = tokens[0], tokens[1:]

    if cmd not in COMMAND_DICT:
        raise InvalidCommandError(command=cmd)

    COMMAND_DICT[cmd](state, args)
