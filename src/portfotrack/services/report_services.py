"""Service orchestration for loading allocation report context."""

from dataclasses import dataclass

import portfotrack.path as path_mod
from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation
from portfotrack.services.allocation_report import (
    AllocationReport,
    generate_allocation_report,
)
from portfotrack.services.snapshot_services import load_snapshot_by_filename
from portfotrack.services.target_services import load_latest_target
from portfotrack.storage.json_store.errors import SnapshotNotFoundError


@dataclass(frozen=True)
class AllocationReportContext:
    """Domain objects that must refer to the same allocation comparison."""

    target: TargetAllocation
    snapshot: Snapshot
    report: AllocationReport


def load_allocation_report_context(snapshot_date: str) -> AllocationReportContext:
    """Load one selected snapshot, the latest target, and their report.

    When multiple persisted versions exist for the selected date, filename
    ordering chooses the latest version. Missing-resource exceptions remain
    unchanged so the calling boundary can translate them consistently.

    Args:
        snapshot_date: Explicit ISO snapshot date selected by the caller.

    Returns:
        The selected snapshot, latest target, and generated comparison report.

    Raises:
        SnapshotNotFoundError: If the selected date has no persisted snapshot.
        FileNotFoundError: If no target allocation exists.
    """
    matching = sorted(
        path_mod.SNAPSHOTS_DIR.glob(f"snapshot_{snapshot_date}_v*.json")
    )
    if not matching:
        raise SnapshotNotFoundError(
            file_name=f"snapshot_{snapshot_date}_v*.json"
        )

    snapshot = load_snapshot_by_filename(matching[-1].name)
    target = load_latest_target()
    report = generate_allocation_report(target, snapshot)
    return AllocationReportContext(target=target, snapshot=snapshot, report=report)
