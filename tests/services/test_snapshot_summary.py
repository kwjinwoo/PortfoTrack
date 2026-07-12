"""Tests for portable snapshot summary generation."""

from portfotrack.domain.asset import Asset
from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation, Tolerance
from portfotrack.services.snapshot_summary import build_snapshot_summary


def _target() -> TargetAllocation:
    target = TargetAllocation()
    target.add_asset(
        Asset("us_equity", "미국 주식", "성장"),
        0.6,
        Tolerance(lower=0.55, upper=0.65),
    )
    target.add_asset(
        Asset("kr_bond", "한국 채권", "안정"),
        0.4,
        Tolerance(lower=0.35, upper=0.45),
    )
    return target


def _snapshot(date: str, us_equity: int, kr_bond: int) -> Snapshot:
    snapshot = Snapshot(date=date, currency="KRW")
    snapshot.add_snapshot_item("us_equity", "S&P 500", us_equity)
    snapshot.add_snapshot_item("kr_bond", "국채", kr_bond)
    return snapshot


def test_builds_mobile_summary_with_additions_reductions_and_distribution() -> None:
    """Summary exposes signed target gaps and their separate distributions."""
    summary = build_snapshot_summary(
        _target(),
        _snapshot("2026-07-11", 4_000_000, 6_000_000),
        _snapshot("2026-07-04", 3_500_000, 5_500_000),
    )

    assert summary["schema_version"] == "1.0"
    assert summary["kind"] == "snapshot_summary"
    assert summary["snapshot_date"] == "2026-07-11"
    assert "총자산: 10,000,000원" in summary["message"]
    assert "이전 대비: +1,000,000원 (+11.11%)" in summary["message"]
    assert "미국 주식 ⚠️ 허용 범위 이탈" in summary["message"]
    assert "현재 금액: 4,000,000원" in summary["message"]
    assert "현재 / 목표: 40.0% / 60.0%" in summary["message"]
    assert "허용 범위: 55.0%–65.0%" in summary["message"]
    assert "목표 기준 필요 추가금: +2,000,000원" in summary["message"]
    assert "한국 채권 ⚠️ 허용 범위 이탈" in summary["message"]
    assert "목표 기준 필요 감액: 2,000,000원" in summary["message"]
    assert "목표 비중 보완에 필요한 총액: 2,000,000원" in summary["message"]
    assert "• 미국 주식: 2,000,000원 · 100.0%" in summary["message"]
    assert "목표 비중 초과분 감액 참고" in summary["message"]
    assert "목표 비중 초과분의 총액: 2,000,000원" in summary["message"]
    assert "• 한국 채권: 2,000,000원 · 100.0%" in summary["message"]
    assert "개인화된 투자 조언이나 거래 지시가 아닙니다." in summary["message"]


def test_summary_handles_missing_previous_snapshot_and_no_shortfall() -> None:
    """First snapshots and fully funded targets have explicit empty states."""
    summary = build_snapshot_summary(
        _target(),
        _snapshot("2026-07-11", 6_000_000, 4_000_000),
        None,
    )

    assert "이전 대비: 비교할 이전 스냅샷 없음" in summary["message"]
    assert "허용 범위 이탈: 0개 자산군" in summary["message"]
    assert "목표 비중 보완에 필요한 추가금이 없습니다." in summary["message"]
    assert "목표 비중 초과분에 대한 감액 참고값이 없습니다." in summary["message"]


def test_summary_handles_zero_previous_total_without_dividing_by_zero() -> None:
    """A zero-value previous snapshot reports amount change without a rate."""
    previous = Snapshot(date="2026-07-04", currency="KRW")

    summary = build_snapshot_summary(
        _target(),
        _snapshot("2026-07-11", 6_000_000, 4_000_000),
        previous,
    )

    assert "이전 대비: +10,000,000원 (비율 계산 불가)" in summary["message"]
