"""Module entry point for the PortfoTrack CLI package.

Enables:
    python -m portfotrack.cli
"""

from portfotrack.cli.main import run_repl


def main() -> None:
    raise SystemExit(run_repl())


if __name__ == "__main__":
    main()
