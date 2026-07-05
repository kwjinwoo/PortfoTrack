"""Tests for optional bet API endpoints.

Covers:
- GET    /api/optional-bets              — list optional bet files
- GET    /api/optional-bets/latest       — load latest optional bet snapshot
- GET    /api/optional-bets/<date>       — load optional bet by date
- POST   /api/optional-bets              — create new snapshot
- POST   /api/optional-bets/items        — add item to latest snapshot
- DELETE /api/optional-bets/items/<id>   — remove item
- PATCH  /api/optional-bets/items/<id>   — update item
- PUT    /api/optional-bets/<date>       — update snapshot (overwrite/new)
- GET    /api/optional-bets/breaches     — check cap breaches
"""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect OPTIONAL_BETS_DIR and SNAPSHOTS_DIR to temporary directories."""
    ob_dir = tmp_path / "optional_bets"
    ob_dir.mkdir()
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()

    import portfotrack.path as path_mod
    import portfotrack.services.optional_bet_services as svc_mod
    import portfotrack.services.snapshot_services as snap_svc_mod
    import portfotrack.storage.json_store.optional_bet_store as store_mod
    import portfotrack.storage.json_store.snapshot_store as snap_store_mod

    monkeypatch.setattr(path_mod, "OPTIONAL_BETS_DIR", ob_dir)
    monkeypatch.setattr(svc_mod, "OPTIONAL_BETS_DIR", ob_dir)
    monkeypatch.setattr(store_mod, "OPTIONAL_BETS_DIR", ob_dir)
    monkeypatch.setattr(snap_svc_mod, "SNAPSHOTS_DIR", snap_dir)
    monkeypatch.setattr(snap_store_mod, "SNAPSHOTS_DIR", snap_dir)

    return ob_dir


@pytest.fixture()
def client(tmp_data_dir):
    """Create a test client with isolated data directory."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


def _write_optional_bet_file(
    ob_dir: Path,
    date: str,
    items: list | None = None,
) -> None:
    """Write a minimal valid optional bet JSON file."""
    dto = {
        "date": date,
        "currency": "KRW",
        "items": items
        or [
            {
                "asset_id": "bitcoin",
                "name": "Bitcoin",
                "cap_ratio": 0.05,
                "amount": 1_000_000,
            }
        ],
    }
    file_name = f"optional_bet_{date}_v1.json"
    with open(ob_dir / file_name, "w", encoding="utf-8") as f:
        json.dump(dto, f, ensure_ascii=False, indent=2)


def _write_snapshot_file(
    tmp_path: Path,
    date: str,
    items: list | None = None,
) -> str:
    """Write a minimal valid snapshot JSON file and return its filename."""
    snap_dir = tmp_path / "snapshots"
    dto = {
        "date": date,
        "currency": "KRW",
        "items": items
        or [{"asset_id": "US_EQUITY", "label": "S&P500", "amount": 100_000_000}],
    }
    file_name = f"snapshot_{date}_v1.json"
    with open(snap_dir / file_name, "w", encoding="utf-8") as f:
        json.dump(dto, f, ensure_ascii=False, indent=2)
    return file_name


# ---------------------------------------------------------------------------
# GET /api/optional-bets — list files
# ---------------------------------------------------------------------------


class TestListOptionalBets:
    """GET /api/optional-bets — list optional bet files."""

    def test_empty_returns_empty_list(self, client):
        """When no optional bet files exist, returns an empty array."""
        response = client.get("/api/optional-bets")

        assert response.status_code == 200
        assert response.get_json() == []

    def test_returns_files_sorted_by_date(self, client, tmp_data_dir):
        """Returns date and filename for each file, sorted ascending."""
        _write_optional_bet_file(tmp_data_dir, "2026-02-28")
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.get("/api/optional-bets")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert data[0]["date"] == "2026-02-28"
        assert data[1]["date"] == "2026-03-01"
        assert "filename" in data[0]


# ---------------------------------------------------------------------------
# GET /api/optional-bets/latest — load latest
# ---------------------------------------------------------------------------


class TestGetLatestOptionalBet:
    """GET /api/optional-bets/latest — load latest optional bet snapshot."""

    def test_no_files_returns_404(self, client):
        """When no optional bet files exist, returns 404."""
        response = client.get("/api/optional-bets/latest")

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_returns_latest_snapshot(self, client, tmp_data_dir):
        """Returns the most recent optional bet snapshot."""
        _write_optional_bet_file(tmp_data_dir, "2026-02-28")
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-01",
            items=[
                {
                    "asset_id": "ethereum",
                    "name": "Ethereum",
                    "cap_ratio": 0.03,
                    "amount": 500_000,
                }
            ],
        )

        response = client.get("/api/optional-bets/latest")

        assert response.status_code == 200
        data = response.get_json()
        assert data["date"] == "2026-03-01"
        assert len(data["items"]) == 1
        assert data["items"][0]["asset_id"] == "ethereum"


