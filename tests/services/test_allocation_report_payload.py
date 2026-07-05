"""Tests for allocation report API payload construction."""

from portfotrack.domain.target_allocation import Tolerance
from portfotrack.services.allocation_report import (
    AllocationReport,
    AllocationReportItem,
)
from portfotrack.services.allocation_report_payload import (
    build_allocation_report_payload,
)


def test_builds_complete_allocation_report_payload() -> None:
    """The builder exposes the established API fields without web concerns."""
    report = AllocationReport(
        snapshot_date="2026-02-12",
        total_portfolio_amount=10_000_000,
        report_items=[
            AllocationReportItem(
                asset_id="us_equity",
                asset_name="US Equity",
                current_amount=4_000_000,
                total_portfolio=10_000_000,
                current_ratio=0.4,
                target_ratio=0.6,
                target_amount_needed=2_000_000,
                tolerance=Tolerance(lower=0.5, upper=0.7),
                is_within_tolerance=False,
            )
        ],
    )

    payload = build_allocation_report_payload(report)

    assert payload == {
        "snapshot_date": "2026-02-12",
        "total_portfolio_amount": 10_000_000,
        "is_complete": False,
        "total_additional_needed": 2_000_000,
        "items": [
            {
                "asset_id": "us_equity",
                "asset_name": "US Equity",
                "current_amount": 4_000_000,
                "total_portfolio": 10_000_000,
                "current_ratio": 0.4,
                "target_ratio": 0.6,
                "target_amount_needed": 2_000_000,
                "tolerance": {"lower": 0.5, "upper": 0.7},
                "is_within_tolerance": False,
            }
        ],
    }


def test_empty_report_payload_preserves_summary_semantics() -> None:
    """An empty report remains complete with no additional amount needed."""
    report = AllocationReport(
        snapshot_date="2026-02-12",
        total_portfolio_amount=0,
    )

    payload = build_allocation_report_payload(report)

    assert payload["items"] == []
    assert payload["is_complete"] is True
    assert payload["total_additional_needed"] == 0
