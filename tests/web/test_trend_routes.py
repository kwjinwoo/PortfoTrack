"""Tests for trend analysis API endpoint.

Covers:
- GET /api/trends/analysis — full trend data
- Empty snapshots returns 200 with empty data
- Error handling for missing data
"""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect SNAPSHOTS_DIR to temp directory."""
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()

    import portfotrack.path as path_mod
    import portfotrack.services.snapshot_services as snap_svc
    import portfotrack.services.trend_analysis as trend_svc
    import portfotrack.storage.json_store.snapshot_store as snap_store

    monkeypatch.setattr(path_mod, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(snap_svc, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(snap_store, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(trend_svc, "SNAPSHOTS_DIR", snapshots_dir)

    return {"snapshots": snapshots_dir}


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


class TestTrendAnalysisEndpoint:
    """GET /api/trends/analysis — generate trend data."""

    def test_returns_200_with_empty_data_when_no_snapshots(self, client) -> None:
        """No snapshots yields 200 with empty trend data."""
        response = client.get("/api/trends/analysis")

        assert response.status_code == 200
        data = response.get_json()
        assert data["asset_trends"] == []
        assert data["portfolio_trend"] == []
        assert data["metadata"]["snapshot_count"] == 0

    def test_returns_200_with_single_snapshot(self, client, tmp_data_dir) -> None:
        """One snapshot produces valid trend data."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [
                {"asset_id": "us-etf", "label": "S&P500", "amount": 6_000_000},
                {"asset_id": "gold", "label": "GOLD", "amount": 4_000_000},
            ],
        )

        response = client.get("/api/trends/analysis")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["asset_trends"]) == 2
        assert len(data["portfolio_trend"]) == 1
        assert data["portfolio_trend"][0]["total_amount"] == 10_000_000
        assert data["metadata"]["snapshot_count"] == 1

    def test_returns_200_with_multiple_snapshots(self, client, tmp_data_dir) -> None:
        """Multiple snapshots produce chronological trend data."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [
                {"asset_id": "us-etf", "label": "S&P500", "amount": 6_000_000},
                {"asset_id": "gold", "label": "GOLD", "amount": 4_000_000},
            ],
        )
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-14",
            [
                {"asset_id": "us-etf", "label": "S&P500", "amount": 6_500_000},
                {"asset_id": "gold", "label": "GOLD", "amount": 4_200_000},
            ],
        )

        response = client.get("/api/trends/analysis")

        assert response.status_code == 200
        data = response.get_json()
        assert data["metadata"]["snapshot_count"] == 2
        assert data["metadata"]["start_date"] == "2026-02-12"
        assert data["metadata"]["end_date"] == "2026-02-14"
        assert len(data["portfolio_trend"]) == 2

    def test_asset_trend_structure(self, client, tmp_data_dir) -> None:
        """Each asset trend contains asset_id, asset_name, and data_points."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [{"asset_id": "us-etf", "label": "S&P500", "amount": 5_000_000}],
        )

        response = client.get("/api/trends/analysis")

        data = response.get_json()
        trend = data["asset_trends"][0]
        assert "asset_id" in trend
        assert "asset_name" in trend
        assert "data_points" in trend
        point = trend["data_points"][0]
        assert "date" in point
        assert "amount" in point
        assert "ratio" in point

    def test_portfolio_trend_structure(self, client, tmp_data_dir) -> None:
        """Each portfolio trend point contains date, total_amount, and change_pct."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [{"asset_id": "us-etf", "label": "S&P500", "amount": 5_000_000}],
        )

        response = client.get("/api/trends/analysis")

        data = response.get_json()
        point = data["portfolio_trend"][0]
        assert "date" in point
        assert "total_amount" in point
        assert "change_pct" in point

    def test_portfolio_trend_change_pct_values(self, client, tmp_data_dir) -> None:
        """change_pct reflects percentage change from previous snapshot."""
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-12",
            [{"asset_id": "us-etf", "label": "S&P500", "amount": 10_000_000}],
        )
        _write_snapshot(
            tmp_data_dir["snapshots"],
            "2026-02-14",
            [{"asset_id": "us-etf", "label": "S&P500", "amount": 12_000_000}],
        )

        response = client.get("/api/trends/analysis")

        data = response.get_json()
        assert data["portfolio_trend"][0]["change_pct"] == pytest.approx(0.0)
        assert data["portfolio_trend"][1]["change_pct"] == pytest.approx(20.0)
