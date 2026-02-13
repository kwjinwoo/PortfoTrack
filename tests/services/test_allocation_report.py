import pytest

from portfotrack.domain.asset import Asset
from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation, Tolerance
from portfotrack.services.allocation_report import (
    AllocationReport,
    AllocationReportItem,
    format_allocation_report,
    generate_allocation_report,
)

# ---------------------------------------------------------------------------
# Phase 1 – Data model tests
# ---------------------------------------------------------------------------


class TestAllocationReportItem:
    """Tests for AllocationReportItem dataclass."""

    def test_create_report_item(self):
        """AllocationReportItem can be instantiated with all fields."""
        item = AllocationReportItem(
            asset_id="US_EQUITY",
            asset_name="US Equities",
            current_amount=5_000_000,
            total_portfolio=10_000_000,
            current_ratio=0.50,
            target_ratio=0.60,
            target_amount_needed=1_000_000,
            tolerance=Tolerance(lower=0.55, upper=0.65),
            is_within_tolerance=False,
        )

        assert item.asset_id == "US_EQUITY"
        assert item.asset_name == "US Equities"
        assert item.current_amount == 5_000_000
        assert item.total_portfolio == 10_000_000
        assert item.current_ratio == 0.50
        assert item.target_ratio == 0.60
        assert item.target_amount_needed == 1_000_000
        assert item.is_within_tolerance is False


class TestAllocationReport:
    """Tests for AllocationReport dataclass and its convenience methods."""

    @pytest.fixture
    def two_item_report(self) -> AllocationReport:
        """Report with two items: one within tolerance, one not."""
        return AllocationReport(
            snapshot_date="2026-02-14",
            total_portfolio_amount=10_000_000,
            report_items=[
                AllocationReportItem(
                    asset_id="US_EQUITY",
                    asset_name="US Equities",
                    current_amount=6_000_000,
                    total_portfolio=10_000_000,
                    current_ratio=0.60,
                    target_ratio=0.60,
                    target_amount_needed=0,
                    tolerance=Tolerance(lower=0.55, upper=0.65),
                    is_within_tolerance=True,
                ),
                AllocationReportItem(
                    asset_id="KR_BOND",
                    asset_name="KR Bonds",
                    current_amount=2_000_000,
                    total_portfolio=10_000_000,
                    current_ratio=0.20,
                    target_ratio=0.40,
                    target_amount_needed=2_000_000,
                    tolerance=Tolerance(lower=0.35, upper=0.45),
                    is_within_tolerance=False,
                ),
            ],
        )

    def test_is_complete_returns_false_when_any_item_outside_tolerance(
        self, two_item_report: AllocationReport
    ):
        """is_complete() returns False if any item is outside tolerance."""
        assert two_item_report.is_complete() is False

    def test_is_complete_returns_true_when_all_within_tolerance(self):
        """is_complete() returns True when every item is within tolerance."""
        report = AllocationReport(
            snapshot_date="2026-02-14",
            total_portfolio_amount=10_000_000,
            report_items=[
                AllocationReportItem(
                    asset_id="US_EQUITY",
                    asset_name="US Equities",
                    current_amount=6_000_000,
                    total_portfolio=10_000_000,
                    current_ratio=0.60,
                    target_ratio=0.60,
                    target_amount_needed=0,
                    tolerance=Tolerance(lower=0.55, upper=0.65),
                    is_within_tolerance=True,
                ),
            ],
        )

        assert report.is_complete() is True

    def test_total_additional_needed_sums_positive_only(
        self, two_item_report: AllocationReport
    ):
        """total_additional_needed() sums only positive shortfall amounts."""
        assert two_item_report.total_additional_needed() == 2_000_000

    def test_total_additional_needed_excludes_excess(self):
        """total_additional_needed() ignores negative (excess) amounts."""
        report = AllocationReport(
            snapshot_date="2026-02-14",
            total_portfolio_amount=10_000_000,
            report_items=[
                AllocationReportItem(
                    asset_id="US_EQUITY",
                    asset_name="US Equities",
                    current_amount=8_000_000,
                    total_portfolio=10_000_000,
                    current_ratio=0.80,
                    target_ratio=0.60,
                    target_amount_needed=-2_000_000,
                    tolerance=Tolerance(lower=0.55, upper=0.65),
                    is_within_tolerance=False,
                ),
                AllocationReportItem(
                    asset_id="KR_BOND",
                    asset_name="KR Bonds",
                    current_amount=2_000_000,
                    total_portfolio=10_000_000,
                    current_ratio=0.20,
                    target_ratio=0.40,
                    target_amount_needed=2_000_000,
                    tolerance=Tolerance(lower=0.35, upper=0.45),
                    is_within_tolerance=False,
                ),
            ],
        )

        assert report.total_additional_needed() == 2_000_000

    def test_total_additional_needed_zero_when_all_met(self):
        """total_additional_needed() returns 0 when no shortfall exists."""
        report = AllocationReport(
            snapshot_date="2026-02-14",
            total_portfolio_amount=10_000_000,
            report_items=[
                AllocationReportItem(
                    asset_id="US_EQUITY",
                    asset_name="US Equities",
                    current_amount=6_000_000,
                    total_portfolio=10_000_000,
                    current_ratio=0.60,
                    target_ratio=0.60,
                    target_amount_needed=0,
                    tolerance=Tolerance(lower=0.55, upper=0.65),
                    is_within_tolerance=True,
                ),
            ],
        )

        assert report.total_additional_needed() == 0


