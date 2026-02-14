"""End-to-end workflow tests for PortfoTrack Web API.

Validates the full lifecycle:
    1. Create a snapshot with items
    2. Create a target allocation with assets
    3. Generate an allocation report comparing snapshot vs target
"""

import json

import pytest


@pytest.fixture()
def tmp_data_dirs(tmp_path, monkeypatch):
    """Redirect both SNAPSHOTS_DIR and TARGETS_DIR to temp directories."""
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()
    targets_dir = tmp_path / "targets"
    targets_dir.mkdir()

    import portfotrack.path as path_mod
    import portfotrack.services.snapshot_services as snap_svc
    import portfotrack.services.target_services as tgt_svc
    import portfotrack.storage.json_store.snapshot_store as snap_store
    import portfotrack.storage.json_store.target_store as tgt_store

    monkeypatch.setattr(path_mod, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(snap_svc, "SNAPSHOTS_DIR", snapshots_dir)
    monkeypatch.setattr(snap_store, "SNAPSHOTS_DIR", snapshots_dir)

    monkeypatch.setattr(path_mod, "TARGETS_DIR", targets_dir)
    monkeypatch.setattr(tgt_svc, "TARGETS_DIR", targets_dir)
    monkeypatch.setattr(tgt_store, "TARGETS_DIR", targets_dir)

    return {"snapshots": snapshots_dir, "targets": targets_dir}


@pytest.fixture()
def client(tmp_data_dirs):
    """Create a test client with fully isolated data directories."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


class TestFullWorkflow:
    """E2E: snapshot creation → target creation → report generation."""

    def test_complete_workflow(self, client):
        """Create snapshot, target, then verify report matches."""
        # --- Step 1: Create a snapshot ---
        snap_resp = client.post(
            "/api/snapshots",
            data=json.dumps(
                {
                    "items": [
                        {
                            "asset_id": "us_equity",
                            "label": "S&P500",
                            "amount": 5_000_000,
                        },
                        {"asset_id": "kr_bond", "label": "국채", "amount": 3_000_000},
                        {"asset_id": "gold", "label": "금", "amount": 2_000_000},
                    ],
                }
            ),
            content_type="application/json",
        )
        assert snap_resp.status_code == 201
        snapshot_date = snap_resp.get_json()["date"]

        # --- Step 2: Create a target allocation ---
        tgt_resp = client.post("/api/targets")
        assert tgt_resp.status_code == 201

        # Add assets to the target
        assets = [
            {
                "asset_id": "us_equity",
                "asset_name": "미국주식",
                "purpose": "growth",
                "target_ratio": 0.5,
                "lower": 0.45,
                "upper": 0.55,
            },
            {
                "asset_id": "kr_bond",
                "asset_name": "한국채권",
                "purpose": "stability",
                "target_ratio": 0.3,
                "lower": 0.25,
                "upper": 0.35,
            },
            {
                "asset_id": "gold",
                "asset_name": "금",
                "purpose": "hedge",
                "target_ratio": 0.2,
                "lower": 0.15,
                "upper": 0.25,
            },
        ]
        for asset in assets:
            add_resp = client.post(
                "/api/targets/assets",
                data=json.dumps(asset),
                content_type="application/json",
            )
            assert add_resp.status_code == 200

        # --- Step 3: Generate allocation report ---
        report_resp = client.get(
            f"/api/reports/allocation?snapshot_date={snapshot_date}"
        )
        assert report_resp.status_code == 200
        report = report_resp.get_json()

        # Verify report structure
        assert "items" in report
        assert "is_complete" in report
        assert "total_additional_needed" in report

        # Verify all three assets appear in report
        item_ids = [item["asset_id"] for item in report["items"]]
        assert "us_equity" in item_ids
        assert "kr_bond" in item_ids
        assert "gold" in item_ids

        # Total amount = 10,000,000
        # us_equity: 5M/10M = 50%, target 50% → within tolerance
        # kr_bond: 3M/10M = 30%, target 30% → within tolerance
        # gold: 2M/10M = 20%, target 20% → within tolerance
        assert report["is_complete"] is True

    def test_report_without_target_returns_404(self, client):
        """Report request without a saved target returns 404."""
        # Create a snapshot first
        snap_resp = client.post(
            "/api/snapshots",
            data=json.dumps(
                {
                    "items": [
                        {
                            "asset_id": "us_equity",
                            "label": "S&P500",
                            "amount": 1_000_000,
                        },
                    ],
                }
            ),
            content_type="application/json",
        )
        snapshot_date = snap_resp.get_json()["date"]

        report_resp = client.get(
            f"/api/reports/allocation?snapshot_date={snapshot_date}"
        )
        assert report_resp.status_code == 404

    def test_report_with_drift_detected(self, client):
        """Report detects drift when allocation is outside tolerance."""
        # Create a skewed snapshot
        snap_resp = client.post(
            "/api/snapshots",
            data=json.dumps(
                {
                    "items": [
                        {
                            "asset_id": "us_equity",
                            "label": "S&P500",
                            "amount": 8_000_000,
                        },
                        {"asset_id": "kr_bond", "label": "국채", "amount": 1_000_000},
                        {"asset_id": "gold", "label": "금", "amount": 1_000_000},
                    ],
                }
            ),
            content_type="application/json",
        )
        snapshot_date = snap_resp.get_json()["date"]

        # Create target: 50/30/20 split
        client.post("/api/targets")
        assets = [
            {
                "asset_id": "us_equity",
                "asset_name": "미국주식",
                "purpose": "growth",
                "target_ratio": 0.5,
                "lower": 0.45,
                "upper": 0.55,
            },
            {
                "asset_id": "kr_bond",
                "asset_name": "한국채권",
                "purpose": "stability",
                "target_ratio": 0.3,
                "lower": 0.25,
                "upper": 0.35,
            },
            {
                "asset_id": "gold",
                "asset_name": "금",
                "purpose": "hedge",
                "target_ratio": 0.2,
                "lower": 0.15,
                "upper": 0.25,
            },
        ]
        for asset in assets:
            client.post(
                "/api/targets/assets",
                data=json.dumps(asset),
                content_type="application/json",
            )

        report_resp = client.get(
            f"/api/reports/allocation?snapshot_date={snapshot_date}"
        )
        assert report_resp.status_code == 200
        report = report_resp.get_json()

        # us_equity: 8M/10M = 80%, target 50%, upper 55% → outside
        # kr_bond: 1M/10M = 10%, target 30%, lower 25% → outside
        # gold: 1M/10M = 10%, target 20%, lower 15% → outside
        assert report["is_complete"] is False

        # At least some items should need additional investment
        items_needing_more = [
            item for item in report["items"] if item["target_amount_needed"] > 0
        ]
        assert len(items_needing_more) > 0
