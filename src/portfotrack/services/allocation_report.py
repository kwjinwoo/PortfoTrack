"""Allocation report service.

Compares a TargetAllocation against a Snapshot to produce a human-readable
report showing per-asset progress toward allocation goals.
"""

from dataclasses import dataclass, field

from portfotrack.domain.asset.asset import Asset
from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation, Tolerance
from portfotrack.services.snapshot_services import aggregate_snapshot

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AllocationReportItem:
    """A single row in the allocation report comparing one asset class.

    Attributes:
        asset_id: Stable identifier of the asset class.
        asset_name: Human-readable name of the asset.
        current_amount: Aggregated amount from the snapshot for this asset.
        total_portfolio: Total portfolio amount across all assets.
        current_ratio: Current allocation ratio (0.0–1.0).
        target_ratio: Target allocation ratio (0.0–1.0).
        target_amount_needed: Amount still needed to reach the target.
            Positive means shortfall, negative means excess.
        tolerance: Acceptable allocation range for this asset.
        is_within_tolerance: Whether the current ratio falls within the
            tolerance bounds (inclusive).
    """

    asset_id: str
    asset_name: str
    current_amount: int
    total_portfolio: int
    current_ratio: float
    target_ratio: float
    target_amount_needed: int
    tolerance: Tolerance
    is_within_tolerance: bool


@dataclass(frozen=True)
class AllocationReport:
    """Complete allocation comparison report.

    Attributes:
        snapshot_date: ISO-format date of the snapshot.
        total_portfolio_amount: Sum of all snapshot item amounts.
        report_items: Per-asset comparison items.
    """

    snapshot_date: str
    total_portfolio_amount: int
    report_items: list[AllocationReportItem] = field(default_factory=list)

    def is_complete(self) -> bool:
        """Check whether every asset is within its tolerance range.

        Returns:
            True if all report items are within tolerance; False otherwise.
        """
        return all(item.is_within_tolerance for item in self.report_items)

    def total_additional_needed(self) -> int:
        """Sum of shortfall amounts across all assets.

        Only positive (shortfall) values are summed; excess allocations
        are ignored because the user needs to know how much more capital
        is required, not how much to liquidate.

        Returns:
            Total additional capital needed to reach all targets.
        """
        return sum(
            item.target_amount_needed
            for item in self.report_items
            if item.target_amount_needed > 0
        )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_allocation_report(
    target_allocation: TargetAllocation,
    snapshot: Snapshot,
) -> AllocationReport:
    """Generate an allocation comparison report.

    Aggregates snapshot items by asset_id using ``aggregate_snapshot``,
    then compares each asset against the target allocation to determine
    current ratios, shortfalls, and tolerance status.

    Args:
        target_allocation: The desired portfolio allocation.
        snapshot: The current portfolio snapshot.

    Returns:
        An AllocationReport containing per-asset comparison data.

    Raises:
        RuntimeError: If the snapshot contains an asset_id that does not
            appear in the target allocation.
    """
    aggregated = aggregate_snapshot(snapshot)
    total = sum(aggregated.values())

    # Build an asset_id → Asset lookup from the target allocation
    id_to_asset: dict[str, Asset] = {}
    for asset in target_allocation.target_assets:
        id_to_asset[asset.id] = asset

    # Validate: every snapshot asset_id must exist in the target
    for asset_id in aggregated:
        if asset_id not in id_to_asset:
            raise RuntimeError(
                f"Unknown asset '{asset_id}' in snapshot. "
                f"It is not defined in the target allocation."
            )

    # Build report items — one per target asset
    items: list[AllocationReportItem] = []
    for asset, (target_ratio, tolerance) in target_allocation.target_assets.items():
        current_amount = aggregated.get(asset.id, 0)
        current_ratio = current_amount / total if total > 0 else 0.0
        target_amount = int(total * target_ratio)
        needed = target_amount - current_amount

        lo = tolerance["lower"]
        hi = tolerance["upper"]
        within = lo <= current_ratio <= hi

        items.append(
            AllocationReportItem(
                asset_id=asset.id,
                asset_name=asset.name,
                current_amount=current_amount,
                total_portfolio=total,
                current_ratio=current_ratio,
                target_ratio=target_ratio,
                target_amount_needed=needed,
                tolerance=tolerance,
                is_within_tolerance=within,
            )
        )

    return AllocationReport(
        snapshot_date=snapshot.date,
        total_portfolio_amount=total,
        report_items=items,
    )


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def format_allocation_report(report: AllocationReport) -> str:
    """Format an AllocationReport as a human-readable text table.

    The output includes:
    - Snapshot date and total portfolio amount.
    - Per-asset rows with current vs target ratios, amounts, and
      the additional amount needed.
    - Visual tolerance-status indicators (✓ / ✗).
    - A summary footer with total additional capital needed.

    Args:
        report: The allocation report to format.

    Returns:
        A formatted multi-line string suitable for terminal display.
    """
    lines: list[str] = []

    # Header
    lines.append("=" * 66)
    lines.append(f"  Allocation Report  —  {report.snapshot_date}")
    lines.append(f"  Total Portfolio: {report.total_portfolio_amount:,} KRW")
    lines.append("=" * 66)
    lines.append("")

    # Column header
    lines.append(
        f"  {'Asset':<16} {'Current':>12} {'Ratio':>8} "
        f"{'Target':>8} {'Needed':>14} {'Status':>6}"
    )
    lines.append("  " + "-" * 64)

    # Per-asset rows
    for item in report.report_items:
        status = "✓" if item.is_within_tolerance else "✗"
        current_pct = f"{item.current_ratio * 100:.1f}%"
        target_pct = f"{item.target_ratio * 100:.1f}%"

        if item.target_amount_needed > 0:
            needed_str = f"+{item.target_amount_needed:,}"
        elif item.target_amount_needed < 0:
            needed_str = f"{item.target_amount_needed:,}"
        else:
            needed_str = "0"

        lines.append(
            f"  {item.asset_name:<16} "
            f"{item.current_amount:>12,} "
            f"{current_pct:>8} "
            f"{target_pct:>8} "
            f"{needed_str:>14} "
            f"{status:>6}"
        )

        # Tolerance detail
        lo_pct = f"{item.tolerance['lower'] * 100:.1f}%"
        hi_pct = f"{item.tolerance['upper'] * 100:.1f}%"
        lines.append(f"  {'':16} tolerance: [{lo_pct} – {hi_pct}]")

    lines.append("")
    lines.append("  " + "-" * 64)

    # Summary footer
    total_needed = report.total_additional_needed()
    if total_needed > 0:
        lines.append(f"  Additional capital needed: {total_needed:,} KRW")
    else:
        lines.append("  All targets met ✓")

    if report.is_complete():
        lines.append("  Portfolio status: ON TARGET ✓")
    else:
        on_count = sum(1 for i in report.report_items if i.is_within_tolerance)
        total_count = len(report.report_items)
        lines.append(
            f"  Portfolio status: {on_count}/{total_count} assets within tolerance"
        )

    lines.append("=" * 66)
    return "\n".join(lines)
