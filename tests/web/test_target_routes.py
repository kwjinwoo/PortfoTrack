"""Tests for target allocation API endpoints.

Covers:
- GET  /api/targets          — load latest target
- POST /api/targets          — create new target
- POST /api/targets/assets   — add asset to current target
"""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect TARGETS_DIR to a temporary directory for isolation."""
    targets_dir = tmp_path / "targets"
    targets_dir.mkdir()

    import portfotrack.path as path_mod
    import portfotrack.services.target_services as svc_mod
    import portfotrack.storage.json_store.target_store as store_mod

    monkeypatch.setattr(path_mod, "TARGETS_DIR", targets_dir)
    monkeypatch.setattr(svc_mod, "TARGETS_DIR", targets_dir)
    monkeypatch.setattr(store_mod, "TARGETS_DIR", targets_dir)

    return targets_dir


@pytest.fixture()
def client(tmp_data_dir):
    """Create a test client with isolated data directory."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


def _write_target_file(targets_dir: Path, date: str) -> None:
    """Write a minimal valid target JSON file."""
    dto = {
        "assets": [
            {
                "id": "us_equity",
                "name": "US Equity",
                "purpose": "growth",
                "target_ratio": 0.6,
                "tolerance": {"lower": 0.5, "upper": 0.7},
            },
        ]
    }
    file_name = f"target_{date}_v1.json"
    with open(targets_dir / file_name, "w", encoding="utf-8") as f:
        json.dump(dto, f, ensure_ascii=False, indent=2)


class TestGetTarget:
    """GET /api/targets — load latest target allocation."""

    def test_no_targets_returns_404(self, client):
        """When no target files exist, returns 404."""
        response = client.get("/api/targets")

        assert response.status_code == 404

    def test_existing_target_returns_200(self, client, tmp_data_dir):
        """Loading an existing target returns its data."""
        _write_target_file(tmp_data_dir, "2026-02-07")

        response = client.get("/api/targets")

        assert response.status_code == 200
        data = response.get_json()
        assert "assets" in data
        assert len(data["assets"]) == 1
        assert data["assets"][0]["id"] == "us_equity"


class TestCreateTarget:
    """POST /api/targets — create a new empty target."""

    def test_create_target_returns_201(self, client):
        """Creating a new target returns 201."""
        response = client.post("/api/targets")

        assert response.status_code == 201
        data = response.get_json()
        assert data == {"assets": []}

    def test_create_target_persists(self, client, tmp_data_dir):
        """Created target should be persisted as a JSON file."""
        client.post("/api/targets")

        files = list(tmp_data_dir.glob("target_*.json"))
        assert len(files) == 1


class TestAddAssetToTarget:
    """POST /api/targets/assets — add asset to current target."""

    def test_add_asset_returns_200(self, client, tmp_data_dir):
        """Adding a valid asset returns 200 with updated target."""
        _write_target_file(tmp_data_dir, "2026-02-07")

        payload = {
            "asset_id": "kr_bond",
            "asset_name": "KR Bond",
            "purpose": "stability",
            "target_ratio": 0.3,
            "lower": 0.2,
            "upper": 0.4,
        }
        response = client.post(
            "/api/targets/assets",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["assets"]) == 2

    def test_add_asset_no_target_returns_404(self, client):
        """Adding asset when no target exists returns 404."""
        payload = {
            "asset_id": "kr_bond",
            "asset_name": "KR Bond",
            "purpose": "stability",
            "target_ratio": 0.3,
            "lower": 0.2,
            "upper": 0.4,
        }
        response = client.post(
            "/api/targets/assets",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_add_asset_missing_fields_returns_400(self, client, tmp_data_dir):
        """Adding asset with missing fields returns 400."""
        _write_target_file(tmp_data_dir, "2026-02-07")

        payload = {"asset_id": "kr_bond"}
        response = client.post(
            "/api/targets/assets",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_add_duplicate_asset_returns_409(self, client, tmp_data_dir):
        """Adding a duplicate asset_id returns 409 conflict."""
        _write_target_file(tmp_data_dir, "2026-02-07")

        payload = {
            "asset_id": "us_equity",
            "asset_name": "US Equity",
            "purpose": "growth",
            "target_ratio": 0.5,
            "lower": 0.4,
            "upper": 0.6,
        }
        response = client.post(
            "/api/targets/assets",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 409

    def test_add_asset_invalid_ratio_returns_400(self, client, tmp_data_dir):
        """Adding asset with ratio > 1.0 returns 400."""
        _write_target_file(tmp_data_dir, "2026-02-07")

        payload = {
            "asset_id": "kr_bond",
            "asset_name": "KR Bond",
            "purpose": "stability",
            "target_ratio": 1.5,
            "lower": 0.2,
            "upper": 0.4,
        }
        response = client.post(
            "/api/targets/assets",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400


class TestGetTargetAssets:
    """GET /api/targets/assets — list asset ids from latest target."""

    def test_returns_asset_list_when_target_exists(self, client, tmp_data_dir):
        """When a target exists, returns list of assets."""
        _write_target_file(tmp_data_dir, "2026-02-07")

        response = client.get("/api/targets/assets")

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "us_equity"
        assert data[0]["name"] == "US Equity"
        assert data[0]["purpose"] == "growth"

    def test_returns_404_when_no_target_exists(self, client):
        """When no target files exist, returns 404."""
        response = client.get("/api/targets/assets")

        assert response.status_code == 404
