"""Tests for the ChatGPT-friendly portfolio Markdown export."""

from portfotrack.domain.asset import Asset
from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation
from portfotrack.services.allocation_report import generate_allocation_report
from portfotrack.services.chatgpt_export import format_portfolio_markdown


def _portfolio() -> tuple[TargetAllocation, Snapshot]:
    target = TargetAllocation()
    target.add_asset(
        Asset("us_equity", "US Equity", "growth"),
        0.6,
        {"lower": 0.5, "upper": 0.7},
    )
    target.add_asset(
        Asset("kr_bond", "KR Bond", "stability"),
        0.4,
        {"lower": 0.3, "upper": 0.5},
    )
    snapshot = Snapshot(date="2026-02-12", currency="KRW")
    snapshot.add_snapshot_item("us_equity", "S&P 500", 4_000_000)
    snapshot.add_snapshot_item("kr_bond", "국채", 6_000_000)
    return target, snapshot


def test_formats_target_snapshot_and_drift_without_request_prompt() -> None:
    """Export contains factual portfolio sections but no suggested prompt."""
    target, snapshot = _portfolio()
    report = generate_allocation_report(target, snapshot)

    markdown = format_portfolio_markdown(target, snapshot, report)

    assert "# PortfoTrack 포트폴리오 분석 자료" in markdown
    assert "기준일: 2026-02-12" in markdown
    assert "총자산: 10,000,000원" in markdown
    assert "| US Equity | growth | 60.0% | 50.0–70.0% |" in markdown
    assert "| us_equity | S&P 500 | 4,000,000원 | 40.0% |" in markdown
    assert "| US Equity | 40.0% | 60.0% | -20.0%p | 허용 범위 미달 |" in markdown
    assert "ChatGPT에게 요청할 내용" not in markdown


def test_can_hide_labels_and_amounts() -> None:
    """Privacy options remove holding labels and exact portfolio amounts."""
    target, snapshot = _portfolio()
    report = generate_allocation_report(target, snapshot)

    markdown = format_portfolio_markdown(
        target,
        snapshot,
        report,
        include_labels=False,
        hide_amounts=True,
    )

    assert "S&P 500" not in markdown
    assert "10,000,000" not in markdown
    assert "4,000,000" not in markdown
    assert "| 자산군 | 현재 비중 |" in markdown
    assert "| us_equity | 40.0% |" in markdown
