import json
import re
from pathlib import Path
from typing import Any

import pytest

import portfotrack.storage.json_store.target_store as store_mod
from portfotrack.storage.json_store.errors import TargetNotFoundError
from portfotrack.storage.serialization.target_json import TargetAllocationDTO


@pytest.fixture()
def targets_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:

    d = tmp_path / "targets"
    monkeypatch.setattr(store_mod, "TARGETS_DIR", d, raising=True)
    return d


def _valid_target_dto() -> TargetAllocationDTO:
    # Must match what save() expects (TargetAllocationDTO), i.e. JSON-serializable dict.
    return {
        "assets": [
            {
                "id": "us_etf",
                "name": "S&P500",
                "purpose": "growth",
                "target_ratio": 0.4,
                "tolerance": {"lower": 0.35, "upper": 0.45},
            },
            {
                "id": "cash_krw",
                "name": "KRW Cash",
                "purpose": "cash",
                "target_ratio": 0.6,  # int/float both allowed; load() casts to float.
                "tolerance": {"lower": 0.55, "upper": 0.65},
            },
        ]
    }


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode="w", encoding="utf8") as f:
        json.dump(obj, f)


def _read_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_save_creates_dir_and_file_and_writes_json(targets_dir: Path):
    dto = _valid_target_dto()
    store_mod.save(dto)
    assert targets_dir.exists() and targets_dir.is_dir()

    files = sorted(targets_dir.glob("target_*.json"))
    assert len(files) == 1

    v = store_mod.CURRENT_TARGET_SCHEMA_VERSION
    file = files[0]
    assert re.match(rf"^target_\d{{4}}-\d{{2}}-\d{{2}}_v{v}\.json$", file.name)

    assert _read_json(file) == dto


def test_save_overwrites_same_day_same_version(targets_dir: Path):
    dto1 = _valid_target_dto()
    dto2 = _valid_target_dto()
    dto2["assets"][0]["name"] = "S&P500 (updated)"

    store_mod.save(dto1)
    files = sorted(targets_dir.glob("target_*.json"))
    assert len(files) == 1
    assert _read_json(files[0]) == dto1

    file_name = files[0].name
    store_mod.save(dto2)
    overwrited_files = sorted(targets_dir.glob("target_*.json"))
    assert len(overwrited_files) == 1
    assert overwrited_files[0].name == file_name
    assert _read_json(overwrited_files[0]) == dto2


def test_load_missing_file_raise_target_not_found():
    with pytest.raises(TargetNotFoundError):
        store_mod.load("does_not_exist.json")


@pytest.mark.parametrize("invalid_data", [["invliad"], "invalid", 123, True, False])
def test_load_root_not_dict_raise_runtime_error(invalid_data, targets_dir: Path):
    file_path = targets_dir / "invalid.json"
    _write_json(file_path, invalid_data)

    with pytest.raises(RuntimeError):
        store_mod.load(file_path.name)


def test_load_missing_root_asset_key_raise_runtime_error(targets_dir: Path):
    invalid_data = {"invalid_key": "invalid_data"}
    file_path = targets_dir / "invalid.json"
    _write_json(file_path, invalid_data)

    with pytest.raises(RuntimeError):
        store_mod.load(file_path.name)


@pytest.mark.parametrize(
    "invalid_data",
    [{"invalid_data": "invalid_value"}, "invalid_data1, invalid_data2", 1, True, False],
)
def test_load_asset_not_list_raise_type_error(invalid_data, targets_dir: Path):
    invalid_data = {"assets": invalid_data}
    file_path = targets_dir / "invalid.json"
    _write_json(file_path, invalid_data)

    with pytest.raises(TypeError):
        store_mod.load(file_path.name)


def test_load_reconstruct_target(targets_dir: Path):
    dto = _valid_target_dto()
    file_path = targets_dir / "ok.json"
    _write_json(file_path, dto)

    target = store_mod.load(file_path.name)

    assert isinstance(target, dict)

    assets = target["assets"]
    assert isinstance(assets, list)

    for asset, asset_dto in zip(assets, dto["assets"], strict=True):
        assert asset["id"] == asset_dto["id"]
        assert asset["name"] == asset_dto["name"]
        assert asset["purpose"] == asset_dto["purpose"]
        assert asset["target_ratio"] == asset_dto["target_ratio"]
        assert asset["tolerance"] == asset_dto["tolerance"]
