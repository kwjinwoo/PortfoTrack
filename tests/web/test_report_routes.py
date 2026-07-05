"""Tests for allocation report API endpoint.

Covers:
- GET /api/reports/allocation?snapshot_date=YYYY-MM-DD
"""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect SNAPSHOTS_DIR and TARGETS_DIR to temp directories."""
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()
    targets_dir = tmp_path / "targets"
    targets_dir.mkdir()

    import portfotrack.path as path_mod
    import portfotrack.services.snapshot_services as snap_svc
    import portfotrack.services.target_services as target_svc
    import portfotrack.storage.json_store.snapshot_store as snap_store
    import portfotrack.storage.json_store.target_store as target_store

    monkeypatch.setattr(path_mod, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(path_mod, "TARGETS_DIR", targets_dir)
    monkeypatch.setattr(snap_svc, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(snap_store, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(target_svc, "TARGETS_DIR", targets_dir)
    monkeypatch.setattr(target_store, "TARGETS_DIR", targets_dir)

    return {"snapshots": snapshots_dir, "targets": targets_dir}


@pytest.fixture()
def client(tmp_data_dir):
    """Create a test client with isolated data directories."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


def _write_snapshot(snapshots_dir: Path, date: str, items: list) -> None:
    """Write a snapshot JSON file."""
    dto = {"date": date, "currency": "KRW", "items": items}
    file_name = f"snapshot_{date}_v1.json"
    with open(snapshots_dir / file_name, "w", encoding="utf-8") as f:
        json.dump(dto, f, ensure_ascii=False, indent=2)


def _write_target(targets_dir: Path, date: str, assets: list) -> None:
    """Write a target allocation JSON file."""
    dto = {"assets": assets}
    file_name = f"target_{date}_v1.json"
    with open(targets_dir / file_name, "w", encoding="utf-8") as f:
        json.dump(dto, f, ensure_ascii=False, indent=2)


class TestAllocationReport:
    """GET /api/reports/allocation — generate allocation report."""

    def test_report_returns_200(self, client, tmp_data_dir):
        """Valid snapshot + target produces a 200 response."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [
                {"asset_id": "us_equity", "label": "S&P500", "amount": 6_000_000},
                {"asset_id": "kr_bond", "label": "국채", "amount": 4_000_000},
            ],
        )
        _write_target(
            tmp_data_dir["targets"],
            "2026-02-07",
            [
                {
                    "id": "us_equity",
                    "name": "US Equity",
                    "purpose": "growth",
                    "target_ratio": 0.6,
                    "tolerance": {"lower": 0.5, "upper": 0.7},
                },
                {
                    "id": "kr_bond",
                    "name": "KR Bond",
                    "purpose": "stability",
                    "target_ratio": 0.4,
                    "tolerance": {"lower": 0.3, "upper": 0.5},
                },
            ],
        )

        response = client.get("/api/reports/allocation?snapshot_date=2026-02-12")

        assert response.status_code == 200
        data = response.get_json()
        assert data["snapshot_date"] == "2026-02-12"
        assert data["total_portfolio_amount"] == 10_000_000
        assert len(data["items"]) == 2

    def test_report_item_fields(self, client, tmp_data_dir):
        """Report items should contain expected fields."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [{"asset_id": "us_equity", "label": "S&P500", "amount": 10_000_000}],
        )
        _write_target(
            tmp_data_dir["targets"],
            "2026-02-07",
            [
                {
                    "id": "us_equity",
                    "name": "US Equity",
                    "purpose": "growth",
                    "target_ratio": 1.0,
                    "tolerance": {"lower": 0.9, "upper": 1.0},
                },
            ],
        )

        response = client.get("/api/reports/allocation?snapshot_date=2026-02-12")

        data = response.get_json()
        item = data["items"][0]
        assert "asset_id" in item
        assert "asset_name" in item
        assert "current_amount" in item
        assert "current_ratio" in item
        assert "target_ratio" in item
        assert "target_amount_needed" in item
        assert "is_within_tolerance" in item

    def test_missing_snapshot_date_returns_400(self, client):
        """Omitting snapshot_date query param returns 400."""
        response = client.get("/api/reports/allocation")

        assert response.status_code == 400

    def test_nonexistent_snapshot_returns_404(self, client, tmp_data_dir):
        """Requesting report for missing snapshot returns 404."""
        _write_target(
            tmp_data_dir["targets"],
            "2026-02-07",
            [
                {
                    "id": "us_equity",
                    "name": "US Equity",
                    "purpose": "growth",
                    "target_ratio": 1.0,
                    "tolerance": {"lower": 0.9, "upper": 1.0},
                },
            ],
        )

        response = client.get("/api/reports/allocation?snapshot_date=2099-01-01")

        assert response.status_code == 404

    def test_no_target_returns_404(self, client, tmp_data_dir):
        """Requesting report with no target returns 404."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [{"asset_id": "us_equity", "label": "S&P500", "amount": 10_000_000}],
        )

        response = client.get("/api/reports/allocation?snapshot_date=2026-02-12")

        assert response.status_code == 404

    def test_report_is_complete_field(self, client, tmp_data_dir):
        """Report should include is_complete boolean."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [{"asset_id": "us_equity", "label": "S&P500", "amount": 10_000_000}],
        )
        _write_target(
            tmp_data_dir["targets"],
            "2026-02-07",
            [
                {
                    "id": "us_equity",
                    "name": "US Equity",
                    "purpose": "growth",
                    "target_ratio": 1.0,
                    "tolerance": {"lower": 0.9, "upper": 1.0},
                },
            ],
        )

        response = client.get("/api/reports/allocation?snapshot_date=2026-02-12")

        data = response.get_json()
        assert "is_complete" in data
        assert data["is_complete"] is True