# ---------------------------------------------------------------------------
# POST /api/optional-bets — create new snapshot
# ---------------------------------------------------------------------------


class TestCreateOptionalBet:
    """POST /api/optional-bets — create a new optional bet snapshot."""

    def test_no_body_returns_400(self, client):
        """Missing request body returns 400."""
        response = client.post("/api/optional-bets", content_type="application/json")

        assert response.status_code == 400

    def test_create_empty_snapshot_returns_201(self, client):
        """Creating with empty items list produces an empty snapshot."""
        response = client.post(
            "/api/optional-bets",
            json={"items": []},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["items"] == []
        assert data["currency"] == "KRW"

    def test_create_with_items_returns_201(self, client):
        """Creating with valid items returns the populated snapshot."""
        response = client.post(
            "/api/optional-bets",
            json={
                "items": [
                    {
                        "asset_id": "bitcoin",
                        "name": "Bitcoin",
                        "cap_ratio": 0.05,
                        "amount": 1_000_000,
                    }
                ]
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert len(data["items"]) == 1
        assert data["items"][0]["asset_id"] == "bitcoin"

    def test_invalid_item_fields_returns_400(self, client):
        """Items with missing or invalid fields return 400."""
        response = client.post(
            "/api/optional-bets",
            json={"items": [{"asset_id": "bitcoin"}]},
        )

        assert response.status_code == 400

    def test_duplicate_asset_id_returns_409(self, client):
        """Duplicate asset_id within items returns 409."""
        response = client.post(
            "/api/optional-bets",
            json={
                "items": [
                    {
                        "asset_id": "bitcoin",
                        "name": "Bitcoin",
                        "cap_ratio": 0.05,
                        "amount": 1_000_000,
                    },
                    {
                        "asset_id": "bitcoin",
                        "name": "BTC",
                        "cap_ratio": 0.03,
                        "amount": 500_000,
                    },
                ]
            },
        )

        assert response.status_code == 409

    def test_invalid_cap_ratio_returns_400(self, client):
        """Invalid cap_ratio returns 400."""
        response = client.post(
            "/api/optional-bets",
            json={
                "items": [
                    {
                        "asset_id": "bitcoin",
                        "name": "Bitcoin",
                        "cap_ratio": 1.5,
                        "amount": 1_000_000,
                    }
                ]
            },
        )

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/optional-bets/items — add item
# ---------------------------------------------------------------------------


class TestAddItemRoute:
    """POST /api/optional-bets/items — add item to latest snapshot."""

    def test_no_snapshot_returns_404(self, client):
        """When no snapshot exists, returns 404."""
        response = client.post(
            "/api/optional-bets/items",
            json={
                "asset_id": "bitcoin",
                "name": "Bitcoin",
                "cap_ratio": 0.05,
                "amount": 1_000_000,
            },
        )

        assert response.status_code == 404

    def test_adds_item_returns_200(self, client, tmp_data_dir):
        """Successfully adding an item returns 200 with updated snapshot."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.post(
            "/api/optional-bets/items",
            json={
                "asset_id": "ethereum",
                "name": "Ethereum",
                "cap_ratio": 0.03,
                "amount": 500_000,
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 2

    def test_duplicate_returns_409(self, client, tmp_data_dir):
        """Adding an item with duplicate asset_id returns 409."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.post(
            "/api/optional-bets/items",
            json={
                "asset_id": "bitcoin",
                "name": "BTC",
                "cap_ratio": 0.03,
                "amount": 500_000,
            },
        )

        assert response.status_code == 409

    def test_missing_fields_returns_400(self, client, tmp_data_dir):
        """Missing required fields returns 400."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.post(
            "/api/optional-bets/items",
            json={"asset_id": "ethereum"},
        )

        assert response.status_code == 400

    def test_no_body_returns_400(self, client, tmp_data_dir):
        """Missing request body returns 400."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.post(
            "/api/optional-bets/items",
            content_type="application/json",
        )

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /api/optional-bets/items/<asset_id> — remove item
# ---------------------------------------------------------------------------


class TestRemoveItemRoute:
    """DELETE /api/optional-bets/items/<asset_id> — remove item."""

    def test_no_snapshot_returns_404(self, client):
        """When no snapshot exists, returns 404."""
        response = client.delete("/api/optional-bets/items/bitcoin")

        assert response.status_code == 404

    def test_removes_item_returns_200(self, client, tmp_data_dir):
        """Successfully removing an item returns 200."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.delete("/api/optional-bets/items/bitcoin")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 0

    def test_nonexistent_asset_returns_404(self, client, tmp_data_dir):
        """Removing a non-existent asset returns 404."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.delete("/api/optional-bets/items/ethereum")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/optional-bets/items/<asset_id> — update item
# ---------------------------------------------------------------------------


class TestUpdateItemRoute:
    """PATCH /api/optional-bets/items/<asset_id> — update item fields."""

    def test_no_snapshot_returns_404(self, client):
        """When no snapshot exists, returns 404."""
        response = client.patch(
            "/api/optional-bets/items/bitcoin",
            json={"name": "BTC"},
        )

        assert response.status_code == 404

    def test_updates_name_returns_200(self, client, tmp_data_dir):
        """Partial update of name returns 200."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.patch(
            "/api/optional-bets/items/bitcoin",
            json={"name": "BTC"},
        )

        assert response.status_code == 200
        data = response.get_json()
        updated = [i for i in data["items"] if i["asset_id"] == "bitcoin"][0]
        assert updated["name"] == "BTC"
        assert updated["cap_ratio"] == 0.05

    def test_nonexistent_asset_returns_404(self, client, tmp_data_dir):
        """Updating a non-existent asset returns 404."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.patch(
            "/api/optional-bets/items/ethereum",
            json={"name": "ETH"},
        )

        assert response.status_code == 404

    def test_invalid_cap_ratio_returns_400(self, client, tmp_data_dir):
        """Updating with invalid cap_ratio returns 400."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.patch(
            "/api/optional-bets/items/bitcoin",
            json={"cap_ratio": 1.5},
        )

        assert response.status_code == 400

    def test_no_body_returns_400(self, client, tmp_data_dir):
        """Missing request body returns 400."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.patch(
            "/api/optional-bets/items/bitcoin",
            content_type="application/json",
        )

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# PUT /api/optional-bets/<date> — update snapshot
# ---------------------------------------------------------------------------


