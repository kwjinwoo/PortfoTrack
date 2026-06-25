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

    @pytest.mark.parametrize(
        ("path", "label"),
        [
            ("/", "대시보드"),
            ("/snapshots", "스냅샷"),
            ("/targets", "타겟"),
            ("/reports", "리포트"),
            ("/trends", "추이"),
            ("/optional-bets", "옵셔널 벳"),
        ],
    )
    def test_current_nav_link_is_marked(self, client, path, label):
        """The active page link should expose a visual and semantic marker."""
        response = client.get(path)
        html = response.data.decode("utf-8")

        assert f'aria-current="page">{label}</a>' in html
        assert 'class="nav-link is-active"' in html


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
        """Page should reference local Chart.js assets."""
        response = client.get("/optional-bets")
        html = response.data.decode("utf-8")
        assert "https://cdn.jsdelivr.net" not in html
        assert "vendor/chart.umd.js" in html
        assert "vendor/chartjs-plugin-datalabels.min.js" in html

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

    def test_trend_charts_use_chart_panels(self, client) -> None:
        """Optional bet trend charts should not be nested as cards."""
        response = client.get("/optional-bets")
        html = response.data.decode("utf-8")

        assert 'class="chart-panel"' in html
        assert 'class="card" style="margin-top: 1rem;"' not in html


class TestOptionalBetsInputs:
    """Optional bet forms should use user-facing units consistently."""

    def test_cap_ratio_input_uses_percent_unit(self, client) -> None:
        """The optional bet cap ratio field should accept percent-scale values."""
        response = client.get("/optional-bets")
        html = response.data.decode("utf-8")

        assert "캡 비율 (%)" in html
        assert 'placeholder="예: 5"' in html
        assert 'max="99"' in html


class TestResponsiveTables:
    """Wide data tables should be wrapped for small screens."""

    @pytest.mark.parametrize(
        "path",
        ["/snapshots", "/targets", "/reports", "/optional-bets"],
    )
    def test_data_tables_use_scroll_wrapper(self, client, path):
        """Pages with data tables should expose a responsive table container."""
        response = client.get(path)
        html = response.data.decode("utf-8")

        assert 'class="table-scroll"' in html


class TestEmptyStateActions:
    """Empty states should point users to the next useful action."""

    def test_snapshots_page_links_target_setup_from_warning(self, client):
        """Snapshot setup should offer a direct path to target setup."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'href="/targets"' in html
        assert "타겟 설정으로 이동" in html

    def test_reports_page_contains_snapshot_empty_state(self, client):
        """Reports should expose a first action when no snapshots exist."""
        response = client.get("/reports")
        html = response.data.decode("utf-8")

        assert 'id="report-empty-state"' in html
        assert 'href="/snapshots"' in html

    def test_optional_bets_page_contains_empty_state_action_region(self, client):
        """Optional bets should reserve a clear empty-state action region."""
        response = client.get("/optional-bets")
        html = response.data.decode("utf-8")

        assert 'class="empty-state-actions"' in html
        assert "새 옵셔널 벳 생성" in html


class TestSnapshotFormLayout:
    """Snapshot amount entry should remain scannable as rows grow."""

    def test_snapshot_create_form_uses_dense_item_rows(self, client):
        """The initial snapshot row should expose the compact row classes."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'class="item-row snapshot-item-row"' in html
        assert 'class="amount-input"' in html
        assert 'inputmode="numeric"' in html


class TestTargetSaveConfirmation:
    """Target edits should confirm ratio mismatches inside the page."""

    def test_target_edit_page_contains_ratio_warning_panel(self, client):
        """The target page should expose an in-app ratio warning panel."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert 'id="target-ratio-warning"' in html
        assert "그래도 저장" in html
