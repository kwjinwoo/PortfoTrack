import pytest

from portfotrack.services import target_services


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
