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
    check_cap_breaches_with_snapshot,
    init_optional_bet_snapshot,
    load_all_optional_bets,
    load_latest_optional_bet,
    load_optional_bet_by_filename,
    remove_item,
    save_optional_bet,
    save_optional_bet_overwrite,
    update_item,
)
from portfotrack.storage.json_store.errors import (
    OptionalBetNotFoundError,
    SnapshotNotFoundError,
)


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
# update_item
# ---------------------------------------------------------------------------


class TestUpdateItem:
    """Tests for update_item service function."""

    def test_updates_name_and_returns_same_instance(self) -> None:
        """Partial update of name only keeps other fields unchanged."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        result = update_item(snapshot, "bitcoin", name="BTC")

        assert result is snapshot
        assert snapshot.items[0].name == "BTC"
        assert snapshot.items[0].cap_ratio == 0.05
        assert snapshot.items[0].amount == 1_000_000

    def test_updates_cap_ratio_and_amount(self) -> None:
        """Multiple fields can be updated at once."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        update_item(snapshot, "bitcoin", cap_ratio=0.10, amount=2_000_000)

        assert snapshot.items[0].cap_ratio == 0.10
        assert snapshot.items[0].amount == 2_000_000

    def test_nonexistent_asset_raises_error(self) -> None:
        """Updating a non-existent asset_id raises OptionalBetAssetNotFoundError."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        with pytest.raises(
            OptionalBetAssetNotFoundError,
            match=OptionalBetErrorCode.OPTIONAL_BET_ASSET_NOT_FOUND,
        ):
            update_item(snapshot, "ethereum", name="ETH")

    def test_invalid_cap_ratio_raises_error(self) -> None:
        """Updating with an invalid cap_ratio raises InvalidCapRatioError."""
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        with pytest.raises(
            InvalidCapRatioError,
            match=OptionalBetErrorCode.OPTIONAL_BET_INVALID_CAP_RATIO,
        ):
            update_item(snapshot, "bitcoin", cap_ratio=1.5)


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


# ---------------------------------------------------------------------------
# check_cap_breaches_with_snapshot
# ---------------------------------------------------------------------------


@pytest.fixture()
def _snapshot_and_bet_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    """Set up isolated directories for both snapshots and optional bets."""
    import portfotrack.services.optional_bet_services as ob_svc_mod
    import portfotrack.services.snapshot_services as snap_svc_mod
    import portfotrack.storage.json_store.optional_bet_store as ob_store_mod
    import portfotrack.storage.json_store.snapshot_store as snap_store_mod

    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    ob_dir = tmp_path / "optional_bets"
    ob_dir.mkdir()

    monkeypatch.setattr(snap_svc_mod, "SNAPSHOTS_DIR", snap_dir)
    monkeypatch.setattr(snap_store_mod, "SNAPSHOTS_DIR", snap_dir)
    monkeypatch.setattr(ob_svc_mod, "OPTIONAL_BETS_DIR", ob_dir)
    monkeypatch.setattr(ob_store_mod, "OPTIONAL_BETS_DIR", ob_dir)

    return snap_dir, ob_dir


def _write_snapshot_file(snap_dir: Path, date: str, items: list) -> str:
    """Write a snapshot JSON file and return its filename."""
    file_name = f"snapshot_{date}_v1.json"
    (snap_dir / file_name).write_text(
        json.dumps(
            {"date": date, "currency": "KRW", "items": items},
            ensure_ascii=False,
        )
    )
    return file_name


def _write_ob_file(ob_dir: Path, date: str, items: list) -> str:
    """Write an optional bet JSON file and return its filename."""
    file_name = f"optional_bet_{date}_v1.json"
    (ob_dir / file_name).write_text(
        json.dumps(
            {"date": date, "currency": "KRW", "items": items},
            ensure_ascii=False,
        )
    )
    return file_name


class TestCheckCapBreachesWithSnapshot:
    """Tests for check_cap_breaches_with_snapshot service function."""

    def test_uses_latest_snapshot_by_default(
        self, _snapshot_and_bet_dirs: tuple[Path, Path]
    ) -> None:
        """When no filename given, uses latest snapshot total for breach check."""
        snap_dir, ob_dir = _snapshot_and_bet_dirs
        _write_snapshot_file(
            snap_dir,
            "2026-02-27",
            [
                {"asset_id": "US_EQUITY", "label": "S&P500", "amount": 50_000_000},
                {"asset_id": "KR_BOND", "label": "Treasury", "amount": 50_000_000},
            ],
        )
        _write_ob_file(
            ob_dir,
            "2026-03-01",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 1_000_000,
                }
            ],
        )

        result = check_cap_breaches_with_snapshot()

        assert result["snapshot_date"] == "2026-02-27"
        assert result["main_portfolio_total"] == 100_000_000
        assert result["breaches"] == []

    def test_uses_specified_snapshot_file(
        self, _snapshot_and_bet_dirs: tuple[Path, Path]
    ) -> None:
        """When a filename is given, uses that snapshot's total."""
        snap_dir, ob_dir = _snapshot_and_bet_dirs
        _write_snapshot_file(
            snap_dir,
            "2026-02-14",
            [{"asset_id": "US_EQUITY", "label": "S&P500", "amount": 80_000_000}],
        )
        _write_snapshot_file(
            snap_dir,
            "2026-02-27",
            [{"asset_id": "US_EQUITY", "label": "S&P500", "amount": 200_000_000}],
        )
        _write_ob_file(
            ob_dir,
            "2026-03-01",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 10_000_000,
                }
            ],
        )

        result = check_cap_breaches_with_snapshot(
            snapshot_filename="snapshot_2026-02-14_v1.json"
        )

        assert result["snapshot_date"] == "2026-02-14"
        assert result["main_portfolio_total"] == 80_000_000
        # 10M / (80M + 10M) ≈ 0.111 > 0.05 → breach
        assert len(result["breaches"]) == 1
        assert result["breaches"][0].asset_id == "bitcoin"

    def test_no_snapshot_raises_error(
        self, _snapshot_and_bet_dirs: tuple[Path, Path]
    ) -> None:
        """When no snapshot files exist, raises SnapshotNotFoundError."""
        _, ob_dir = _snapshot_and_bet_dirs
        _write_ob_file(
            ob_dir,
            "2026-03-01",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 1_000_000,
                }
            ],
        )

        with pytest.raises(SnapshotNotFoundError):
            check_cap_breaches_with_snapshot()

    def test_no_optional_bet_raises_error(
        self, _snapshot_and_bet_dirs: tuple[Path, Path]
    ) -> None:
        """When no optional bet files exist, raises OptionalBetNotFoundError."""
        snap_dir, _ = _snapshot_and_bet_dirs
        _write_snapshot_file(
            snap_dir,
            "2026-02-27",
            [{"asset_id": "US_EQUITY", "label": "S&P500", "amount": 100_000_000}],
        )

        with pytest.raises(OptionalBetNotFoundError):
            check_cap_breaches_with_snapshot()

    def test_breach_detected_with_snapshot(
        self, _snapshot_and_bet_dirs: tuple[Path, Path]
    ) -> None:
        """Detects breach when optional bet exceeds cap relative to snapshot total."""
        snap_dir, ob_dir = _snapshot_and_bet_dirs
        _write_snapshot_file(
            snap_dir,
            "2026-02-27",
            [{"asset_id": "US_EQUITY", "label": "S&P500", "amount": 100_000_000}],
        )
        _write_ob_file(
            ob_dir,
            "2026-03-01",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 10_000_000,
                }
            ],
        )

        result = check_cap_breaches_with_snapshot()

        # 10M / (100M + 10M) ≈ 0.0909 > 0.05 → breach
        assert len(result["breaches"]) == 1
        assert result["breaches"][0].asset_id == "bitcoin"
        assert result["main_portfolio_total"] == 100_000_000

    def test_no_breach_returns_empty_list(
        self, _snapshot_and_bet_dirs: tuple[Path, Path]
    ) -> None:
        """When no items breach cap, returns empty breaches list."""
        snap_dir, ob_dir = _snapshot_and_bet_dirs
        _write_snapshot_file(
            snap_dir,
            "2026-02-27",
            [{"asset_id": "US_EQUITY", "label": "S&P500", "amount": 100_000_000}],
        )
        _write_ob_file(
            ob_dir,
            "2026-03-01",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 1_000_000,
                }
            ],
        )

        result = check_cap_breaches_with_snapshot()

        assert result["breaches"] == []


