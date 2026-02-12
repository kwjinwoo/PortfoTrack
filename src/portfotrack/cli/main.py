from portfotrack.cli.io import print_banner, print_help
from portfotrack.cli.registry import CommandRegistry
from portfotrack.cli.state import ReplState
from portfotrack.common.errors import AppError

PROMPT = "portfotrack> "


def build_registry() -> CommandRegistry:
    """Build and initialize the global CLI command registry.

    This function creates a CommandRegistry instance and registers
    all available CLI commands by invoking feature-specific
    registration functions.

    It serves as a single, explicit entry point for command
    registration and is intended to be called once during
    application startup.

    Returns:
        A fully initialized CommandRegistry containing all
        registered CLI commands.
    """
    registry = CommandRegistry()

    from portfotrack.cli.snapshot_cli.snapshot import register_snapshot_commands
    from portfotrack.cli.target_cli.target import register_target_commands

    register_target_commands(registry)
    register_snapshot_commands(registry)

    return registry


def run_repl() -> int:
    """Run the interactive PortfoTrack command loop."""
    state = ReplState()
    registry = build_registry()

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
            registry.dispatch(raw=raw, state=state)
        except AppError as e:
            print(e)