class TestAllocationMarkdownExport:
    """GET /api/reports/allocation/export — export target and snapshot."""

    def test_returns_downloadable_markdown(self, client, tmp_data_dir):
        """A valid portfolio produces a UTF-8 Markdown attachment."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [{"asset_id": "us_equity", "label": "S&P500", "amount": 10_000_000}],
        )
        _write_target(
            tmp_data_dir["targets"],
            "2026-02-07",
            [
                {
                    "id": "us_equity",
                    "name": "US Equity",
                    "purpose": "growth",
                    "target_ratio": 1.0,
                    "tolerance": {"lower": 0.9, "upper": 1.0},
                }
            ],
        )

        response = client.get("/api/reports/allocation/export?snapshot_date=2026-02-12")

        assert response.status_code == 200
        assert response.mimetype == "text/markdown"
        assert "portfotrack-2026-02-12.md" in response.headers["Content-Disposition"]
        assert "S&P500" in response.get_data(as_text=True)
        assert "ChatGPT에게 요청할 내용" not in response.get_data(as_text=True)

    def test_applies_privacy_options(self, client, tmp_data_dir):
        """Query options omit labels and exact amounts from the export."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [{"asset_id": "us_equity", "label": "S&P500", "amount": 10_000_000}],
        )
        _write_target(
            tmp_data_dir["targets"],
            "2026-02-07",
            [
                {
                    "id": "us_equity",
                    "name": "US Equity",
                    "purpose": "growth",
                    "target_ratio": 1.0,
                    "tolerance": {"lower": 0.9, "upper": 1.0},
                }
            ],
        )

        response = client.get(
            "/api/reports/allocation/export"
            "?snapshot_date=2026-02-12&include_labels=false&hide_amounts=true"
        )

        markdown = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "S&P500" not in markdown
        assert "10,000,000" not in markdown


class TestAllocationContextExport:
    """GET /api/reports/allocation/export.json — versioned JSON download."""

    def test_returns_downloadable_versioned_json(self, client, tmp_data_dir):
        """An explicitly selected snapshot produces an attachment."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [
                {"asset_id": "us_equity", "label": "S&P500", "amount": 4_000_000},
                {"asset_id": "kr_bond", "label": "Bond", "amount": 6_000_000},
            ],
        )
        _write_target(
            tmp_data_dir["targets"],
            "2026-02-07",
            [
                {
                    "id": "us_equity",
                    "name": "US Equity",
                    "purpose": "growth",
                    "target_ratio": 0.6,
                    "tolerance": {"lower": 0.5, "upper": 0.7},
                },
                {
                    "id": "kr_bond",
                    "name": "KR Bond",
                    "purpose": "stability",
                    "target_ratio": 0.4,
                    "tolerance": {"lower": 0.3, "upper": 0.5},
                },
            ],
        )

        response = client.get(
            "/api/reports/allocation/export.json?snapshot_date=2026-02-12"
        )

        assert response.status_code == 200
        assert response.mimetype == "application/json"
        assert response.headers["Content-Disposition"] == (
            'attachment; filename="portfotrack-allocation-2026-02-12-v1.json"'
        )
        payload = response.get_json()
        assert payload["schema_version"] == "1.0"
        assert payload["snapshot"]["currency"] == "KRW"
        assert [item["asset_id"] for item in payload["assets"]] == [
            "kr_bond",
            "us_equity",
        ]
        assert all("label" not in item for item in payload["assets"])

    def test_requires_explicit_snapshot_date(self, client):
        """The export never silently selects the latest snapshot."""
        response = client.get("/api/reports/allocation/export.json")

        assert response.status_code == 400
        assert response.get_json() == {
            "error": "Query parameter 'snapshot_date' is required."
        }

    def test_rejects_invalid_snapshot_date(self, client):
        """Malformed dates use the same 400 boundary as other report routes."""
        response = client.get(
            "/api/reports/allocation/export.json?snapshot_date=2026-2-12"
        )

        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid date format. Use YYYY-MM-DD."}

    def test_returns_404_for_missing_snapshot(self, client, tmp_data_dir):
        """An unavailable explicitly selected snapshot returns 404."""
        response = client.get(
            "/api/reports/allocation/export.json?snapshot_date=2099-01-01"
        )

        assert response.status_code == 404
        assert response.get_json() == {"error": "Snapshot for 2099-01-01 not found."}

    def test_returns_404_for_missing_target(self, client, tmp_data_dir):
        """An existing snapshot without a target returns 404."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [{"asset_id": "us_equity", "label": "S&P500", "amount": 1}],
        )

        response = client.get(
            "/api/reports/allocation/export.json?snapshot_date=2026-02-12"
        )

        assert response.status_code == 404
        assert response.get_json() == {"error": "No target allocation found."}
