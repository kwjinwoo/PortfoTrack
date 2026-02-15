"""Tests for the web CLI command handler."""

import threading
from unittest.mock import MagicMock, patch

from portfotrack.cli.registry import CommandRegistry
from portfotrack.cli.state import ReplState


class TestWebCommandRegistration:
    """web command should be registered in the CLI registry."""

    def test_web_command_registered(self):
        """The 'web' command should be available in the registry."""
        from portfotrack.cli.web_cli.web import register_web_commands

        registry = CommandRegistry()
        register_web_commands(registry)

        # Verify the command is registered (dispatch should not raise)
        assert "web" in registry._commands


class TestWebCommandHandler:
    """web command handler should start the Flask server."""

    @patch("portfotrack.cli.web_cli.web.create_app")
    def test_web_start_calls_app_run(self, mock_create_app):
        """'web start' should call app.run with default host/port."""
        from portfotrack.cli.web_cli.web import handle_web

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        state = ReplState()
        handle_web(state, ["start"])

        mock_app.run.assert_called_once_with(host="127.0.0.1", port=5000, debug=False)

    @patch("portfotrack.cli.web_cli.web.create_app")
    def test_web_start_custom_port(self, mock_create_app):
        """'web start --port 8080' should use custom port."""
        from portfotrack.cli.web_cli.web import handle_web

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        state = ReplState()
        handle_web(state, ["start", "--port", "8080"])

        mock_app.run.assert_called_once_with(host="127.0.0.1", port=8080, debug=False)

    @patch("portfotrack.cli.web_cli.web.create_app")
    def test_web_start_custom_host(self, mock_create_app):
        """'web start --host 0.0.0.0' should use custom host."""
        from portfotrack.cli.web_cli.web import handle_web

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        state = ReplState()
        handle_web(state, ["start", "--host", "0.0.0.0"])

        mock_app.run.assert_called_once_with(host="0.0.0.0", port=5000, debug=False)

    def test_web_no_subcommand_prints_usage(self, capsys):
        """'web' without subcommand should print usage."""
        from portfotrack.cli.web_cli.web import handle_web

        state = ReplState()
        handle_web(state, [])

        captured = capsys.readouterr()
        assert "Usage" in captured.out or "usage" in captured.out.lower()


class TestWebDebugMode:
    """Flask debug mode must be disabled for thread safety.

    Flask's debug=True activates Werkzeug's reloader, which calls
    signal.signal() internally.  signal handlers can only be set in
    the main thread, so running app.run(debug=True) in a background
    thread raises ``ValueError: signal only works in main thread``.
    """

    @patch("portfotrack.cli.web_cli.web.create_app")
    def test_web_start_debug_disabled_for_thread_safety(self, mock_create_app):
        """app.run must be called with debug=False to avoid signal error."""
        from portfotrack.cli.web_cli.web import handle_web

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        state = ReplState()
        handle_web(state, ["start"])

        _, kwargs = mock_app.run.call_args
        assert kwargs.get("debug") is False, (
            "debug must be False when running Flask in a background thread "
            "to prevent signal.signal() ValueError"
        )


class TestWebServerErrorHandling:
    """run_server should surface unexpected errors to stderr."""

    @patch("portfotrack.cli.web_cli.web.create_app")
    def test_run_server_prints_to_stderr_on_exception(self, mock_create_app, capsys):
        """If app.run raises, the error message must appear on stderr."""
        from portfotrack.cli.web_cli.web import handle_web

        mock_app = MagicMock()
        mock_app.run.side_effect = OSError("Address already in use")
        mock_create_app.return_value = mock_app

        state = ReplState()
        handle_web(state, ["start"])

        # Wait briefly for the daemon thread to execute and crash
        if state.web_server_thread is not None:
            state.web_server_thread.join(timeout=2)

        captured = capsys.readouterr()
        assert "Web server encountered an error" in captured.err


class TestWebBackgroundExecution:
    """web start should run Flask in a background thread.

    This ensures that the REPL loop continues after 'web start'
    is invoked, rather than blocking on app.run().
    """

    @patch("portfotrack.cli.web_cli.web.create_app")
    def test_web_start_runs_in_background_thread(self, mock_create_app):
        """'web start' should start Flask server in a background thread."""
        from portfotrack.cli.web_cli.web import handle_web

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        state = ReplState()
        handle_web(state, ["start"])

        # The function should return immediately without blocking
        # (test completes quickly instead of waiting for app.run() to block)

        # Verify that app.run() was called
        assert mock_app.run.called

    @patch("portfotrack.cli.web_cli.web.create_app")
    def test_web_start_server_thread_is_daemon(self, mock_create_app):
        """The server thread should be a daemon thread.

        This ensures the program can exit cleanly even if the server
        thread is still running.
        """
        from portfotrack.cli.web_cli.web import handle_web

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        # Track which thread runs app.run
        app_run_thread = None

        def capture_run_thread(*args, **kwargs):
            nonlocal app_run_thread
            app_run_thread = threading.current_thread()

        mock_app.run.side_effect = capture_run_thread

        state = ReplState()
        handle_web(state, ["start"])

        # Verify app.run was called in a different thread than main
        assert app_run_thread is not None
        assert app_run_thread != threading.current_thread()
        assert app_run_thread.daemon is True

    @patch("portfotrack.cli.web_cli.web.create_app")
    def test_web_start_server_thread_stores_in_state(self, mock_create_app):
        """The server thread reference should be stored in ReplState.

        This allows other commands to access or stop the running server.
        """
        from portfotrack.cli.web_cli.web import handle_web

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        state = ReplState()
        handle_web(state, ["start"])

        # Verify that state has a reference to the running server thread
        assert hasattr(state, "web_server_thread")
        assert state.web_server_thread is not None
        assert isinstance(state.web_server_thread, threading.Thread)
        assert state.web_server_thread.daemon is True


class TestWebStop:
    """web stop should cleanly terminate the running server thread."""

    def test_web_stop_no_server_running(self, capsys):
        """'web stop' with no running server should print message."""
        from portfotrack.cli.web_cli.web import handle_web

        state = ReplState()
        state.web_server_thread = None

        handle_web(state, ["stop"])

        captured = capsys.readouterr()
        assert (
            "not running" in captured.out.lower() or "no server" in captured.out.lower()
        )

    def test_web_stop_terminates_running_server(self):
        """'web stop' should terminate the running server thread."""
        from portfotrack.cli.web_cli.web import handle_web

        # Create a mock server thread
        mock_thread = MagicMock(spec=threading.Thread)
        mock_thread.is_alive.return_value = True

        state = ReplState()
        state.web_server_thread = mock_thread

        handle_web(state, ["stop"])

        # After stop, the state should have web_server_thread set to None
        assert state.web_server_thread is None
