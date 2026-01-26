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
        "  exit | quit\n"
        "  init-target\n"
        "  add-asset\n"
    )
