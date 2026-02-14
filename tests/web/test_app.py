"""Tests for Flask application factory and health endpoint."""

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
