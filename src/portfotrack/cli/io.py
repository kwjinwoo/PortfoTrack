def print_banner() -> None:
    """
    Print the startup banner for the interactive CLI.

    This function displays a short welcome message when the
    interactive session starts, providing basic guidance on
    how to access available commands.
    """
    print("PortfoTrack interactive CLI")
    print("Type 'help' to see commands.\n")


def print_help() -> None:
    """
    Print the list of available interactive commands.

    This function displays a short help message describing
    the commands supported by the interactive CLI and how
    to exit the session.
    """
    print(
        "\nCommands:\n"
        "  help | ?\n"
        "      Show this help message.\n\n"
        "  exit | quit\n"
        "      Exit the REPL.\n\n"
        "  init-target\n"
        "      Initialize a new target allocation.\n\n"
        "  add-asset <id> <name> <purpose> --ratio <r> --lower <l> --upper <u>\n"
        "      Add an asset to the current target allocation.\n"
        "      Example:\n"
        '        add-asset us-stock "US Equity" core --ratio 0.4 --lower 0.35 --upper 0.45\n\n'
        "  save-target\n"
        "      Save the current target allocation to disk.\n\n"
        "  load-target\n"
        "      Load the most recently saved target allocation.\n"
        "  init-snapshot\n"
        "      Initialize a new empty snapshot for recording holdings.\n"
        "\n"
        "  add-snapshot <id> <label> --amount <n>\n"
        "      Add an item to the active snapshot. Example:\n"
        '        add-snapshot cash "KRW Deposit" --amount 1000000\n'
    )