# ---------------------------------------------------------------------------
# Phase 2 – generate_allocation_report() tests
# ---------------------------------------------------------------------------


def _make_target(*specs: tuple[str, str, str, float, float, float]) -> TargetAllocation:
    """Helper: build a TargetAllocation from (id, name, purpose, ratio, lo, hi) tuples."""
    ta = TargetAllocation()
    for asset_id, name, purpose, ratio, lo, hi in specs:
        ta.add_asset(
            Asset(asset_id, name, purpose), ratio, Tolerance(lower=lo, upper=hi)
        )
    return ta


def _make_snapshot(*items: tuple[str, str, int]) -> Snapshot:
    """Helper: build a Snapshot from (asset_id, label, amount) tuples."""
    snap = Snapshot()
    for asset_id, label, amount in items:
        snap.add_snapshot_item(asset_id, label, amount)
    return snap


class TestGenerateAllocationReport:
    """Tests for generate_allocation_report()."""

    def test_single_asset_on_target(self):
        """Single-asset portfolio exactly meeting its target."""
        target = _make_target(
            ("US_EQUITY", "US Equities", "growth", 1.0, 0.95, 1.0),
        )
        snapshot = _make_snapshot(("US_EQUITY", "S&P500", 10_000_000))

        report = generate_allocation_report(target, snapshot)

        assert report.total_portfolio_amount == 10_000_000
        assert report.snapshot_date == snapshot.date
        assert len(report.report_items) == 1

        item = report.report_items[0]
        assert item.asset_id == "US_EQUITY"
        assert item.asset_name == "US Equities"
        assert item.current_amount == 10_000_000
        assert item.current_ratio == pytest.approx(1.0)
        assert item.target_ratio == 1.0
        assert item.target_amount_needed == 0
        assert item.is_within_tolerance is True

    def test_multiple_assets_all_on_target(self):
        """Two-asset portfolio with both meeting targets."""
        target = _make_target(
            ("US_EQUITY", "US Equities", "growth", 0.6, 0.55, 0.65),
            ("KR_BOND", "KR Bonds", "stability", 0.4, 0.35, 0.45),
        )
        snapshot = _make_snapshot(
            ("US_EQUITY", "S&P500", 6_000_000),
            ("KR_BOND", "Treasury", 4_000_000),
        )

        report = generate_allocation_report(target, snapshot)

        assert report.total_portfolio_amount == 10_000_000
        assert len(report.report_items) == 2
        assert report.is_complete() is True

    def test_shortfall_asset(self):
        """Asset below target should report positive target_amount_needed."""
        target = _make_target(
            ("US_EQUITY", "US Equities", "growth", 0.6, 0.55, 0.65),
            ("KR_BOND", "KR Bonds", "stability", 0.4, 0.35, 0.45),
        )
        snapshot = _make_snapshot(
            ("US_EQUITY", "S&P500", 5_000_000),
            ("KR_BOND", "Treasury", 5_000_000),
        )

        report = generate_allocation_report(target, snapshot)

        us = next(i for i in report.report_items if i.asset_id == "US_EQUITY")
        assert us.current_amount == 5_000_000
        assert us.current_ratio == pytest.approx(0.50)
        assert us.target_amount_needed == 1_000_000
        assert us.is_within_tolerance is False

    def test_excess_asset(self):
        """Asset above target should report negative target_amount_needed."""
        target = _make_target(
            ("US_EQUITY", "US Equities", "growth", 0.6, 0.55, 0.65),
            ("KR_BOND", "KR Bonds", "stability", 0.4, 0.35, 0.45),
        )
        snapshot = _make_snapshot(
            ("US_EQUITY", "S&P500", 8_000_000),
            ("KR_BOND", "Treasury", 2_000_000),
        )

        report = generate_allocation_report(target, snapshot)

        us = next(i for i in report.report_items if i.asset_id == "US_EQUITY")
        assert us.current_amount == 8_000_000
        assert us.target_amount_needed == -2_000_000
        assert us.is_within_tolerance is False

    def test_aggregates_snapshot_items(self):
        """Multiple snapshot items with same asset_id are aggregated."""
        target = _make_target(
            ("US_EQUITY", "US Equities", "growth", 0.6, 0.55, 0.65),
            ("KR_BOND", "KR Bonds", "stability", 0.4, 0.35, 0.45),
        )
        snapshot = _make_snapshot(
            ("US_EQUITY", "S&P500", 3_000_000),
            ("US_EQUITY", "Nasdaq100", 3_000_000),
            ("KR_BOND", "Treasury", 4_000_000),
        )

        report = generate_allocation_report(target, snapshot)

        us = next(i for i in report.report_items if i.asset_id == "US_EQUITY")
        assert us.current_amount == 6_000_000

    def test_within_tolerance_boundary(self):
        """Ratio exactly on tolerance boundary is considered within tolerance."""
        target = _make_target(
            ("US_EQUITY", "US Equities", "growth", 0.6, 0.55, 0.65),
            ("KR_BOND", "KR Bonds", "stability", 0.4, 0.35, 0.45),
        )
        # 55% US_EQUITY → exactly on lower bound
        snapshot = _make_snapshot(
            ("US_EQUITY", "S&P500", 5_500_000),
            ("KR_BOND", "Treasury", 4_500_000),
        )

        report = generate_allocation_report(target, snapshot)

        us = next(i for i in report.report_items if i.asset_id == "US_EQUITY")
        assert us.is_within_tolerance is True

    def test_unknown_asset_in_snapshot_raises_runtime_error(self):
        """Snapshot asset_id not in TargetAllocation raises RuntimeError."""
        target = _make_target(
            ("US_EQUITY", "US Equities", "growth", 1.0, 0.95, 1.0),
        )
        snapshot = _make_snapshot(("UNKNOWN", "Mystery", 1_000_000))

        with pytest.raises(RuntimeError, match="Unknown asset"):
            generate_allocation_report(target, snapshot)

    def test_empty_snapshot_reports_zero_amounts(self):
        """Empty snapshot produces report with zero amounts for all targets."""
        target = _make_target(
            ("US_EQUITY", "US Equities", "growth", 0.6, 0.55, 0.65),
            ("KR_BOND", "KR Bonds", "stability", 0.4, 0.35, 0.45),
        )
        snapshot = _make_snapshot()

        report = generate_allocation_report(target, snapshot)

        assert report.total_portfolio_amount == 0
        assert len(report.report_items) == 2
        for item in report.report_items:
            assert item.current_amount == 0
            assert item.current_ratio == 0.0


