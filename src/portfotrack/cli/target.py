from portfotrack.cli.io import print_banner

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
            print("\nBye.")
            return 0
