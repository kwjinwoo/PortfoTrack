from portfotrack.cli.io import print_banner, print_help

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