class TestUpdateOptionalBet:
    """PUT /api/optional-bets/<date> — update snapshot."""

    def test_invalid_date_format_returns_400(self, client):
        """Invalid date format returns 400."""
        response = client.put(
            "/api/optional-bets/not-a-date",
            json={"mode": "overwrite", "items": []},
        )

        assert response.status_code == 400

    def test_no_body_returns_400(self, client):
        """Missing request body returns 400."""
        response = client.put(
            "/api/optional-bets/2026-03-01",
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_invalid_mode_returns_400(self, client):
        """Invalid mode value returns 400."""
        response = client.put(
            "/api/optional-bets/2026-03-01",
            json={"mode": "invalid", "items": []},
        )

        assert response.status_code == 400

    def test_missing_items_returns_400(self, client):
        """Missing items field returns 400."""
        response = client.put(
            "/api/optional-bets/2026-03-01",
            json={"mode": "overwrite"},
        )

        assert response.status_code == 400

    def test_nonexistent_date_returns_404(self, client):
        """Updating a non-existent date returns 404."""
        response = client.put(
            "/api/optional-bets/2026-03-01",
            json={
                "mode": "overwrite",
                "items": [
                    {
                        "asset_id": "bitcoin",
                        "name": "Bitcoin",
                        "cap_ratio": 0.05,
                        "amount": 1_000_000,
                    }
                ],
            },
        )

        assert response.status_code == 404

    def test_overwrite_mode_returns_200(self, client, tmp_data_dir):
        """Overwrite mode replaces the file and returns 200."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.put(
            "/api/optional-bets/2026-03-01",
            json={
                "mode": "overwrite",
                "items": [
                    {
                        "asset_id": "ethereum",
                        "name": "Ethereum",
                        "cap_ratio": 0.03,
                        "amount": 2_000_000,
                    }
                ],
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 1
        assert data["items"][0]["asset_id"] == "ethereum"

    def test_new_mode_returns_201(self, client, tmp_data_dir):
        """New mode saves as a new file and returns 201."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.put(
            "/api/optional-bets/2026-03-01",
            json={
                "mode": "new",
                "items": [
                    {
                        "asset_id": "ethereum",
                        "name": "Ethereum",
                        "cap_ratio": 0.03,
                        "amount": 2_000_000,
                    }
                ],
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert len(data["items"]) == 1

    def test_overwrite_empty_items_returns_200(self, client, tmp_data_dir):
        """Overwrite with empty items list returns 200."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.put(
            "/api/optional-bets/2026-03-01",
            json={"mode": "overwrite", "items": []},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["items"] == []

    def test_duplicate_asset_in_items_returns_409(self, client, tmp_data_dir):
        """Duplicate asset_id within items returns 409."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.put(
            "/api/optional-bets/2026-03-01",
            json={
                "mode": "overwrite",
                "items": [
                    {
                        "asset_id": "bitcoin",
                        "name": "Bitcoin",
                        "cap_ratio": 0.05,
                        "amount": 1_000_000,
                    },
                    {
                        "asset_id": "bitcoin",
                        "name": "BTC",
                        "cap_ratio": 0.03,
                        "amount": 500_000,
                    },
                ],
            },
        )

        assert response.status_code == 409


# ---------------------------------------------------------------------------
# GET /api/optional-bets/breaches — check cap breaches
# ---------------------------------------------------------------------------


class TestCheckBreaches:
    """GET /api/optional-bets/breaches — snapshot-based cap breach check."""

    def test_uses_latest_snapshot_by_default(self, client, tmp_data_dir, tmp_path):
        """Without snapshot param, uses latest snapshot total."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")
        _write_snapshot_file(tmp_path, "2026-02-27")

        response = client.get("/api/optional-bets/breaches")

        assert response.status_code == 200
        data = response.get_json()
        assert data["snapshot_date"] == "2026-02-27"
        assert data["main_portfolio_total"] == 100_000_000
        assert data["breaches"] == []

    def test_uses_specified_snapshot(self, client, tmp_data_dir, tmp_path):
        """With snapshot param, uses that specific snapshot."""
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-01",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 10_000_000,
                }
            ],
        )
        _write_snapshot_file(
            tmp_path,
            "2026-02-14",
            items=[{"asset_id": "US_EQUITY", "label": "S&P500", "amount": 80_000_000}],
        )
        _write_snapshot_file(tmp_path, "2026-02-27")

        response = client.get(
            "/api/optional-bets/breaches?snapshot=snapshot_2026-02-14_v1.json"
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["snapshot_date"] == "2026-02-14"
        assert data["main_portfolio_total"] == 80_000_000
        assert len(data["breaches"]) == 1
        assert data["breaches"][0]["asset_id"] == "bitcoin"

    def test_no_optional_bet_returns_404(self, client, tmp_data_dir, tmp_path):
        """When no optional bet snapshot exists, returns 404."""
        _write_snapshot_file(tmp_path, "2026-02-27")

        response = client.get("/api/optional-bets/breaches")

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_no_snapshot_returns_404(self, client, tmp_data_dir):
        """When no portfolio snapshot exists, returns 404."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.get("/api/optional-bets/breaches")

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_nonexistent_snapshot_file_returns_404(self, client, tmp_data_dir):
        """When specified snapshot file does not exist, returns 404."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.get(
            "/api/optional-bets/breaches?snapshot=snapshot_9999-12-31_v1.json"
        )

        assert response.status_code == 404

    def test_breach_detected(self, client, tmp_data_dir, tmp_path):
        """When an item exceeds its cap, returns breach details."""
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-01",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 10_000_000,
                }
            ],
        )
        _write_snapshot_file(tmp_path, "2026-02-27")

        response = client.get("/api/optional-bets/breaches")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["breaches"]) == 1
        assert data["breaches"][0]["asset_id"] == "bitcoin"
        assert "actual_ratio" in data["breaches"][0]
        assert "cap_ratio" in data["breaches"][0]

    def test_no_breaches_returns_empty(self, client, tmp_data_dir, tmp_path):
        """When no items breach their cap, returns empty list."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")
        _write_snapshot_file(tmp_path, "2026-02-27")

        response = client.get("/api/optional-bets/breaches")

        assert response.status_code == 200
        data = response.get_json()
        assert data["breaches"] == []


