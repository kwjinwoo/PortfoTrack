"""Tests for static file serving and template rendering."""

import pytest


@pytest.fixture()
def client():
    """Create a test client for the Flask app."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


class TestIndexPage:
    """Tests for the root / page serving."""

    def test_index_returns_200(self, client):
        """GET / should return HTTP 200."""
        response = client.get("/")

        assert response.status_code == 200

    def test_index_returns_html(self, client):
        """GET / should return text/html content type."""
        response = client.get("/")

        assert "text/html" in response.content_type

    def test_index_contains_portfotrack_title(self, client):
        """GET / should contain PortfoTrack in the page title."""
        response = client.get("/")
        html = response.data.decode("utf-8")

        assert "PortfoTrack" in html

    def test_index_links_stylesheet(self, client):
        """GET / should reference the main CSS stylesheet."""
        response = client.get("/")
        html = response.data.decode("utf-8")

        assert "styles.css" in html

    def test_index_links_javascript(self, client):
        """GET / should reference the main JavaScript file."""
        response = client.get("/")
        html = response.data.decode("utf-8")

        assert "app.js" in html

    def test_index_contains_dashboard_summary_regions(self, client):
        """GET / should expose dashboard summary and action regions."""
        response = client.get("/")
        html = response.data.decode("utf-8")

        assert "dashboard-summary" in html
        assert "latest-snapshot-date" in html
        assert "dashboard-next-actions" in html
        assert "drift-status" in html

    def test_index_contains_setup_flow_regions(self, client):
        """GET / should expose setup flow steps for first-time users."""
        response = client.get("/")
        html = response.data.decode("utf-8")

        assert "dashboard-setup-flow" in html
        assert 'data-setup-step="target"' in html
        assert 'data-setup-step="snapshot"' in html
        assert 'data-setup-step="report"' in html
        assert 'data-setup-step="trend"' in html

    def test_index_links_dashboard_javascript(self, client):
        """GET / should reference the dashboard JavaScript file."""
        response = client.get("/")
        html = response.data.decode("utf-8")

        assert "dashboard-ui.js" in html


class TestStaticFiles:
    """Tests for static CSS and JS file serving."""

    def test_css_file_accessible(self, client):
        """GET /static/css/styles.css should return 200."""
        response = client.get("/static/css/styles.css")

        assert response.status_code == 200

    def test_js_file_accessible(self, client):
        """GET /static/js/app.js should return 200."""
        response = client.get("/static/js/app.js")

        assert response.status_code == 200

    def test_dashboard_js_file_accessible(self, client):
        """GET /static/js/dashboard-ui.js should return 200."""
        response = client.get("/static/js/dashboard-ui.js")

        assert response.status_code == 200
