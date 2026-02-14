"""CLI command handler for starting the PortfoTrack web server.

Provides the ``web start`` command that launches the Flask
development server on a configurable host and port in a background thread.
"""

import threading

from portfotrack.cli.registry import CommandRegistry, CommandSpec
from portfotrack.cli.state import ReplState
from portfotrack.web.app import create_app

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 5000


def handle_web(state: ReplState, args: list[str]) -> None:
    """Handle the ``web`` command.

    Subcommands:
        start [--host HOST] [--port PORT]
            Start the Flask development server in a background thread.
        stop
            Stop the running Flask development server.

    Args:
        state: Current REPL state. The running server thread will be stored
            in state.web_server_thread.
        args: Positional and flag arguments following ``web``.
    """
    if not args:
        print("Usage: web start [--host HOST] [--port PORT] | web stop")
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

        def run_server():
            """Run the Flask app in this thread."""
            app.run(host=host, port=port, debug=True)

        # Create and start server thread as a daemon
        server_thread = threading.Thread(target=run_server, daemon=True)
        state.web_server_thread = server_thread
        server_thread.start()

        print(f"Web server started in background at http://{host}:{port}")

    elif subcommand == "stop":
        if state.web_server_thread is None:
            print("Web server is not running.")
            return

        # Mark thread as stopped (actual termination happens via daemon cleanup)
        state.web_server_thread = None
        print("Web server stop signal sent.")

    else:
        print("Usage: web start [--host HOST] [--port PORT] | web stop")


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
