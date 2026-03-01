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

    def test_optional_bets_page_returns_200(self, client):
        """GET /optional-bets should return 200."""
        response = client.get("/optional-bets")
        assert response.status_code == 200

    def test_optional_bets_page_contains_title(self, client):
        """Optional bets page should contain section heading."""
        response = client.get("/optional-bets")
        html = response.data.decode("utf-8")
        assert "옵셔널 벳" in html


class TestNavigation:
    """Navigation links should be present on all pages."""

    @pytest.mark.parametrize(
        "path", ["/", "/snapshots", "/targets", "/reports", "/optional-bets"]
    )
    def test_nav_links_present(self, client, path):
        """Each page should contain navigation links to all sections."""
        response = client.get(path)
        html = response.data.decode("utf-8")

        assert "/snapshots" in html
        assert "/targets" in html
        assert "/reports" in html
        assert "/optional-bets" in html


class TestOptionalBetsTrendUI:
    """Optional bets page should contain trend chart elements."""

    def test_page_contains_trend_chart_containers(self, client) -> None:
        """Page should have canvas elements for the three trend charts."""
        response = client.get("/optional-bets")
        html = response.data.decode("utf-8")
        assert "ob-ratio-chart" in html
        assert "ob-amount-chart" in html
        assert "ob-total-chart" in html

    def test_page_loads_chart_js(self, client) -> None:
        """Page should reference Chart.js CDN."""
        response = client.get("/optional-bets")
        html = response.data.decode("utf-8")
        assert "chart.js" in html.lower() or "Chart" in html

    def test_page_loads_trend_script(self, client) -> None:
        """Page should load the optional-bets-trend-ui.js script."""
        response = client.get("/optional-bets")
        html = response.data.decode("utf-8")
        assert "optional-bets-trend-ui.js" in html

    def test_page_contains_trend_section_heading(self, client) -> None:
        """Page should contain a heading for the trend analysis section."""
        response = client.get("/optional-bets")
        html = response.data.decode("utf-8")
        assert "추이 분석" in html
