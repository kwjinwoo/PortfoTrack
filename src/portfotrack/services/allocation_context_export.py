"""Versioned, consumer-neutral allocation-context export."""

from typing import Literal, TypedDict

from portfotrack.domain.snapshot import Snapshot
from portfotrack.services.allocation_report import AllocationReport

SCHEMA_VERSION = "1.0"


class TargetRangeDTO(TypedDict):
    """Inclusive target-allocation bounds expressed as ratios."""

    lower: float
    upper: float


class AllocationContextAssetDTO(TypedDict):
    """Stable allocation facts for one asset class."""

    asset_id: str
    current_amount: int
    current_weight: float
    target_weight: float
    target_range: TargetRangeDTO
    drift_percentage_points: float
    status: Literal["below_tolerance", "within_tolerance", "above_tolerance"]


class AllocationContextSnapshotDTO(TypedDict):
    """Identity and totals for the explicitly selected snapshot."""

    date: str
    currency: str
    total_amount: int


class AllocationContextExportDTO(TypedDict):
    """Versioned local-file contract for allocation context."""

    schema_version: str
    snapshot: AllocationContextSnapshotDTO
    assets: list[AllocationContextAssetDTO]


def build_allocation_context_export(
    snapshot: Snapshot,
    report: AllocationReport,
) -> AllocationContextExportDTO:
    """Build a deterministic allocation-facts payload for local exchange.

    Ratios retain the report's computed precision, while percentage-point
    drift is represented without display rounding. Asset labels and capital
    guidance are deliberately excluded so the contract remains stable and
    consumer-neutral.

    Args:
        snapshot: Snapshot explicitly selected by the user.
        report: Allocation comparison generated from the selected snapshot.

    Returns:
        A schema-versioned payload ordered by stable asset identifier.
    """
    assets: list[AllocationContextAssetDTO] = []
    for item in sorted(report.report_items, key=lambda value: value.asset_id):
        if item.current_ratio < item.tolerance["lower"]:
            status: Literal[
                "below_tolerance", "within_tolerance", "above_tolerance"
            ] = "below_tolerance"
        elif item.current_ratio > item.tolerance["upper"]:
            status = "above_tolerance"
        else:
            status = "within_tolerance"

        assets.append(
            {
                "asset_id": item.asset_id,
                "current_amount": item.current_amount,
                "current_weight": item.current_ratio,
                "target_weight": item.target_ratio,
                "target_range": {
                    "lower": item.tolerance["lower"],
                    "upper": item.tolerance["upper"],
                },
                "drift_percentage_points": round(
                    (item.current_ratio - item.target_ratio) * 100,
                    12,
                ),
                "status": status,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot": {
            "date": snapshot.date,
            "currency": snapshot.currency,
            "total_amount": report.total_portfolio_amount,
        },
        "assets": assets,
    }
