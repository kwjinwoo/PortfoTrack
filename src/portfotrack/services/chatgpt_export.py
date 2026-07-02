"""ChatGPT-friendly Markdown export for portfolio facts."""

from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation
from portfotrack.services.allocation_report import AllocationReport


def _percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def format_portfolio_markdown(
    target: TargetAllocation,
    snapshot: Snapshot,
    report: AllocationReport,
    *,
    include_labels: bool = True,
    hide_amounts: bool = False,
) -> str:
    """Format a target and snapshot as factual, paste-ready Markdown.

    The export intentionally contains no suggested prompt or financial advice.
    Privacy options can omit holding labels and all exact monetary amounts while
    retaining allocation ratios needed for a useful conversation.

    Args:
        target: Current target allocation used for comparison.
        snapshot: Historical snapshot selected by the user.
        report: Allocation comparison generated from ``target`` and ``snapshot``.
        include_labels: Whether individual holding labels should be included.
        hide_amounts: Whether exact portfolio amounts should be omitted.

    Returns:
        A deterministic Markdown document describing the portfolio state.
    """
    lines = [
        "# PortfoTrack 포트폴리오 분석 자료",
        "",
        f"기준일: {snapshot.date}",
        f"통화: {snapshot.currency}",
    ]
    if not hide_amounts:
        lines.append(f"총자산: {report.total_portfolio_amount:,}원")

    lines.extend(
        [
            "",
            "## 목표 배분",
            "",
            "| 자산군 | 목적 | 목표 | 허용 범위 |",
            "|---|---|---:|---:|",
        ]
    )
    for asset, (ratio, tolerance) in target.target_assets.items():
        lines.append(
            f"| {_cell(asset.name)} | {_cell(asset.purpose)} | "
            f"{_percentage(ratio)} | {tolerance['lower'] * 100:.1f}–"
            f"{_percentage(tolerance['upper'])} |"
        )

    lines.extend(["", "## 현재 스냅샷", ""])
    if include_labels and not hide_amounts:
        lines.extend(
            [
                "| 자산군 | 항목 | 금액 | 현재 비중 |",
                "|---|---|---:|---:|",
            ]
        )
        total = report.total_portfolio_amount
        for item in snapshot.items:
            ratio = item.amount / total if total > 0 else 0.0
            lines.append(
                f"| {_cell(item.asset_id)} | {_cell(item.label)} | "
                f"{item.amount:,}원 | {_percentage(ratio)} |"
            )
    elif include_labels:
        lines.extend(
            [
                "| 자산군 | 항목 | 현재 비중 |",
                "|---|---|---:|",
            ]
        )
        total = report.total_portfolio_amount
        for item in snapshot.items:
            ratio = item.amount / total if total > 0 else 0.0
            lines.append(
                f"| {_cell(item.asset_id)} | {_cell(item.label)} | "
                f"{_percentage(ratio)} |"
            )
    elif hide_amounts:
        lines.extend(["| 자산군 | 현재 비중 |", "|---|---:|"])
        for item in report.report_items:
            lines.append(
                f"| {_cell(item.asset_id)} | {_percentage(item.current_ratio)} |"
            )
    else:
        lines.extend(
            [
                "| 자산군 | 금액 | 현재 비중 |",
                "|---|---:|---:|",
            ]
        )
        for item in report.report_items:
            lines.append(
                f"| {_cell(item.asset_id)} | {item.current_amount:,}원 | "
                f"{_percentage(item.current_ratio)} |"
            )

    lines.extend(
        [
            "",
            "## 목표 대비 상태",
            "",
            "| 자산군 | 현재 | 목표 | 차이 | 판정 |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for item in report.report_items:
        difference = (item.current_ratio - item.target_ratio) * 100
        if item.is_within_tolerance:
            status = "허용 범위 이내"
        elif item.current_ratio < item.tolerance["lower"]:
            status = "허용 범위 미달"
        else:
            status = "허용 범위 초과"
        lines.append(
            f"| {_cell(item.asset_name)} | {_percentage(item.current_ratio)} | "
            f"{_percentage(item.target_ratio)} | {difference:+.1f}%p | {status} |"
        )

    return "\n".join(lines) + "\n"