# ---------------------------------------------------------------------------
# GET /api/optional-bets/<date> — load by date
# ---------------------------------------------------------------------------


class TestGetOptionalBetByDate:
    """GET /api/optional-bets/<date> — load optional bet by date."""

    def test_returns_snapshot_for_valid_date(self, client, tmp_data_dir):
        """Valid date with existing file returns 200 with snapshot DTO."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.get("/api/optional-bets/2026-03-01")

        assert response.status_code == 200
        data = response.get_json()
        assert data["date"] == "2026-03-01"
        assert len(data["items"]) == 1
        assert data["items"][0]["asset_id"] == "bitcoin"

    def test_nonexistent_date_returns_404(self, client, tmp_data_dir):
        """Requesting a date with no file returns 404."""
        response = client.get("/api/optional-bets/2026-12-31")

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_invalid_date_format_returns_400(self, client, tmp_data_dir):
        """Invalid date format returns 400."""
        response = client.get("/api/optional-bets/not-a-date")

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_impossible_calendar_date_returns_400(self, client, tmp_data_dir):
        """A correctly shaped but nonexistent optional-bet date returns 400."""
        response = client.get("/api/optional-bets/2026-02-30")

        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid date format. Use YYYY-MM-DD."}

    def test_returns_correct_snapshot_among_multiple(self, client, tmp_data_dir):
        """Returns the correct snapshot when multiple dates exist."""
        _write_optional_bet_file(tmp_data_dir, "2026-02-28")
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-01",
            items=[
                {
                    "asset_id": "ethereum",
                    "name": "Ethereum",
                    "cap_ratio": 0.03,
                    "amount": 500_000,
                }
            ],
        )

        response = client.get("/api/optional-bets/2026-02-28")

        assert response.status_code == 200
        data = response.get_json()
        assert data["date"] == "2026-02-28"
        assert data["items"][0]["asset_id"] == "bitcoin"


# ---------------------------------------------------------------------------
# GET /api/optional-bets/trends/analysis — optional bet trend analysis
# ---------------------------------------------------------------------------


class TestOptionalBetTrendAnalysis:
    """GET /api/optional-bets/trends/analysis — trend analysis."""

    def test_returns_200_with_empty_data_when_no_files(self, client) -> None:
        """No optional bet files yields 200 with empty trend data."""
        response = client.get("/api/optional-bets/trends/analysis")

        assert response.status_code == 200
        data = response.get_json()
        assert data["asset_trends"] == []
        assert data["portfolio_trend"] == []
        assert data["metadata"]["snapshot_count"] == 0

    def test_returns_200_with_single_file(self, client, tmp_data_dir) -> None:
        """One optional bet file produces valid trend data."""
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-01",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 1_000_000,
                },
                {
                    "asset_id": "ethereum",
                    "name": "Ethereum",
                    "cap_ratio": 0.03,
                    "amount": 500_000,
                },
            ],
        )

        response = client.get("/api/optional-bets/trends/analysis")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["asset_trends"]) == 2
        assert len(data["portfolio_trend"]) == 1
        assert data["portfolio_trend"][0]["total_amount"] == 1_500_000
        assert data["metadata"]["snapshot_count"] == 1

    def test_returns_200_with_multiple_files(self, client, tmp_data_dir) -> None:
        """Multiple files produce chronological trend data."""
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-02-28",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 800_000,
                }
            ],
        )
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-01",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 1_000_000,
                }
            ],
        )

        response = client.get("/api/optional-bets/trends/analysis")

        assert response.status_code == 200
        data = response.get_json()
        assert data["metadata"]["snapshot_count"] == 2
        assert data["metadata"]["start_date"] == "2026-02-28"
        assert data["metadata"]["end_date"] == "2026-03-01"
        assert len(data["portfolio_trend"]) == 2

    def test_asset_trend_structure(self, client, tmp_data_dir) -> None:
        """Each asset trend contains asset_id, asset_name, and data_points."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.get("/api/optional-bets/trends/analysis")

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
        """Each portfolio trend point has date, total_amount, and change_pct."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-01")

        response = client.get("/api/optional-bets/trends/analysis")

        data = response.get_json()
        point = data["portfolio_trend"][0]
        assert "date" in point
        assert "total_amount" in point
        assert "change_pct" in point

    def test_portfolio_trend_change_pct_values(self, client, tmp_data_dir) -> None:
        """change_pct reflects percentage change from previous snapshot."""
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-02-28",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 10_000_000,
                }
            ],
        )
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-01",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 12_000_000,
                }
            ],
        )

        response = client.get("/api/optional-bets/trends/analysis")

        data = response.get_json()
        assert data["portfolio_trend"][0]["change_pct"] == pytest.approx(0.0)
        assert data["portfolio_trend"][1]["change_pct"] == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# POST /api/optional-bets/record-today — record today's amounts
# ---------------------------------------------------------------------------


class TestRecordToday:
    """POST /api/optional-bets/record-today — record amounts for today."""

    def test_no_snapshot_returns_404(self, client):
        """When no optional bet snapshot exists, returns 404."""
        response = client.post(
            "/api/optional-bets/record-today",
            json={"items": [{"asset_id": "bitcoin", "amount": 600_000}]},
        )

        assert response.status_code == 404

    def test_returns_200_with_updated_amounts(self, client, tmp_data_dir):
        """Successfully recording amounts returns 200 with new snapshot."""
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-12",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 500_000,
                },
                {
                    "asset_id": "ethereum",
                    "name": "Ethereum",
                    "cap_ratio": 0.03,
                    "amount": 300_000,
                },
            ],
        )

        response = client.post(
            "/api/optional-bets/record-today",
            json={
                "items": [
                    {"asset_id": "bitcoin", "amount": 600_000},
                    {"asset_id": "ethereum", "amount": 400_000},
                ]
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        amounts = {it["asset_id"]: it["amount"] for it in data["items"]}
        assert amounts["bitcoin"] == 600_000
        assert amounts["ethereum"] == 400_000

    def test_preserves_name_and_cap_ratio(self, client, tmp_data_dir):
        """Recorded snapshot preserves name and cap_ratio from latest."""
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-12",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 500_000,
                }
            ],
        )

        response = client.post(
            "/api/optional-bets/record-today",
            json={"items": [{"asset_id": "bitcoin", "amount": 700_000}]},
        )

        data = response.get_json()
        item = data["items"][0]
        assert item["name"] == "Bitcoin"
        assert item["cap_ratio"] == 0.05

    def test_invalid_json_returns_400(self, client, tmp_data_dir):
        """Non-JSON body returns 400."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-12")

        response = client.post(
            "/api/optional-bets/record-today",
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_missing_items_key_returns_400(self, client, tmp_data_dir):
        """Missing 'items' key returns 400."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-12")

        response = client.post(
            "/api/optional-bets/record-today",
            json={"amounts": []},
        )

        assert response.status_code == 400

    def test_unknown_asset_id_returns_400(self, client, tmp_data_dir):
        """An asset_id not in the latest snapshot returns 400."""
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-12",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 500_000,
                }
            ],
        )

        response = client.post(
            "/api/optional-bets/record-today",
            json={
                "items": [
                    {"asset_id": "bitcoin", "amount": 600_000},
                    {"asset_id": "unknown", "amount": 100_000},
                ]
            },
        )

        assert response.status_code == 400

    def test_missing_required_fields_returns_400(self, client, tmp_data_dir):
        """Item without asset_id or amount returns 400."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-12")

        response = client.post(
            "/api/optional-bets/record-today",
            json={"items": [{"asset_id": "bitcoin"}]},
        )

        assert response.status_code == 400

    def test_non_integer_amount_returns_400(self, client, tmp_data_dir):
        """Non-integer amount returns 400."""
        _write_optional_bet_file(tmp_data_dir, "2026-03-12")

        response = client.post(
            "/api/optional-bets/record-today",
            json={"items": [{"asset_id": "bitcoin", "amount": "not_a_number"}]},
        )

        assert response.status_code == 400

    def test_incomplete_items_returns_400(self, client, tmp_data_dir):
        """When not all assets from latest are included, returns 400."""
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-12",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 500_000,
                },
                {
                    "asset_id": "ethereum",
                    "name": "Ethereum",
                    "cap_ratio": 0.03,
                    "amount": 300_000,
                },
            ],
        )

        response = client.post(
            "/api/optional-bets/record-today",
            json={"items": [{"asset_id": "bitcoin", "amount": 600_000}]},
        )

        assert response.status_code == 400

    def test_saves_new_snapshot_file(self, client, tmp_data_dir):
        """Record-today creates a new file with today's date."""
        _write_optional_bet_file(
            tmp_data_dir,
            "2026-03-12",
            items=[
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 500_000,
                }
            ],
        )

        response = client.post(
            "/api/optional-bets/record-today",
            json={"items": [{"asset_id": "bitcoin", "amount": 700_000}]},
        )

        assert response.status_code == 200
        # A new file should have been saved (today's date)
        files = sorted(tmp_data_dir.glob("optional_bet_*.json"))
        assert len(files) >= 1
        # The latest file should contain the updated amount
        latest_file = files[-1]
        data = json.loads(latest_file.read_text())
        assert data["items"][0]["amount"] == 700_000
