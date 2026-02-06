from portfotrack.cli.parsing.flags import parse_flags, pop_required_float
from portfotrack.cli.registry import CommandRegistry, CommandSpec
from portfotrack.cli.state import ReplState
from portfotrack.common.errors import AppError
from portfotrack.services.target_services import (
    add_asset_to_target,
    init_target,
    load_latest_target,
    save_target,
)


def run_init_target(state: ReplState, args: list[str]) -> None:
    """Initialize and set the active target allocation in REPL state."""
    state.target = init_target()
    print("Target initialized.")


def run_add_asset(state: ReplState, args: list[str]) -> None:
    """Add Asset to Target."""
    if state.target is None:
        print("No target. Run `init-target` first.")
        return

    if len(args) < 3:
        print(
            "Usage: add-asset <id> <name> <purpose> --ratio <r> --lower <l> --upper <u>"
        )
        return

    results = parse_flags(args, allowed={"ratio", "lower", "upper"})

    if len(results.rest) != 3:
        print(
            "Usage: add-asset <id> <name> <purpose> --ratio <r> --lower <l> --upper <u>"
        )
        return

    asset_id, asset_name, purpose = results.rest

    ratio = pop_required_float(results.flags, "ratio")
    lower = pop_required_float(results.flags, "lower")
    upper = pop_required_float(results.flags, "upper")

    add_asset_to_target(
        state.target, asset_id, asset_name, purpose, ratio, lower, upper
    )
    print("Asset added.")


def run_save_target(state: ReplState, args: list[str]) -> None:
    """Save Target Allocation."""
    target = state.target

    if target is None:
        print("No target. Run `init-target` first.")
        return

    try:
        target.validate_total()
    except AppError as e:
        print(e)
        return

    save_target(target)
    print("Target allocation saved successfully.")


def run_load_target(state: ReplState, args: list[str]) -> None:
    """Load latest Target Allocation."""
    target = load_latest_target()
    print("Target allocation loaded successfully.")
    state.target = target


def register_target_commands(registry: CommandRegistry) -> None:
    """Register target-related CLI commands.

    This function registers all commands related to target allocation
    management (e.g. initialization and asset addition) into the given
    CommandRegistry.

    It performs command registration only and does not execute any
    command logic. This function is intended to be called during
    application startup when building the global command registry.

    Args:
        registry: CommandRegistry instance to register commands into.
    """
    registry.register(
        CommandSpec(
            name="init-target",
            handler=run_init_target,
            help="Initialize target allocation",
        )
    )
    registry.register(
        CommandSpec(
            name="add-asset",
            handler=run_add_asset,
            help="Add asset to the active target",
        )
    )
    registry.register(
        CommandSpec(
            name="save-target",
            handler=run_save_target,
            help="Save current target allocation",
        )
    )
    registry.register(
        CommandSpec(
            name="load-target",
            handler=run_load_target,
            help="Load latest target allocation",
        )
    )
