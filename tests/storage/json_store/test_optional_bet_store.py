import json
import re
from pathlib import Path
from typing import Any

import pytest

import portfotrack.storage.json_store.optional_bet_store as store_mod
from portfotrack.storage.json_store.errors import OptionalBetNotFoundError
from portfotrack.storage.serialization.optional_bet_json import (
    OptionalBetSnapshotDTO,
)


@pytest.fixture()
def optional_bets_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    d = tmp_path / "optional_bets"
    monkeypatch.setattr(store_mod, "OPTIONAL_BETS_DIR", d, raising=True)
    return d


def _valid_dto() -> OptionalBetSnapshotDTO:
    return {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [
            {
                "asset_id": "bitcoin",
                "name": "Bitcoin",
                "cap_ratio": 0.05,
                "amount": 1_000_000,
            },
            {
                "asset_id": "solana",
                "name": "Solana",
                "cap_ratio": 0.03,
                "amount": 500_000,
            },
        ],
    }


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode="w", encoding="utf-8") as f:
        json.dump(obj, f)


def _read_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


def test_save_creates_dir_and_file(optional_bets_dir: Path) -> None:
    dto = _valid_dto()
    store_mod.save(dto)

    assert optional_bets_dir.exists() and optional_bets_dir.is_dir()

    files = sorted(optional_bets_dir.glob("optional_bet_*.json"))
    assert len(files) == 1

    v = store_mod.CURRENT_OPTIONAL_BET_SCHEMA_VERSION
    file = files[0]
    assert re.match(rf"^optional_bet_\d{{4}}-\d{{2}}-\d{{2}}_v{v}\.json$", file.name)

    assert _read_json(file) == dto


def test_save_overwrites_same_day(optional_bets_dir: Path) -> None:
    dto1 = _valid_dto()
    dto2 = _valid_dto()
    dto2["items"][0]["name"] = "Bitcoin (updated)"

    store_mod.save(dto1)
    files = sorted(optional_bets_dir.glob("optional_bet_*.json"))
    assert len(files) == 1
    assert _read_json(files[0]) == dto1

    file_name = files[0].name
    store_mod.save(dto2)
    overwritten_files = sorted(optional_bets_dir.glob("optional_bet_*.json"))
    assert len(overwritten_files) == 1
    assert overwritten_files[0].name == file_name
    assert _read_json(overwritten_files[0]) == dto2


# ---------------------------------------------------------------------------
# save_to_file
# ---------------------------------------------------------------------------


class TestSaveToFile:
    """Tests for save_to_file: persist to a specific filename."""

    def test_creates_file_with_given_name(self, optional_bets_dir: Path) -> None:
        dto = _valid_dto()
        store_mod.save_to_file(dto, "optional_bet_2026-03-01_v1.json")

        file_path = optional_bets_dir / "optional_bet_2026-03-01_v1.json"
        assert file_path.exists()
        assert _read_json(file_path) == dto

    def test_overwrites_existing(self, optional_bets_dir: Path) -> None:
        dto1 = _valid_dto()
        dto2 = _valid_dto()
        dto2["items"][0]["name"] = "Updated"

        store_mod.save_to_file(dto1, "optional_bet_2026-03-01_v1.json")
        store_mod.save_to_file(dto2, "optional_bet_2026-03-01_v1.json")

        file_path = optional_bets_dir / "optional_bet_2026-03-01_v1.json"
        assert _read_json(file_path) == dto2

    def test_creates_directory_if_missing(self, optional_bets_dir: Path) -> None:
        assert not optional_bets_dir.exists()

        dto = _valid_dto()
        store_mod.save_to_file(dto, "optional_bet_2026-03-01_v1.json")

        assert optional_bets_dir.exists()


# ---------------------------------------------------------------------------
# load — file not found
# ---------------------------------------------------------------------------


def test_load_missing_file_raises_not_found() -> None:
    with pytest.raises(OptionalBetNotFoundError):
        store_mod.load("does_not_exist.json")


# ---------------------------------------------------------------------------
# load — invariant violations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("invalid_data", [["invalid"], "invalid", 123, True, False])
def test_load_root_not_dict_raises_runtime_error(
    invalid_data: object, optional_bets_dir: Path
) -> None:
    file_path = optional_bets_dir / "invalid.json"
    _write_json(file_path, invalid_data)

    with pytest.raises(RuntimeError):
        store_mod.load(file_path.name)


@pytest.mark.parametrize("missing_key", ["date", "currency", "items"])
def test_load_missing_required_key_raises_runtime_error(
    missing_key: str, optional_bets_dir: Path
) -> None:
    dto: dict[str, Any] = dict(_valid_dto())
    del dto[missing_key]
    file_path = optional_bets_dir / "invalid.json"
    _write_json(file_path, dto)

    with pytest.raises(RuntimeError, match=f"'{missing_key}'"):
        store_mod.load(file_path.name)


@pytest.mark.parametrize(
    "invalid_items",
    [{"not": "a list"}, "invalid", 1, True, False],
)
def test_load_items_not_list_raises_type_error(
    invalid_items: object, optional_bets_dir: Path
) -> None:
    data = {"date": "2026-03-01", "currency": "KRW", "items": invalid_items}
    file_path = optional_bets_dir / "invalid.json"
    _write_json(file_path, data)

    with pytest.raises(TypeError):
        store_mod.load(file_path.name)


# ---------------------------------------------------------------------------
# load — happy path
# ---------------------------------------------------------------------------


def test_load_valid_dto_returns_dto(optional_bets_dir: Path) -> None:
    dto = _valid_dto()
    file_path = optional_bets_dir / "ok.json"
    _write_json(file_path, dto)

    result = store_mod.load(file_path.name)

    assert isinstance(result, dict)
    assert result["date"] == dto["date"]
    assert result["currency"] == dto["currency"]

    items = result["items"]
    assert isinstance(items, list)
    assert len(items) == 2

    for item, expected in zip(items, dto["items"], strict=True):
        assert item["asset_id"] == expected["asset_id"]
        assert item["name"] == expected["name"]
        assert item["cap_ratio"] == expected["cap_ratio"]
        assert item["amount"] == expected["amount"]


# ---------------------------------------------------------------------------
# Round-trip: save → load
# ---------------------------------------------------------------------------


def test_save_and_load_roundtrip(optional_bets_dir: Path) -> None:
    dto = _valid_dto()
    file_name = "optional_bet_2026-03-01_v1.json"
    store_mod.save_to_file(dto, file_name)

    result = store_mod.load(file_name)

    assert result == dto
