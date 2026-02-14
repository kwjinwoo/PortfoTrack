"""Tests for the web CLI command handler."""

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

        mock_app.run.assert_called_once_with(host="127.0.0.1", port=5000, debug=True)

    @patch("portfotrack.cli.web_cli.web.create_app")
    def test_web_start_custom_port(self, mock_create_app):
        """'web start --port 8080' should use custom port."""
        from portfotrack.cli.web_cli.web import handle_web

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        state = ReplState()
        handle_web(state, ["start", "--port", "8080"])

        mock_app.run.assert_called_once_with(host="127.0.0.1", port=8080, debug=True)

    @patch("portfotrack.cli.web_cli.web.create_app")
    def test_web_start_custom_host(self, mock_create_app):
        """'web start --host 0.0.0.0' should use custom host."""
        from portfotrack.cli.web_cli.web import handle_web

        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        state = ReplState()
        handle_web(state, ["start", "--host", "0.0.0.0"])

        mock_app.run.assert_called_once_with(host="0.0.0.0", port=5000, debug=True)

    def test_web_no_subcommand_prints_usage(self, capsys):
        """'web' without subcommand should print usage."""
        from portfotrack.cli.web_cli.web import handle_web

        state = ReplState()
        handle_web(state, [])

        captured = capsys.readouterr()
        assert "Usage" in captured.out or "usage" in captured.out.lower()
