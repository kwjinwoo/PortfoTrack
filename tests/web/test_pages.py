"""Tests for page navigation and layout."""

import pytest


@pytest.fixture()
def client():
    """Create a test client for the Flask app."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


class TestPageRoutes:
    """All page routes should return 200 and contain expected content."""

    def test_snapshots_page_returns_200(self, client):
        """GET /snapshots should return 200."""
        response = client.get("/snapshots")
        assert response.status_code == 200

    def test_targets_page_returns_200(self, client):
        """GET /targets should return 200."""
        response = client.get("/targets")
        assert response.status_code == 200

    def test_reports_page_returns_200(self, client):
        """GET /reports should return 200."""
        response = client.get("/reports")
        assert response.status_code == 200

    def test_snapshots_page_contains_title(self, client):
        """Snapshots page should contain section heading."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")
        assert "스냅샷" in html

    def test_targets_page_contains_title(self, client):
        """Targets page should contain section heading."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")
        assert "타겟" in html

    def test_reports_page_contains_title(self, client):
        """Reports page should contain section heading."""
        response = client.get("/reports")
        html = response.data.decode("utf-8")
        assert "리포트" in html


class TestNavigation:
    """Navigation links should be present on all pages."""

    @pytest.mark.parametrize("path", ["/", "/snapshots", "/targets", "/reports"])
    def test_nav_links_present(self, client, path):
        """Each page should contain navigation links to all sections."""
        response = client.get(path)
        html = response.data.decode("utf-8")

        assert "/snapshots" in html
        assert "/targets" in html
        assert "/reports" in html
