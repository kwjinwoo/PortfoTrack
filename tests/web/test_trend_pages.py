"""Tests for trends UI page.

Covers:
- GET /trends returns 200 with expected content
- Page contains chart containers and script references
- Navigation link added to base template
"""

import pytest


@pytest.fixture()
def client():
    """Create a test client for the Flask app."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


class TestTrendsPage:
    """GET /trends — trend analysis page rendering."""

    def test_trends_page_returns_200(self, client) -> None:
        """GET /trends should return 200."""
        response = client.get("/trends")
        assert response.status_code == 200

    def test_trends_page_contains_title(self, client) -> None:
        """Trends page should contain the section heading."""
        response = client.get("/trends")
        html = response.data.decode("utf-8")
        assert "추이 분석" in html

    def test_trends_page_contains_chart_containers(self, client) -> None:
        """Trends page should have canvas elements for the three charts."""
        response = client.get("/trends")
        html = response.data.decode("utf-8")
        assert "ratio-chart" in html
        assert "amount-chart" in html
        assert "total-chart" in html

    def test_trends_page_loads_chart_js(self, client) -> None:
        """Trends page should reference Chart.js CDN."""
        response = client.get("/trends")
        html = response.data.decode("utf-8")
        assert "chart.js" in html.lower() or "Chart" in html

    def test_trends_page_loads_trends_ui_script(self, client) -> None:
        """Trends page should load the trends-ui.js script."""
        response = client.get("/trends")
        html = response.data.decode("utf-8")
        assert "trends-ui.js" in html

    def test_navigation_contains_trends_link(self, client) -> None:
        """Base navigation should include a link to /trends."""
        response = client.get("/")
        html = response.data.decode("utf-8")
        assert "/trends" in html

    def test_trends_page_includes_datalabels_plugin(self, client) -> None:
        """Trends page should load the chartjs-plugin-datalabels script."""
        response = client.get("/trends")
        html = response.data.decode("utf-8")
        assert "chartjs-plugin-datalabels" in html

    def test_trends_page_has_comparison_dropdowns(self, client) -> None:
        """Trends page should contain two select elements for snapshot comparison."""
        response = client.get("/trends")
        html = response.data.decode("utf-8")
        assert 'id="compare-from"' in html
        assert 'id="compare-to"' in html

    def test_trends_page_has_comparison_result(self, client) -> None:
        """Trends page should contain a comparison result display area."""
        response = client.get("/trends")
        html = response.data.decode("utf-8")
        assert 'id="comparison-result"' in html
