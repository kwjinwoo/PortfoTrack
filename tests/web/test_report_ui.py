"""Tests for allocation report UI page content.

Verifies that the reports page contains the expected HTML structure
(form elements, table structure, JS references) needed for the UI.
"""

import pytest


@pytest.fixture()
def client():
    """Create a test client for the Flask app."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


class TestReportsPageStructure:
    """Reports page should contain UI elements for report generation."""

    def test_contains_snapshot_selector(self, client):
        """Page should have a snapshot date selector."""
        response = client.get("/reports")
        html = response.data.decode("utf-8")

        assert 'id="snapshot-date-select"' in html

    def test_contains_report_form(self, client):
        """Page should have a report generation form."""
        response = client.get("/reports")
        html = response.data.decode("utf-8")

        assert 'id="report-form"' in html

    def test_contains_report_table(self, client):
        """Page should have a report results table."""
        response = client.get("/reports")
        html = response.data.decode("utf-8")

        assert 'id="report-table"' in html
        assert 'id="report-items"' in html

    def test_contains_report_summary(self, client):
        """Page should have a report summary section."""
        response = client.get("/reports")
        html = response.data.decode("utf-8")

        assert 'id="report-summary"' in html

    def test_contains_progress_column(self, client):
        """Report table should have a progress column header."""
        response = client.get("/reports")
        html = response.data.decode("utf-8")

        assert "진행률" in html

    def test_references_reports_js(self, client):
        """Page should reference the reports UI script."""
        response = client.get("/reports")
        html = response.data.decode("utf-8")

        assert "reports-ui.js" in html

    def test_reports_js_accessible(self, client):
        """The reports-ui.js file should be accessible."""
        response = client.get("/static/js/reports-ui.js")

        assert response.status_code == 200
