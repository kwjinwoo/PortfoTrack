"""Entry point for ``python -m portfotrack``.

Starts the PortfoTrack web server directly.
"""

from portfotrack.web.app import run_server


def main() -> None:
    """Start the web server, propagating SystemExit on failure."""
    run_server()


if __name__ == "__main__":
    main()
