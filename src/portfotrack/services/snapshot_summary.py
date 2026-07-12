"""Portable, deterministic summaries of saved portfolio snapshots."""

from pathlib import Path

import portfotrack.path as path_mod
from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation
from portfotrack.services.allocation_report import (
    AllocationReport,
    generate_allocation_report,
)
from portfotrack.services.snapshot_services import aggregate_snapshot
from portfotrack.services.target_services import load_latest_target
from portfotrack.storage.json_store.notification_outbox_store import save
from portfotrack.storage.json_store.snapshot_store import load as load_snapshot_dto
from portfotrack.storage.serialization.notification_summary_json import (
    SnapshotSummaryDTO,
)
from portfotrack.storage.serialization.snapshot_json import dto_to_snapshot

SCHEMA_VERSION = "1.0"


def build_snapshot_summary(
    target: TargetAllocation,
    snapshot: Snapshot,
    previous_snapshot: Snapshot | None,
) -> SnapshotSummaryDTO:
    """Build a mobile-readable allocation summary from local facts.

    Adjustment amounts retain the established allocation report meaning:
    each signed value is the gap between the current amount and target amount
    at the current total. Addition and reduction distributions are calculated
    separately; they do not forecast a post-adjustment state.

    Args:
        target: Target allocation used for the deterministic comparison.
        snapshot: Newly saved portfolio snapshot.
        previous_snapshot: Most recent earlier snapshot, when available.

    Returns:
        Versioned artifact containing a plain-text notification message.
    """
    report = generate_allocation_report(target, snapshot)
    message = _format_message(snapshot, previous_snapshot, report)
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "snapshot_summary",
        "snapshot_date": snapshot.date,
        "message": message,
    }


def queue_snapshot_summary(snapshot: Snapshot) -> Path | None:
    """Write a summary artifact after an explicit successful snapshot save.

    A target is required for allocation comparison. When setup is incomplete,
    no artifact is queued and the already completed snapshot save is unchanged.

    Args:
        snapshot: Newly persisted snapshot to summarize.

    Returns:
        Written artifact path, or ``None`` when no target exists.
    """
    try:
        target = load_latest_target()
    except FileNotFoundError:
        return None

    previous = _load_previous_snapshot(snapshot.date)
    summary = build_snapshot_summary(target, snapshot, previous)
    return save(summary)


def _load_previous_snapshot(snapshot_date: str) -> Snapshot | None:
    candidates: list[Path] = []
    for file_path in path_mod.SNAPSHOTS_DIR.glob("snapshot_*_v*.json"):
        parts = file_path.stem.split("_")
        if len(parts) >= 3 and parts[1] < snapshot_date:
            candidates.append(file_path)
    if not candidates:
        return None
    dto = load_snapshot_dto(sorted(candidates)[-1].name)
    return dto_to_snapshot(dto)


def _format_message(
    snapshot: Snapshot,
    previous_snapshot: Snapshot | None,
    report: AllocationReport,
) -> str:
    currency_suffix = "원" if snapshot.currency == "KRW" else f" {snapshot.currency}"
    out_of_range = sum(not item.is_within_tolerance for item in report.report_items)
    lines = [
        "📊 PortfoTrack 스냅샷",
        f"{snapshot.date} · {snapshot.currency}",
        "",
        f"총자산: {_amount(report.total_portfolio_amount, currency_suffix)}",
        _format_change(
            previous_snapshot, report.total_portfolio_amount, currency_suffix
        ),
        f"허용 범위 이탈: {out_of_range}개 자산군",
        "",
        "━━━━━━━━━━━━━━",
    ]

    for item in report.report_items:
        status = "✅ 정상" if item.is_within_tolerance else "⚠️ 허용 범위 이탈"
        adjustment_text = _format_adjustment(item.target_amount_needed, currency_suffix)
        lines.extend(
            [
                "",
                f"{item.asset_name} {status}",
                f"현재 금액: {_amount(item.current_amount, currency_suffix)}",
                f"현재 / 목표: {_percent(item.current_ratio)} / {_percent(item.target_ratio)}",
                (
                    "허용 범위: "
                    f"{_percent(item.tolerance['lower'])}–{_percent(item.tolerance['upper'])}"
                ),
                adjustment_text,
            ]
        )

    positive_items = [
        item for item in report.report_items if item.target_amount_needed > 0
    ]
    total_needed = report.total_additional_needed()
    lines.extend(["", "━━━━━━━━━━━━━━", "", "💰 추가 자금 분배 참고", ""])
    if total_needed == 0:
        lines.append("목표 비중 보완에 필요한 추가금이 없습니다.")
    else:
        lines.append(
            f"목표 비중 보완에 필요한 총액: {_amount(total_needed, currency_suffix)}"
        )
        lines.append("")
        for item in positive_items:
            distribution = item.target_amount_needed / total_needed
            lines.append(
                f"• {item.asset_name}: {_amount(item.target_amount_needed, currency_suffix)}"
                f" · {_percent(distribution)}"
            )

    reduction_items = [
        item for item in report.report_items if item.target_amount_needed < 0
    ]
    total_reduction = sum(-item.target_amount_needed for item in reduction_items)
    lines.extend(["", "📉 목표 비중 초과분 감액 참고", ""])
    if total_reduction == 0:
        lines.append("목표 비중 초과분에 대한 감액 참고값이 없습니다.")
    else:
        lines.append(
            f"목표 비중 초과분의 총액: {_amount(total_reduction, currency_suffix)}"
        )
        lines.append("")
        for item in reduction_items:
            reduction = -item.target_amount_needed
            distribution = reduction / total_reduction
            lines.append(
                f"• {item.asset_name}: {_amount(reduction, currency_suffix)}"
                f" · {_percent(distribution)}"
            )

    lines.extend(
        [
            "",
            "추가·감액은 현재 총자산의 목표 비중 기준 참고값입니다.",
            "설정된 목표와 허용 범위에 따른 규칙 기반 참고값이며,",
            "개인화된 투자 조언이나 거래 지시가 아닙니다.",
        ]
    )
    return "\n".join(lines)


def _format_change(
    previous_snapshot: Snapshot | None,
    current_total: int,
    currency_suffix: str,
) -> str:
    if previous_snapshot is None:
        return "이전 대비: 비교할 이전 스냅샷 없음"
    previous_total = sum(aggregate_snapshot(previous_snapshot).values())
    difference = current_total - previous_total
    sign = "+" if difference > 0 else ""
    amount_text = f"{sign}{difference:,}{currency_suffix}"
    if previous_total == 0:
        return f"이전 대비: {amount_text} (비율 계산 불가)"
    rate = difference / previous_total
    rate_sign = "+" if rate > 0 else ""
    return f"이전 대비: {amount_text} ({rate_sign}{rate * 100:.2f}%)"


def _amount(value: int, currency_suffix: str) -> str:
    return f"{value:,}{currency_suffix}"


def _format_adjustment(needed: int, currency_suffix: str) -> str:
    if needed > 0:
        return f"목표 기준 필요 추가금: +{_amount(needed, currency_suffix)}"
    if needed < 0:
        return f"목표 기준 필요 감액: {_amount(-needed, currency_suffix)}"
    return f"목표 기준 조정 필요액: {_amount(0, currency_suffix)}"


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"
