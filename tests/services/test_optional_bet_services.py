import json
from pathlib import Path

import pytest

from portfotrack.domain.optional_bet import (
    CapBreachResult,
    OptionalBetSnapshot,
)
from portfotrack.domain.optional_bet.error_codes import OptionalBetErrorCode
from portfotrack.domain.optional_bet.errors import (
    DuplicateOptionalBetError,
    InvalidCapRatioError,
    OptionalBetAssetNotFoundError,
)
from portfotrack.services.optional_bet_services import (
    add_item,
    check_cap_breaches,
    init_optional_bet_snapshot,
    load_latest_optional_bet,
    remove_item,
    save_optional_bet,
    save_optional_bet_overwrite,
)
from portfotrack.storage.json_store.errors import OptionalBetNotFoundError


@pytest.fixture()
def optional_bets_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    import portfotrack.storage.json_store.optional_bet_store as store_mod

    d = tmp_path / "optional_bets"
    monkeypatch.setattr(store_mod, "OPTIONAL_BETS_DIR", d, raising=True)
    return d


@pytest.fixture()
def optional_bets_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Monkeypatch OPTIONAL_BETS_DIR for load_latest tests."""
    import portfotrack.services.optional_bet_services as svc_mod

    d = tmp_path / "optional_bets"
    d.mkdir()
    monkeypatch.setattr(svc_mod, "OPTIONAL_BETS_DIR", d, raising=True)

    import portfotrack.storage.json_store.optional_bet_store as store_mod

    monkeypatch.setattr(store_mod, "OPTIONAL_BETS_DIR", d, raising=True)
    return d


# ---------------------------------------------------------------------------
# init_optional_bet_snapshot
# ---------------------------------------------------------------------------


class TestInitOptionalBetSnapshot:
    """Tests for init_optional_bet_snapshot."""

    def test_returns_empty_snapshot(self) -> None:
        snapshot = init_optional_bet_snapshot()

        assert isinstance(snapshot, OptionalBetSnapshot)
        assert snapshot.items == []
        assert snapshot.currency == "KRW"


# ---------------------------------------------------------------------------
# add_item
# ---------------------------------------------------------------------------


class TestAddItem:
    """Tests for add_item service function."""

    def test_adds_item_and_returns_same_instance(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        result = add_item(snapshot, "bitcoin", "Bitcoin", 0.05, 1_000_000)

        assert result is snapshot
        assert len(snapshot.items) == 1
        assert snapshot.items[0].asset_id == "bitcoin"

    def test_duplicate_raises_error(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        add_item(snapshot, "bitcoin", "Bitcoin", 0.05, 1_000_000)

        with pytest.raises(
            DuplicateOptionalBetError,
            match=OptionalBetErrorCode.OPTIONAL_BET_DUPLICATE_ASSET,
        ):
            add_item(snapshot, "bitcoin", "BTC", 0.03, 500_000)

    def test_invalid_cap_ratio_raises_error(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        with pytest.raises(
            InvalidCapRatioError,
            match=OptionalBetErrorCode.OPTIONAL_BET_INVALID_CAP_RATIO,
        ):
            add_item(snapshot, "bitcoin", "Bitcoin", 0.0, 1_000_000)


# ---------------------------------------------------------------------------
# remove_item
# ---------------------------------------------------------------------------


class TestRemoveItem:
    """Tests for remove_item service function."""

    def test_removes_item_and_returns_same_instance(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        result = remove_item(snapshot, "bitcoin")

        assert result is snapshot
        assert len(snapshot.items) == 0

    def test_remove_nonexistent_raises_error(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        with pytest.raises(
            OptionalBetAssetNotFoundError,
            match=OptionalBetErrorCode.OPTIONAL_BET_ASSET_NOT_FOUND,
        ):
            remove_item(snapshot, "ethereum")


# ---------------------------------------------------------------------------
# save_optional_bet
# ---------------------------------------------------------------------------


class TestSaveOptionalBet:
    """Tests for save_optional_bet function."""

    def test_saves_snapshot_to_file(self, optional_bets_dir: Path) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        save_optional_bet(snapshot)

        files = list(optional_bets_dir.glob("optional_bet_*_v*.json"))
        assert len(files) == 1

    def test_saves_empty_snapshot(self, optional_bets_dir: Path) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        save_optional_bet(snapshot)

        files = list(optional_bets_dir.glob("optional_bet_*.json"))
        assert len(files) == 1


# ---------------------------------------------------------------------------
# save_optional_bet_overwrite
# ---------------------------------------------------------------------------


class TestSaveOptionalBetOverwrite:
    """Tests for save_optional_bet_overwrite function."""

    def test_overwrites_specific_file(self, optional_bets_dir: Path) -> None:
        snapshot1 = OptionalBetSnapshot(date="2026-03-01")
        snapshot1.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
        file_name = "optional_bet_2026-03-01_v1.json"
        save_optional_bet_overwrite(snapshot1, file_name)

        snapshot2 = OptionalBetSnapshot(date="2026-03-01")
        snapshot2.add_item("bitcoin", "Bitcoin", 0.08, 2_000_000)
        save_optional_bet_overwrite(snapshot2, file_name)

        file_path = optional_bets_dir / file_name
        with open(file_path) as f:
            data = json.load(f)

        assert len(data["items"]) == 1
        assert data["items"][0]["amount"] == 2_000_000


# ---------------------------------------------------------------------------
# load_latest_optional_bet
# ---------------------------------------------------------------------------


class TestLoadLatestOptionalBet:
    """Tests for load_latest_optional_bet function."""

    def test_loads_most_recent_file(self, optional_bets_path: Path) -> None:
        older = {
            "date": "2026-02-28",
            "currency": "KRW",
            "items": [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 500_000,
                }
            ],
        }
        newer = {
            "date": "2026-03-01",
            "currency": "KRW",
            "items": [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 1_000_000,
                }
            ],
        }

        with open(optional_bets_path / "optional_bet_2026-02-28_v1.json", "w") as f:
            json.dump(older, f)
        with open(optional_bets_path / "optional_bet_2026-03-01_v1.json", "w") as f:
            json.dump(newer, f)

        snapshot = load_latest_optional_bet()

        assert snapshot.date == "2026-03-01"
        assert len(snapshot.items) == 1
        assert snapshot.items[0].amount == 1_000_000

    def test_no_files_raises_error(self, optional_bets_path: Path) -> None:
        with pytest.raises(OptionalBetNotFoundError):
            load_latest_optional_bet()


# ---------------------------------------------------------------------------
# check_cap_breaches
# ---------------------------------------------------------------------------


class TestCheckCapBreaches:
    """Tests for check_cap_breaches service function."""

    def test_no_breach(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        result = check_cap_breaches(snapshot, main_portfolio_total=100_000_000)

        assert result == []

    def test_breach_detected(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 10_000_000)

        result = check_cap_breaches(snapshot, main_portfolio_total=100_000_000)

        assert len(result) == 1
        assert isinstance(result[0], CapBreachResult)
        assert result[0].asset_id == "bitcoin"

    def test_empty_snapshot_returns_empty(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        result = check_cap_breaches(snapshot, main_portfolio_total=100_000_000)

        assert result == []
