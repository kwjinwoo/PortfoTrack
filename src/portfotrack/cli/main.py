"""
Interactive CLI entry point for PortfoTrack.

This module serves as the top-level entry point for the PortfoTrack application.
When executed, it launches an interactive, REPL-style command-line interface
that guides the user through managing target portfolio allocations.

Design notes:
- All business logic is delegated to service-layer functions.
- This module is intentionally minimal and only wires program startup
  to the interactive CLI loop.
"""

from portfotrack.cli.target_cli.target import run_repl


def main() -> int:
    """
    Start the interactive PortfoTrack CLI.

    Returns:
        int: Process exit code. Returns 0 on normal termination.
    """
    return run_repl()


if __name__ == "__main__":
    SystemExit(main())