# ---------------------------------------------------------------------------
# load_all_optional_bets
# ---------------------------------------------------------------------------


class TestLoadAllOptionalBets:
    """Tests for load_all_optional_bets function."""

    def test_empty_directory_returns_empty_list(self, optional_bets_path: Path) -> None:
        """No optional bet files yields an empty list."""
        result = load_all_optional_bets()

        assert result == []

    def test_single_file_returns_one_item(self, optional_bets_path: Path) -> None:
        """One optional bet file yields a list with one OptionalBetSnapshot."""
        _write_ob_file(
            optional_bets_path,
            "2026-03-01",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 1_000_000,
                }
            ],
        )

        result = load_all_optional_bets()

        assert len(result) == 1
        assert isinstance(result[0], OptionalBetSnapshot)
        assert result[0].date == "2026-03-01"

    def test_multiple_files_sorted_ascending_by_date(
        self, optional_bets_path: Path
    ) -> None:
        """Multiple files are returned sorted by date ascending."""
        _write_ob_file(
            optional_bets_path,
            "2026-03-02",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 1_200_000,
                }
            ],
        )
        _write_ob_file(
            optional_bets_path,
            "2026-03-01",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 1_000_000,
                }
            ],
        )
        _write_ob_file(
            optional_bets_path,
            "2026-02-28",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 800_000,
                }
            ],
        )

        result = load_all_optional_bets()

        assert len(result) == 3
        assert result[0].date == "2026-02-28"
        assert result[1].date == "2026-03-01"
        assert result[2].date == "2026-03-02"

    def test_items_are_preserved(self, optional_bets_path: Path) -> None:
        """Loaded optional bet snapshots contain correct items."""
        _write_ob_file(
            optional_bets_path,
            "2026-03-01",
            [
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

        result = load_all_optional_bets()

        assert len(result) == 1
        assert len(result[0].items) == 2
        assert result[0].items[0].asset_id == "bitcoin"
        assert result[0].items[1].asset_id == "ethereum"


# ---------------------------------------------------------------------------
# load_optional_bet_by_filename
# ---------------------------------------------------------------------------


class TestLoadOptionalBetByFilename:
    """Tests for load_optional_bet_by_filename function."""

    def test_loads_specific_file(self, optional_bets_path: Path) -> None:
        """Loading by filename returns the correct snapshot."""
        _write_ob_file(
            optional_bets_path,
            "2026-02-28",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 800_000,
                }
            ],
        )
        _write_ob_file(
            optional_bets_path,
            "2026-03-01",
            [
                {
                    "asset_id": "bitcoin",
                    "name": "Bitcoin",
                    "cap_ratio": 0.05,
                    "amount": 1_000_000,
                }
            ],
        )

        result = load_optional_bet_by_filename("optional_bet_2026-02-28_v1.json")

        assert result.date == "2026-02-28"
        assert len(result.items) == 1
        assert result.items[0].amount == 800_000

    def test_nonexistent_file_raises_error(self, optional_bets_path: Path) -> None:
        """Loading a non-existent file raises OptionalBetNotFoundError."""
        with pytest.raises(OptionalBetNotFoundError):
            load_optional_bet_by_filename("optional_bet_9999-12-31_v1.json")
