"""Tests for snapshot API endpoints.

Covers:
- GET  /api/snapshots        — list snapshot files
- GET  /api/snapshots/<date>  — load a specific snapshot
- POST /api/snapshots         — create and save a new snapshot
"""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect SNAPSHOTS_DIR to a temporary directory for isolation."""
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()

    import portfotrack.path as path_mod
    import portfotrack.services.snapshot_services as svc_mod
    import portfotrack.storage.json_store.snapshot_store as store_mod

    monkeypatch.setattr(path_mod, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(svc_mod, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(store_mod, "SNAPSHOTS_DIR", snapshots_dir)

    return snapshots_dir


@pytest.fixture()
def client(tmp_data_dir):
    """Create a test client with isolated data directory."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


def _write_snapshot_file(snapshots_dir: Path, date: str) -> None:
    """Write a minimal valid snapshot JSON file to the given directory."""
    dto = {
        "date": date,
        "currency": "KRW",
        "items": [
            {"asset_id": "us_equity", "label": "S&P500", "amount": 5_000_000},
        ],
    }
    file_name = f"snapshot_{date}_v1.json"
    with open(snapshots_dir / file_name, "w", encoding="utf-8") as f:
        json.dump(dto, f, ensure_ascii=False, indent=2)


class TestListSnapshots:
    """GET /api/snapshots — list available snapshot dates."""

    def test_empty_directory_returns_empty_list(self, client):
        """When no snapshots exist, returns an empty list."""
        response = client.get("/api/snapshots")

        assert response.status_code == 200
        assert response.get_json() == []

    def test_returns_list_of_dates(self, client, tmp_data_dir):
        """When snapshots exist, returns sorted date list."""
        _write_snapshot_file(tmp_data_dir, "2026-02-10")
        _write_snapshot_file(tmp_data_dir, "2026-02-12")

        response = client.get("/api/snapshots")

        data = response.get_json()
        assert response.status_code == 200
        assert len(data) == 2
        assert data[0]["date"] == "2026-02-10"
        assert data[1]["date"] == "2026-02-12"


class TestGetSnapshot:
    """GET /api/snapshots/<date> — load a specific snapshot."""

    def test_existing_snapshot_returns_200(self, client, tmp_data_dir):
        """Loading an existing snapshot returns its data."""
        _write_snapshot_file(tmp_data_dir, "2026-02-12")

        response = client.get("/api/snapshots/2026-02-12")

        assert response.status_code == 200
        data = response.get_json()
        assert data["date"] == "2026-02-12"
        assert data["currency"] == "KRW"
        assert len(data["items"]) == 1

    def test_nonexistent_snapshot_returns_404(self, client):
        """Requesting a missing snapshot returns 404."""
        response = client.get("/api/snapshots/2099-01-01")

        assert response.status_code == 404

    def test_invalid_date_format_returns_400(self, client):
        """Requesting with invalid date format returns 400."""
        response = client.get("/api/snapshots/not-a-date")

        assert response.status_code == 400


class TestCreateSnapshot:
    """POST /api/snapshots — create and persist a new snapshot."""

    def test_create_snapshot_returns_201(self, client):
        """Creating a valid snapshot returns 201."""
        payload = {
            "items": [
                {"asset_id": "us_equity", "label": "S&P500", "amount": 5_000_000},
            ]
        }

        response = client.post(
            "/api/snapshots",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "date" in data
        assert data["currency"] == "KRW"

    def test_create_snapshot_persists_to_disk(self, client, tmp_data_dir):
        """After creation, the snapshot file exists on disk."""
        payload = {
            "items": [
                {"asset_id": "us_equity", "label": "S&P500", "amount": 5_000_000},
            ]
        }

        client.post(
            "/api/snapshots",
            data=json.dumps(payload),
            content_type="application/json",
        )

        files = list(tmp_data_dir.glob("snapshot_*.json"))
        assert len(files) == 1

    def test_create_snapshot_missing_items_returns_400(self, client):
        """Creating a snapshot without items returns 400."""
        response = client.post(
            "/api/snapshots",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_create_snapshot_empty_items_returns_400(self, client):
        """Creating a snapshot with empty items list returns 400."""
        response = client.post(
            "/api/snapshots",
            data=json.dumps({"items": []}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_create_snapshot_invalid_item_returns_400(self, client):
        """Creating a snapshot with invalid item structure returns 400."""
        payload = {
            "items": [
                {"asset_id": "us_equity", "label": "S&P500"},  # missing amount
            ]
        }

        response = client.post(
            "/api/snapshots",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400