# ---------------------------------------------------------------------------
# Phase 3 – format_allocation_report() tests
# ---------------------------------------------------------------------------


class TestFormatAllocationReport:
    """Tests for format_allocation_report()."""

    @pytest.fixture
    def basic_report(self) -> AllocationReport:
        return AllocationReport(
            snapshot_date="2026-02-14",
            total_portfolio_amount=10_000_000,
            report_items=[
                AllocationReportItem(
                    asset_id="US_EQUITY",
                    asset_name="US Equities",
                    current_amount=6_000_000,
                    total_portfolio=10_000_000,
                    current_ratio=0.60,
                    target_ratio=0.60,
                    target_amount_needed=0,
                    tolerance=Tolerance(lower=0.55, upper=0.65),
                    is_within_tolerance=True,
                ),
            ],
        )

    @pytest.fixture
    def multi_asset_report(self) -> AllocationReport:
        return AllocationReport(
            snapshot_date="2026-02-14",
            total_portfolio_amount=10_000_000,
            report_items=[
                AllocationReportItem(
                    asset_id="US_EQUITY",
                    asset_name="US Equities",
                    current_amount=5_000_000,
                    total_portfolio=10_000_000,
                    current_ratio=0.50,
                    target_ratio=0.60,
                    target_amount_needed=1_000_000,
                    tolerance=Tolerance(lower=0.55, upper=0.65),
                    is_within_tolerance=False,
                ),
                AllocationReportItem(
                    asset_id="KR_BOND",
                    asset_name="KR Bonds",
                    current_amount=5_000_000,
                    total_portfolio=10_000_000,
                    current_ratio=0.50,
                    target_ratio=0.40,
                    target_amount_needed=-1_000_000,
                    tolerance=Tolerance(lower=0.35, upper=0.45),
                    is_within_tolerance=False,
                ),
            ],
        )

    def test_format_contains_snapshot_date(self, basic_report: AllocationReport):
        """Formatted report must include the snapshot date."""
        result = format_allocation_report(basic_report)

        assert "2026-02-14" in result

    def test_format_contains_total_amount(self, basic_report: AllocationReport):
        """Formatted report must show total portfolio amount with comma separators."""
        result = format_allocation_report(basic_report)

        assert "10,000,000" in result

    def test_format_contains_asset_name(self, basic_report: AllocationReport):
        """Formatted report must show human-readable asset names."""
        result = format_allocation_report(basic_report)

        assert "US Equities" in result

    def test_format_contains_ratios_as_percent(self, basic_report: AllocationReport):
        """Formatted report must show ratios in percentage form."""
        result = format_allocation_report(basic_report)

        assert "60.0%" in result

    def test_format_multiple_assets_all_present(
        self, multi_asset_report: AllocationReport
    ):
        """Formatted report must include all assets."""
        result = format_allocation_report(multi_asset_report)

        assert "US Equities" in result
        assert "KR Bonds" in result

    def test_format_shows_needed_amount(self, multi_asset_report: AllocationReport):
        """Formatted report must show shortfall amount."""
        result = format_allocation_report(multi_asset_report)

        assert "1,000,000" in result

    def test_format_shows_tolerance_status_symbols(
        self, multi_asset_report: AllocationReport
    ):
        """Formatted report must use visual symbols for tolerance status."""
        result = format_allocation_report(multi_asset_report)

        assert "✗" in result  # at least one out of tolerance

    def test_format_on_target_shows_check(self, basic_report: AllocationReport):
        """Formatted report shows ✓ for items within tolerance."""
        result = format_allocation_report(basic_report)

        assert "✓" in result
