"""Tests for optional bet API endpoints.

Covers:
- GET  /api/optional-bets         — list optional bet files
- GET  /api/optional-bets/latest  — load latest optional bet snapshot
"""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect OPTIONAL_BETS_DIR to a temporary directory for isolation."""
    ob_dir = tmp_path / "optional_bets"
    ob_dir.mkdir()

    import portfotrack.path as path_mod
    import portfotrack.services.optional_bet_services as svc_mod
    import portfotrack.storage.json_store.optional_bet_store as store_mod

    monkeypatch.setattr(path_mod, "OPTIONAL_BETS_DIR", ob_dir)
    monkeypatch.setattr(svc_mod, "OPTIONAL_BETS_DIR", ob_dir)
    monkeypatch.setattr(store_mod, "OPTIONAL_BETS_DIR", ob_dir)

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
