"""Tests for Flask application factory, health endpoint, and run_server."""

from unittest.mock import patch

import pytest


class TestCreateApp:
    """Tests for the create_app factory function."""

    def test_create_app_returns_flask_instance(self):
        """create_app should return a Flask application instance."""
        from portfotrack.web.app import create_app

        app = create_app()

        assert app is not None
        assert app.name == "portfotrack.web.app"

    def test_create_app_sets_testing_flag(self):
        """create_app should respect TESTING config override."""
        from portfotrack.web.app import create_app

        app = create_app({"TESTING": True})

        assert app.config["TESTING"] is True


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    @pytest.fixture()
    def client(self):
        """Create a test client for the Flask app."""
        from portfotrack.web.app import create_app

        app = create_app({"TESTING": True})
        return app.test_client()

    def test_health_returns_200(self, client):
        """GET /health should return HTTP 200."""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_returns_json_status_ok(self, client):
        """GET /health should return JSON body with status 'ok'."""
        response = client.get("/health")

        data = response.get_json()
        assert data == {"status": "ok"}

    def test_health_content_type_is_json(self, client):
        """GET /health should return application/json content type."""
        response = client.get("/health")

        assert response.content_type == "application/json"


class TestRunServer:
    """Tests for the run_server entry point function."""

    def test_run_server_uses_default_host_and_port(self):
        """run_server with no args should start on 127.0.0.1:5000."""
        from portfotrack.web.app import run_server

        with patch("portfotrack.web.app.create_app") as mock_create:
            mock_app = mock_create.return_value
            run_server([])

            mock_create.assert_called_once()
            mock_app.run.assert_called_once_with(
                host="127.0.0.1", port=5000, debug=False
            )

    def test_run_server_accepts_custom_host(self):
        """run_server should accept --host argument."""
        from portfotrack.web.app import run_server

        with patch("portfotrack.web.app.create_app") as mock_create:
            mock_app = mock_create.return_value
            run_server(["--host", "0.0.0.0"])

            mock_app.run.assert_called_once_with(host="0.0.0.0", port=5000, debug=False)

    def test_run_server_accepts_custom_port(self):
        """run_server should accept --port argument."""
        from portfotrack.web.app import run_server

        with patch("portfotrack.web.app.create_app") as mock_create:
            mock_app = mock_create.return_value
            run_server(["--port", "8080"])

            mock_app.run.assert_called_once_with(
                host="127.0.0.1", port=8080, debug=False
            )

    def test_run_server_accepts_both_host_and_port(self):
        """run_server should accept both --host and --port arguments."""
        from portfotrack.web.app import run_server

        with patch("portfotrack.web.app.create_app") as mock_create:
            mock_app = mock_create.return_value
            run_server(["--host", "0.0.0.0", "--port", "9090"])

            mock_app.run.assert_called_once_with(host="0.0.0.0", port=9090, debug=False)

    def test_run_server_rejects_invalid_port(self):
        """run_server should reject non-integer port values."""
        from portfotrack.web.app import run_server

        with pytest.raises(SystemExit):
            run_server(["--port", "abc"])
