"""Tests for static file serving and template rendering."""

from pathlib import Path

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

    def test_optional_bets_js_converts_percent_inputs(self, client):
        """Optional bet UI should convert percent inputs before API calls."""
        response = client.get("/static/js/optional-bets-ui.js")
        js = response.data.decode("utf-8")

        assert "percentInputToRatio" in js
        assert "ratioToPercentInput" in js

    def test_ui_scripts_render_empty_state_actions(self, client):
        """UI scripts should render actionable empty states for missing data."""
        script_paths = [
            "/static/js/snapshots-ui.js",
            "/static/js/targets-ui.js",
            "/static/js/reports-ui.js",
            "/static/js/optional-bets-ui.js",
        ]

        for path in script_paths:
            response = client.get(path)
            js = response.data.decode("utf-8")
            assert "empty-state" in js

    def test_targets_js_uses_in_app_ratio_confirmation(self, client):
        """Target save warnings should avoid native browser confirm dialogs."""
        response = client.get("/static/js/targets-ui.js")
        js = response.data.decode("utf-8")

        assert "confirm(" not in js
        assert "target-ratio-warning" in js

    def test_ui_scripts_do_not_auto_clear_messages(self, client):
        """User-facing messages should remain visible until replaced."""
        script_paths = [
            "/static/js/snapshots-ui.js",
            "/static/js/targets-ui.js",
            "/static/js/reports-ui.js",
        ]

        for path in script_paths:
            response = client.get(path)
            js = response.data.decode("utf-8")
            assert "setTimeout" not in js

    def test_message_regions_are_announced(self, client):
        """Message regions should be exposed to assistive technologies."""
        page_paths = ["/snapshots", "/targets", "/reports", "/trends", "/optional-bets"]

        for path in page_paths:
            response = client.get(path)
            html = response.data.decode("utf-8")
            assert 'class="message' in html
            assert 'aria-live="polite"' in html

    def test_templates_do_not_use_inline_style_attributes(self):
        """Templates should express visual states through classes."""
        template_dir = (
            Path(__file__).resolve().parents[2]
            / "src"
            / "portfotrack"
            / "web"
            / "templates"
        )

        for path in template_dir.glob("*.html"):
            html = path.read_text(encoding="utf-8")
            assert 'style="' not in html, path.name

    @pytest.mark.parametrize(
        "path",
        [
            "/static/vendor/chart.umd.js",
            "/static/vendor/chartjs-plugin-datalabels.min.js",
        ],
    )
    def test_vendor_chart_assets_accessible(self, client, path):
        """Chart vendor assets should be served locally."""
        response = client.get(path)

        assert response.status_code == 200
