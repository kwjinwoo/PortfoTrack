from portfotrack.cli.io import print_banner, print_help
from portfotrack.cli.target_cli.errors import InvalidCommandError
from portfotrack.common.errors import AppError

PROMPT = "portfotrack> "


def run_repl() -> int:
    """
    Run the interactive PortfoTrack command loop.
    """

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
            handle_command(raw)
        except AppError as e:
            print(e)


def _run_init_target() -> None:
    pass


def _run_add_asset() -> None:
    pass


COMMAND_DICT = {"init-target": _run_init_target, "add-asset": _run_add_asset}


def handle_command(raw: str) -> None:
    tokens = raw.split()
    cmd = tokens[0]

    if cmd not in COMMAND_DICT:
        raise InvalidCommandError(command=cmd)

    COMMAND_DICT[cmd]()
