"""CLI handlers for portfolio allocation report commands."""

from portfotrack.cli.registry import CommandRegistry, CommandSpec
from portfotrack.cli.state import ReplState
from portfotrack.services.allocation_report import (
    format_allocation_report,
    generate_allocation_report,
)


def run_report(state: ReplState, args: list[str]) -> None:
    """Generate and display a portfolio allocation report.

    Compares the active snapshot against the active target allocation
    and prints a human-readable status report.  Both a target and a
    snapshot must be present in the REPL state; otherwise a guidance
    message is printed.

    Args:
        state: Current REPL session state.
        args: Positional arguments (ignored).
    """
    if state.target is None:
        print("No target. Run `init-target` or `load-target` first.")
        return

    if state.snapshot is None:
        print("No snapshot. Run `init-snapshot` or `load-snapshot` first.")
        return

    try:
        report = generate_allocation_report(state.target, state.snapshot)
    except RuntimeError as e:
        print(str(e))
        return

    print(format_allocation_report(report))


def register_report_commands(registry: CommandRegistry) -> None:
    """Register report-related CLI commands.

    Registers the ``report`` command that generates and displays
    an allocation comparison report.

    Args:
        registry: The CLI command registry to register commands into.
    """
    registry.register(
        CommandSpec(
            name="report",
            handler=run_report,
            help="Show allocation report comparing target vs snapshot",
        )
    )
