"""CLI command handler for starting the PortfoTrack web server.

Provides the ``web start`` command that launches the Flask
development server on a configurable host and port.  The server
runs in the foreground — Ctrl+C terminates both the server and
the REPL process.
"""

from portfotrack.cli.registry import CommandRegistry, CommandSpec
from portfotrack.cli.state import ReplState
from portfotrack.web.app import create_app

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 5000


def handle_web(state: ReplState, args: list[str]) -> None:
    """Handle the ``web`` command.

    Subcommands:
        start [--host HOST] [--port PORT]
            Start the Flask development server in the foreground.
            Press Ctrl+C to stop.

    Args:
        state: Current REPL state (unused, required by handler signature).
        args: Positional and flag arguments following ``web``.
    """
    if not args:
        print("Usage: web start [--host HOST] [--port PORT]")
        return

    subcommand = args[0]

    if subcommand == "start":
        host = _DEFAULT_HOST
        port = _DEFAULT_PORT

        i = 1
        while i < len(args):
            if args[i] == "--host" and i + 1 < len(args):
                host = args[i + 1]
                i += 2
            elif args[i] == "--port" and i + 1 < len(args):
                port = int(args[i + 1])
                i += 2
            else:
                i += 1

        app = create_app()
        print(f"Starting web server at http://{host}:{port}  (Ctrl+C to stop)")
        app.run(host=host, port=port, debug=False)

    else:
        print("Usage: web start [--host HOST] [--port PORT]")


def register_web_commands(registry: CommandRegistry) -> None:
    """Register web-related CLI commands.

    Args:
        registry: The command registry to add web commands to.
    """
    registry.register(
        CommandSpec(
            name="web",
            handler=handle_web,
            help="Start the web server. Usage: web start [--host HOST] [--port PORT]",
        )
    )
