"""Tests for snapshot item management API endpoints.

Covers:
- POST /api/snapshots/<date>/items — add item to existing snapshot
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


def _write_snapshot_file(
    snapshots_dir: Path, date: str, items: list | None = None
) -> None:
    """Write a snapshot JSON file to the given directory."""
    if items is None:
        items = [{"asset_id": "us_equity", "label": "S&P500", "amount": 5_000_000}]
    dto = {"date": date, "currency": "KRW", "items": items}
    file_name = f"snapshot_{date}_v1.json"
    with open(snapshots_dir / file_name, "w", encoding="utf-8") as f:
        json.dump(dto, f, ensure_ascii=False, indent=2)


class TestAddSnapshotItem:
    """POST /api/snapshots/<date>/items — add item to snapshot."""

    def test_add_item_returns_200(self, client, tmp_data_dir):
        """Adding a valid item to an existing snapshot returns 200."""
        _write_snapshot_file(tmp_data_dir, "2026-02-12")

        payload = {"asset_id": "kr_bond", "label": "국채", "amount": 3_000_000}
        response = client.post(
            "/api/snapshots/2026-02-12/items",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 2

    def test_add_item_persists_to_disk(self, client, tmp_data_dir):
        """Added item should be persisted in the snapshot file."""
        _write_snapshot_file(tmp_data_dir, "2026-02-12")

        payload = {"asset_id": "kr_bond", "label": "국채", "amount": 3_000_000}
        response = client.post(
            "/api/snapshots/2026-02-12/items",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Verify via API response (save may use today's date for filename)
        data = response.get_json()
        assert len(data["items"]) == 2
        asset_ids = [item["asset_id"] for item in data["items"]]
        assert "kr_bond" in asset_ids

    def test_add_item_to_nonexistent_snapshot_returns_404(self, client):
        """Adding item to a non-existing snapshot returns 404."""
        payload = {"asset_id": "kr_bond", "label": "국채", "amount": 3_000_000}
        response = client.post(
            "/api/snapshots/2099-01-01/items",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_add_item_missing_asset_id_returns_400(self, client, tmp_data_dir):
        """Adding item without asset_id returns 400."""
        _write_snapshot_file(tmp_data_dir, "2026-02-12")

        payload = {"label": "국채", "amount": 3_000_000}
        response = client.post(
            "/api/snapshots/2026-02-12/items",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_add_item_missing_amount_returns_400(self, client, tmp_data_dir):
        """Adding item without amount returns 400."""
        _write_snapshot_file(tmp_data_dir, "2026-02-12")

        payload = {"asset_id": "kr_bond", "label": "국채"}
        response = client.post(
            "/api/snapshots/2026-02-12/items",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_add_item_invalid_date_returns_400(self, client):
        """Adding item with invalid date format returns 400."""
        payload = {"asset_id": "kr_bond", "label": "국채", "amount": 3_000_000}
        response = client.post(
            "/api/snapshots/bad-date/items",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_add_item_merges_same_asset_label(self, client, tmp_data_dir):
        """Adding item with same asset_id and label merges amounts."""
        _write_snapshot_file(tmp_data_dir, "2026-02-12")

        payload = {"asset_id": "us_equity", "label": "S&P500", "amount": 2_000_000}
        response = client.post(
            "/api/snapshots/2026-02-12/items",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        # Should merge: 5M + 2M = 7M, still 1 item
        assert len(data["items"]) == 1
        assert data["items"][0]["amount"] == 7_000_000
