import pytest

from portfotrack.domain.asset import Asset
from portfotrack.domain.target_allocation import TargetAllocation, Tolerance
from portfotrack.services import target_services
from portfotrack.services.target_services import (
    get_available_assets_from_target,
    save_target_overwrite,
    validate_asset_id_in_target,
)


def _create_files(directory, names):
    for name in names:
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf8")


def test_load_latest_target_returns_most_recent_file(monkeypatch, tmp_path):
    monkeypatch.setattr(target_services, "TARGETS_DIR", tmp_path, raising=False)

    target_files = [
        "target_2026-01-01_v1.json",
        "target_2026-01-02_v1.json",
        "target_2025-12-31_v1.json",
    ]
    _create_files(tmp_path, target_files)

    captured = {}

    def fake_load(name):
        captured["loaded"] = name
        return {"file": name}

    def fake_dto_to_target(dto):
        captured["converted_dto"] = dto
        return f"converted-{dto['file']}"

    monkeypatch.setattr(target_services, "load", fake_load, raising=False)
    monkeypatch.setattr(
        target_services, "dto_to_target", fake_dto_to_target, raising=False
    )

    result = target_services.load_latest_target()

    assert result == "converted-target_2026-01-02_v1.json"
    assert captured["loaded"] == "target_2026-01-02_v1.json"
    assert captured["converted_dto"] == {"file": "target_2026-01-02_v1.json"}


def test_load_latest_target_empty_directory_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(target_services, "TARGETS_DIR", tmp_path, raising=False)

    def fail_if_called(*_args, **_kwargs):
        pytest.fail("load should not be invoked when directory is empty")

    monkeypatch.setattr(target_services, "load", fail_if_called, raising=False)
    monkeypatch.setattr(
        target_services, "dto_to_target", lambda dto: dto, raising=False
    )

    with pytest.raises(FileNotFoundError) as exc:
        target_services.load_latest_target()

    assert str(exc.value).startswith("No target files found under")


# ---------------------------
# get_available_assets_from_target
# ---------------------------


@pytest.fixture()
def tol() -> Tolerance:
    return {"lower": 0.2, "upper": 0.4}


class TestGetAvailableAssetsFromTarget:
    """Tests for get_available_assets_from_target function."""

    def test_returns_empty_list_for_empty_target(self) -> None:
        target = TargetAllocation()

        result = get_available_assets_from_target(target)

        assert result == []

    def test_returns_asset_info_for_single_asset(self, tol: Tolerance) -> None:
        target = TargetAllocation()
        target.add_asset(Asset("us_equity", "US Equity", "growth"), 0.5, tol)

        result = get_available_assets_from_target(target)

        assert len(result) == 1
        assert result[0] == {
            "id": "us_equity",
            "name": "US Equity",
            "purpose": "growth",
        }

    def test_returns_all_assets_for_multiple(self, tol: Tolerance) -> None:
        target = TargetAllocation()
        target.add_asset(Asset("us_equity", "US Equity", "growth"), 0.3, tol)
        target.add_asset(Asset("gold", "Gold", "hedge"), 0.3, tol)
        target.add_asset(Asset("kr_bond", "KR Bond", "stability"), 0.4, tol)

        result = get_available_assets_from_target(target)

        assert len(result) == 3
        ids = [a["id"] for a in result]
        assert "us_equity" in ids
        assert "gold" in ids
        assert "kr_bond" in ids


# ---------------------------
# validate_asset_id_in_target
# ---------------------------


class TestValidateAssetIdInTarget:
    """Tests for validate_asset_id_in_target function."""

    def test_returns_true_for_existing_asset(self, tol: Tolerance) -> None:
        target = TargetAllocation()
        target.add_asset(Asset("us_equity", "US Equity", "growth"), 0.5, tol)

        assert validate_asset_id_in_target(target, "us_equity") is True

    def test_returns_false_for_missing_asset(self, tol: Tolerance) -> None:
        target = TargetAllocation()
        target.add_asset(Asset("us_equity", "US Equity", "growth"), 0.5, tol)

        assert validate_asset_id_in_target(target, "kr_bond") is False

    def test_returns_false_for_empty_target(self) -> None:
        target = TargetAllocation()

        assert validate_asset_id_in_target(target, "us_equity") is False


# ---------------------------
# save_target_overwrite
# ---------------------------


class TestSaveTargetOverwrite:
    """Tests for save_target_overwrite service function."""

    def test_saves_to_specified_filename(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        import portfotrack.storage.json_store.target_store as store_mod

        targets_dir = tmp_path / "targets"
        monkeypatch.setattr(store_mod, "TARGETS_DIR", targets_dir, raising=True)

        target = TargetAllocation()
        target.add_asset(
            Asset("us_equity", "US Equity", "growth"),
            0.5,
            {"lower": 0.4, "upper": 0.6},
        )
        target.add_asset(
            Asset("kr_bond", "KR Bond", "stability"),
            0.5,
            {"lower": 0.4, "upper": 0.6},
        )

        file_name = "target_2026-01-15_v1.json"
        save_target_overwrite(target, file_name)

        saved_file = targets_dir / file_name
        assert saved_file.exists()

    def test_saved_content_matches_dto(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        import json

        import portfotrack.storage.json_store.target_store as store_mod
        from portfotrack.storage.serialization.target_json import target_to_dto

        targets_dir = tmp_path / "targets"
        monkeypatch.setattr(store_mod, "TARGETS_DIR", targets_dir, raising=True)

        target = TargetAllocation()
        target.add_asset(
            Asset("us_equity", "US Equity", "growth"),
            0.5,
            {"lower": 0.4, "upper": 0.6},
        )
        target.add_asset(
            Asset("kr_bond", "KR Bond", "stability"),
            0.5,
            {"lower": 0.4, "upper": 0.6},
        )

        file_name = "target_2026-01-15_v1.json"
        save_target_overwrite(target, file_name)

        with open(targets_dir / file_name, encoding="utf-8") as f:
            saved = json.load(f)

        expected_dto = target_to_dto(target)
        assert saved == expected_dto
