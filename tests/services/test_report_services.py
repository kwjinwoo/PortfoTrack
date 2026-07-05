"""Tests for allocation report context loading."""

from pathlib import Path

import pytest

import portfotrack.services.report_services as report_services
from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation
from portfotrack.services.allocation_report import AllocationReport
from portfotrack.storage.json_store.errors import SnapshotNotFoundError


def test_load_context_uses_latest_version_for_explicit_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The context loader selects the latest file version for one date."""
    (tmp_path / "snapshot_2026-02-12_v1.json").touch()
    (tmp_path / "snapshot_2026-02-12_v2.json").touch()
    snapshot = Snapshot(date="2026-02-12", currency="KRW")
    target = TargetAllocation()
    report = AllocationReport("2026-02-12", 0)
    loaded_names: list[str] = []

    def fake_load_snapshot(file_name: str) -> Snapshot:
        loaded_names.append(file_name)
        return snapshot

    monkeypatch.setattr(report_services.path_mod, "SNAPSHOTS_DIR", tmp_path)
    monkeypatch.setattr(
        report_services, "load_snapshot_by_filename", fake_load_snapshot
    )
    monkeypatch.setattr(report_services, "load_latest_target", lambda: target)
    monkeypatch.setattr(
        report_services,
        "generate_allocation_report",
        lambda loaded_target, loaded_snapshot: report,
    )

    context = report_services.load_allocation_report_context("2026-02-12")

    assert loaded_names == ["snapshot_2026-02-12_v2.json"]
    assert context.snapshot is snapshot
    assert context.target is target
    assert context.report is report


def test_load_context_raises_for_missing_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A date without a matching snapshot preserves the storage error boundary."""
    monkeypatch.setattr(report_services.path_mod, "SNAPSHOTS_DIR", tmp_path)

    with pytest.raises(SnapshotNotFoundError):
        report_services.load_allocation_report_context("2099-01-01")
