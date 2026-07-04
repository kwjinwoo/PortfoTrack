"""Tests for the versioned allocation-context JSON export."""

from portfotrack.domain.asset import Asset
from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation, Tolerance
from portfotrack.services.allocation_context_export import build_allocation_context_export
from portfotrack.services.allocation_report import generate_allocation_report


def _portfolio() -> tuple[TargetAllocation, Snapshot]:
    target = TargetAllocation()
    target.add_asset(
        Asset("us_equity", "US Equity", "growth"),
        0.6,
        Tolerance(lower=0.5, upper=0.7),
    )
    target.add_asset(
        Asset("kr_bond", "KR Bond", "stability"),
        0.4,
        Tolerance(lower=0.3, upper=0.5),
    )
    snapshot = Snapshot(date="2026-02-12", currency="KRW")
    snapshot.add_snapshot_item("us_equity", "S&P 500", 4_000_000)
    snapshot.add_snapshot_item("kr_bond", "Government Bond", 6_000_000)
    return target, snapshot


def test_builds_versioned_consumer_neutral_payload() -> None:
    """Export exposes allocation facts without labels or guidance."""
    target, snapshot = _portfolio()
    report = generate_allocation_report(target, snapshot)

    payload = build_allocation_context_export(snapshot, report)

    assert payload == {
        "schema_version": "1.0",
        "snapshot": {
            "date": "2026-02-12",
            "currency": "KRW",
            "total_amount": 10_000_000,
        },
        "assets": [
            {
                "asset_id": "kr_bond",
                "current_amount": 6_000_000,
                "current_weight": 0.6,
                "target_weight": 0.4,
                "target_range": {"lower": 0.3, "upper": 0.5},
                "drift_percentage_points": 20.0,
                "status": "above_tolerance",
            },
            {
                "asset_id": "us_equity",
                "current_amount": 4_000_000,
                "current_weight": 0.4,
                "target_weight": 0.6,
                "target_range": {"lower": 0.5, "upper": 0.7},
                "drift_percentage_points": -20.0,
                "status": "below_tolerance",
            },
        ],
    }


def test_preserves_unrounded_ratios_and_inclusive_boundary_status() -> None:
    """Contract retains computed precision and treats tolerance bounds as inclusive."""
    target, _ = _portfolio()
    snapshot = Snapshot(date="2026-02-12", currency="KRW")
    snapshot.add_snapshot_item("us_equity", "S&P 500", 5_000_000)
    snapshot.add_snapshot_item("kr_bond", "Government Bond", 5_000_000)
    report = generate_allocation_report(target, snapshot)

    payload = build_allocation_context_export(snapshot, report)

    by_id = {item["asset_id"]: item for item in payload["assets"]}
    assert by_id["us_equity"]["current_weight"] == 0.5
    assert by_id["us_equity"]["drift_percentage_points"] == -10.0
    assert by_id["us_equity"]["status"] == "within_tolerance"


def test_empty_portfolio_exports_zero_weights_without_guidance() -> None:
    """An empty selected snapshot remains a valid factual context export."""
    target, snapshot = _portfolio()
    snapshot.items.clear()
    report = generate_allocation_report(target, snapshot)

    payload = build_allocation_context_export(snapshot, report)

    assert payload["snapshot"]["total_amount"] == 0
    assert all(item["current_weight"] == 0.0 for item in payload["assets"])
    assert "total_additional_needed" not in payload
