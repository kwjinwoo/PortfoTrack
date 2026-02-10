from portfotrack.cli.parsing.flags import parse_flags, pop_required_int
from portfotrack.cli.registry import CommandRegistry, CommandSpec
from portfotrack.cli.state import ReplState
from portfotrack.services.snapshot_services import add_item_to_snapshot, init_snapshot


def run_init_snapshot(state: ReplState, args: list[str]) -> None:
    """Handle the `init-snapshot` command.

    Initializes a new snapshot using the domain/service layer and stores
    it on the provided `ReplState` instance.

    Args:
        state (ReplState): REPL session state to mutate (snapshot will be set).
        args (list[str]): Ignored positional arguments passed from the CLI.

    Returns:
        None
    """

    state.snapshot = init_snapshot()


def run_add_snapshot(state: ReplState, args: list[str]) -> None:
    """Handle the `add-snapshot` command.

    Expected usage: `add-snapshot <asset_id> <label> --amount <int>`.

    The handler checks that a snapshot has been initialized, parses the
    allowed `--amount` flag, validates positional arguments, and delegates
    the actual addition to `add_item_to_snapshot` from the services layer.

    Args:
        state (ReplState): Current REPL state containing the active snapshot.
        args (list[str]): Positional and flag tokens from the CLI.

    Returns:
        None
    """

    if state.snapshot is None:
        print("No snapshot. Run `init-snapshot first.")
        return

    if len(args) < 2:
        print("Usage: add-snapshot <id> <lable> --amount")
        return

    results = parse_flags(args, allowed={"amount"})

    if len(results.rest) < 2:
        print("Usage: add-snapshot <id> <lable> --amount")
        return

    asset_id, label = results.rest
    amount = pop_required_int(results.flags, "amount")
    add_item_to_snapshot(state.snapshot, asset_id, label, amount)


def register_snapshot_commands(registry: CommandRegistry) -> None:
    """Register snapshot-related commands on a `CommandRegistry`.

    Currently registers the `init-snapshot` command. Additional snapshot
    commands should be registered here so the CLI can discover them.

    Args:
        registry (CommandRegistry): The CLI command registry to modify.

    Returns:
        None
    """

    registry.register(
        CommandSpec(
            name="init-snapshot", handler=run_init_snapshot, help="Initialize snapshot"
        )
    )
    registry.register(
        CommandSpec(
            name="add-snapshot",
            handler=run_add_snapshot,
            help="Add snapshot item to the active snapshot",
        )
    )
