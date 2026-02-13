from unittest.mock import Mock

import pytest

from portfotrack.cli.state import ReplState
from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation

MODULE = "portfotrack.cli.report_cli.report"


# ---------------------------
# Fixtures
# ---------------------------


@pytest.fixture()
def empty_target() -> TargetAllocation:
    return TargetAllocation()


@pytest.fixture()
def empty_snapshot() -> Snapshot:
    return Snapshot()


@pytest.fixture()
def state_with_both(
    empty_target: TargetAllocation, empty_snapshot: Snapshot
) -> ReplState:
    return ReplState(target=empty_target, snapshot=empty_snapshot)


@pytest.fixture()
def state_without_target(empty_snapshot: Snapshot) -> ReplState:
    return ReplState(target=None, snapshot=empty_snapshot)


@pytest.fixture()
def state_without_snapshot(empty_target: TargetAllocation) -> ReplState:
    return ReplState(target=empty_target, snapshot=None)


# ---------------------------
# run_report — happy path
# ---------------------------


def test_run_report_calls_services_and_prints_result(
    monkeypatch, capsys, state_with_both: ReplState
) -> None:
    """TC-1: When both target and snapshot exist, run_report should
    call generate_allocation_report and format_allocation_report,
    then print the formatted result."""
    sentinel_report = object()
    formatted_text = "== MOCK REPORT =="

    generate_mock = Mock(return_value=sentinel_report)
    format_mock = Mock(return_value=formatted_text)

    monkeypatch.setattr(f"{MODULE}.generate_allocation_report", generate_mock)
    monkeypatch.setattr(f"{MODULE}.format_allocation_report", format_mock)

    from portfotrack.cli.report_cli.report import run_report

    run_report(state_with_both, args=[])

    generate_mock.assert_called_once_with(
        state_with_both.target, state_with_both.snapshot
    )
    format_mock.assert_called_once_with(sentinel_report)

    out = capsys.readouterr().out
    assert formatted_text in out


def test_run_report_ignores_extra_args(
    monkeypatch, capsys, state_with_both: ReplState
) -> None:
    """run_report should work identically regardless of extra args."""
    sentinel_report = object()
    formatted_text = "== REPORT =="

    generate_mock = Mock(return_value=sentinel_report)
    format_mock = Mock(return_value=formatted_text)

    monkeypatch.setattr(f"{MODULE}.generate_allocation_report", generate_mock)
    monkeypatch.setattr(f"{MODULE}.format_allocation_report", format_mock)

    from portfotrack.cli.report_cli.report import run_report

    run_report(state_with_both, args=["extra", "args"])

    generate_mock.assert_called_once()
    format_mock.assert_called_once()
    out = capsys.readouterr().out
    assert formatted_text in out


# ---------------------------
# run_report — no target
# ---------------------------


def test_run_report_no_target_prints_message_and_skips_service(
    monkeypatch, capsys, state_without_target: ReplState
) -> None:
    """TC-2: When target is None, print a user-friendly message
    and do NOT call any service functions."""
    generate_mock = Mock()
    format_mock = Mock()

    monkeypatch.setattr(f"{MODULE}.generate_allocation_report", generate_mock)
    monkeypatch.setattr(f"{MODULE}.format_allocation_report", format_mock)

    from portfotrack.cli.report_cli.report import run_report

    run_report(state_without_target, args=[])

    out = capsys.readouterr().out
    assert "No target" in out
    generate_mock.assert_not_called()
    format_mock.assert_not_called()


# ---------------------------
# run_report — no snapshot
# ---------------------------


def test_run_report_no_snapshot_prints_message_and_skips_service(
    monkeypatch, capsys, state_without_snapshot: ReplState
) -> None:
    """TC-3: When snapshot is None, print a user-friendly message
    and do NOT call any service functions."""
    generate_mock = Mock()
    format_mock = Mock()

    monkeypatch.setattr(f"{MODULE}.generate_allocation_report", generate_mock)
    monkeypatch.setattr(f"{MODULE}.format_allocation_report", format_mock)

    from portfotrack.cli.report_cli.report import run_report

    run_report(state_without_snapshot, args=[])

    out = capsys.readouterr().out
    assert "No snapshot" in out
    generate_mock.assert_not_called()
    format_mock.assert_not_called()


# ---------------------------
# run_report — RuntimeError from service
# ---------------------------


def test_run_report_runtime_error_prints_user_message(
    monkeypatch, capsys, state_with_both: ReplState
) -> None:
    """TC-4: When generate_allocation_report raises RuntimeError
    (e.g. unknown asset), the handler should catch it and print
    the error message instead of propagating."""
    error_msg = "Unknown asset 'CRYPTO' in snapshot. It is not defined in the target allocation."
    generate_mock = Mock(side_effect=RuntimeError(error_msg))
    format_mock = Mock()

    monkeypatch.setattr(f"{MODULE}.generate_allocation_report", generate_mock)
    monkeypatch.setattr(f"{MODULE}.format_allocation_report", format_mock)

    from portfotrack.cli.report_cli.report import run_report

    run_report(state_with_both, args=[])

    out = capsys.readouterr().out
    assert "Unknown asset" in out
    format_mock.assert_not_called()


# ---------------------------
# register_report_commands
# ---------------------------


def test_register_report_commands_registers_report_command() -> None:
    """TC-5: register_report_commands should register 'report'
    with the correct handler and help text."""
    registry = Mock()

    from portfotrack.cli.report_cli.report import (
        register_report_commands,
        run_report,
    )

    register_report_commands(registry)

    assert registry.register.call_count == 1

    spec = registry.register.call_args_list[0].args[0]
    assert spec.name == "report"
    assert spec.handler is run_report
    assert spec.help != ""
