import json
import re
from pathlib import Path
from typing import Any

import pytest

import portfotrack.storage.json_store.snapshot_store as store_mod
from portfotrack.storage.json_store.errors import SnapshotNotFoundError
from portfotrack.storage.serialization.snapshot_json import SnapshotDTO


@pytest.fixture()
def snapshots_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    d = tmp_path / "snapshots"
    monkeypatch.setattr(store_mod, "SNAPSHOTS_DIR", d, raising=True)
    return d


def _valid_snapshot_dto() -> SnapshotDTO:
    return {
        "date": "2026-02-11",
        "currency": "KRW",
        "items": [
            {"asset_id": "us_equity", "label": "S&P500", "amount": 5_000_000},
            {"asset_id": "kr_bond", "label": "Bond ETF", "amount": 3_000_000},
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


def test_save_creates_dir_and_file_and_writes_json(snapshots_dir: Path) -> None:
    dto = _valid_snapshot_dto()
    store_mod.save(dto)

    assert snapshots_dir.exists() and snapshots_dir.is_dir()

    files = sorted(snapshots_dir.glob("snapshot_*.json"))
    assert len(files) == 1

    v = store_mod.CURRENT_SNAPSHOT_SCHEMA_VERSION
    file = files[0]
    assert re.match(rf"^snapshot_\d{{4}}-\d{{2}}-\d{{2}}_v{v}\.json$", file.name)

    assert _read_json(file) == dto


def test_save_overwrites_same_day_same_version(snapshots_dir: Path) -> None:
    dto1 = _valid_snapshot_dto()
    dto2 = _valid_snapshot_dto()
    dto2["items"][0]["label"] = "S&P500 (updated)"

    store_mod.save(dto1)
    files = sorted(snapshots_dir.glob("snapshot_*.json"))
    assert len(files) == 1
    assert _read_json(files[0]) == dto1

    file_name = files[0].name
    store_mod.save(dto2)
    overwritten_files = sorted(snapshots_dir.glob("snapshot_*.json"))
    assert len(overwritten_files) == 1
    assert overwritten_files[0].name == file_name
    assert _read_json(overwritten_files[0]) == dto2


# ---------------------------------------------------------------------------
# load — file not found
# ---------------------------------------------------------------------------


def test_load_missing_file_raises_snapshot_not_found() -> None:
    with pytest.raises(SnapshotNotFoundError):
        store_mod.load("does_not_exist.json")


# ---------------------------------------------------------------------------
# load — invariant violations (programmer errors)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("invalid_data", [["invalid"], "invalid", 123, True, False])
def test_load_root_not_dict_raises_runtime_error(
    invalid_data: object, snapshots_dir: Path
) -> None:
    file_path = snapshots_dir / "invalid.json"
    _write_json(file_path, invalid_data)

    with pytest.raises(RuntimeError):
        store_mod.load(file_path.name)


@pytest.mark.parametrize("missing_key", ["date", "currency", "items"])
def test_load_missing_required_key_raises_runtime_error(
    missing_key: str, snapshots_dir: Path
) -> None:
    dto = _valid_snapshot_dto()
    del dto[missing_key]  # type: ignore[misc]
    file_path = snapshots_dir / "invalid.json"
    _write_json(file_path, dto)

    with pytest.raises(RuntimeError, match=f"'{missing_key}'"):
        store_mod.load(file_path.name)


@pytest.mark.parametrize(
    "invalid_items",
    [{"not": "a list"}, "invalid", 1, True, False],
)
def test_load_items_not_list_raises_type_error(
    invalid_items: object, snapshots_dir: Path
) -> None:
    data = {"date": "2026-02-11", "currency": "KRW", "items": invalid_items}
    file_path = snapshots_dir / "invalid.json"
    _write_json(file_path, data)

    with pytest.raises(TypeError):
        store_mod.load(file_path.name)


# ---------------------------------------------------------------------------
# load — happy path
# ---------------------------------------------------------------------------


def test_load_valid_snapshot_dto_returns_dto(snapshots_dir: Path) -> None:
    dto = _valid_snapshot_dto()
    file_path = snapshots_dir / "ok.json"
    _write_json(file_path, dto)

    result = store_mod.load(file_path.name)

    assert isinstance(result, dict)
    assert result["date"] == dto["date"]
    assert result["currency"] == dto["currency"]

    items = result["items"]
    assert isinstance(items, list)

    for item, item_dto in zip(items, dto["items"], strict=True):
        assert item["asset_id"] == item_dto["asset_id"]
        assert item["label"] == item_dto["label"]
        assert item["amount"] == item_dto["amount"]


# ---------------------------------------------------------------------------
# save_to_file
# ---------------------------------------------------------------------------


class TestSaveToFile:
    """Tests for save_to_file: persist a snapshot to a specific filename."""

    def test_save_to_file_creates_file_with_given_name(
        self, snapshots_dir: Path
    ) -> None:
        """save_to_file should create a file with the exact given name."""
        dto = _valid_snapshot_dto()
        store_mod.save_to_file(dto, "snapshot_2026-02-12_v1.json")

        file_path = snapshots_dir / "snapshot_2026-02-12_v1.json"
        assert file_path.exists()
        assert _read_json(file_path) == dto

    def test_save_to_file_overwrites_existing(self, snapshots_dir: Path) -> None:
        """save_to_file should overwrite an existing file with the same name."""
        dto1 = _valid_snapshot_dto()
        dto2 = _valid_snapshot_dto()
        dto2["items"][0]["label"] = "Updated Label"

        store_mod.save_to_file(dto1, "snapshot_2026-02-12_v1.json")
        store_mod.save_to_file(dto2, "snapshot_2026-02-12_v1.json")

        file_path = snapshots_dir / "snapshot_2026-02-12_v1.json"
        assert _read_json(file_path) == dto2

    def test_save_to_file_creates_directory_if_missing(
        self, snapshots_dir: Path
    ) -> None:
        """save_to_file should create the snapshots directory if it does not exist."""
        # snapshots_dir doesn't physically exist yet since fixture only sets attr
        assert not snapshots_dir.exists()

        dto = _valid_snapshot_dto()
        store_mod.save_to_file(dto, "snapshot_2026-02-12_v1.json")

        assert snapshots_dir.exists()
        assert (snapshots_dir / "snapshot_2026-02-12_v1.json").exists()

    def test_save_to_file_preserves_original_date_in_dto(
        self, snapshots_dir: Path
    ) -> None:
        """save_to_file should write exactly the DTO content without altering date."""
        dto = _valid_snapshot_dto()
        dto["date"] = "2026-01-15"

        store_mod.save_to_file(dto, "snapshot_2026-01-15_v1.json")

        result = _read_json(snapshots_dir / "snapshot_2026-01-15_v1.json")
        assert result["date"] == "2026-01-15"
