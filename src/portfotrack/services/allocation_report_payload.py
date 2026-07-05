"""Typed allocation report payload for the local JSON API."""

from typing import TypedDict

from portfotrack.services.allocation_report import AllocationReport


class AllocationReportToleranceDTO(TypedDict):
    """Inclusive allocation ratio bounds for one report item."""

    lower: float
    upper: float


class AllocationReportItemDTO(TypedDict):
    """JSON-compatible allocation comparison for one asset class."""

    asset_id: str
    asset_name: str
    current_amount: int
    total_portfolio: int
    current_ratio: float
    target_ratio: float
    target_amount_needed: int
    tolerance: AllocationReportToleranceDTO
    is_within_tolerance: bool


class AllocationReportPayload(TypedDict):
    """Stable response shape for the allocation report endpoint."""

    snapshot_date: str
    total_portfolio_amount: int
    is_complete: bool
    total_additional_needed: int
    items: list[AllocationReportItemDTO]


def build_allocation_report_payload(
    report: AllocationReport,
) -> AllocationReportPayload:
    """Convert an allocation report into its established API representation.

    Item ordering follows the report so consumers see the same target-defined
    order as other report presentations. The builder performs no HTTP work and
    does not introduce rounding or additional allocation guidance.

    Args:
        report: Domain comparison result to expose through the local API.

    Returns:
        A JSON-compatible payload containing report facts and summaries.
    """
    items: list[AllocationReportItemDTO] = []
    for item in report.report_items:
        items.append(
            {
                "asset_id": item.asset_id,
                "asset_name": item.asset_name,
                "current_amount": item.current_amount,
                "total_portfolio": item.total_portfolio,
                "current_ratio": item.current_ratio,
                "target_ratio": item.target_ratio,
                "target_amount_needed": item.target_amount_needed,
                "tolerance": {
                    "lower": item.tolerance["lower"],
                    "upper": item.tolerance["upper"],
                },
                "is_within_tolerance": item.is_within_tolerance,
            }
        )

    return {
        "snapshot_date": report.snapshot_date,
        "total_portfolio_amount": report.total_portfolio_amount,
        "is_complete": report.is_complete(),
        "total_additional_needed": report.total_additional_needed(),
        "items": items,
    }
