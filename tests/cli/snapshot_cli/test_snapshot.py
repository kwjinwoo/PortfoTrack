from unittest.mock import Mock

import pytest

from portfotrack.cli.parsing.flags import FlagParseResult
from portfotrack.cli.state import ReplState
from portfotrack.domain.snapshot import Snapshot

MODULE = "portfotrack.cli.snapshot_cli.snapshot"


# ---------------------------
# Fixtures
# ---------------------------


@pytest.fixture()
def empty_snapshot() -> Snapshot:
    """Return a fresh Snapshot instance for testing."""
    return Snapshot()


@pytest.fixture()
def state_without_snapshot() -> ReplState:
    """ReplState with no snapshot initialized."""
    return ReplState(snapshot=None)


@pytest.fixture()
def state_with_snapshot(empty_snapshot: Snapshot) -> ReplState:
    """ReplState with an initialized snapshot."""
    return ReplState(snapshot=empty_snapshot)


# ---------------------------
# run_init_snapshot
# ---------------------------


@pytest.mark.parametrize(
    "args",
    [
        [],  # No args
        ["extra"],  # Single extra arg
        ["extra", "args", "here"],  # Multiple extra args
    ],
    ids=["no_args", "one_extra_arg", "multiple_extra_args"],
)
def test_run_init_snapshot_ignores_args_and_initializes_snapshot(
    monkeypatch, args: list[str]
) -> None:
    """Test that run_init_snapshot calls init_snapshot and assigns to state.snapshot.

    The handler should ignore all positional arguments and simply delegate
    to init_snapshot, storing the result in state.snapshot.
    """
    sentinel_snapshot = Snapshot()
    init_snapshot_mock = Mock(return_value=sentinel_snapshot)
    monkeypatch.setattr(f"{MODULE}.init_snapshot", init_snapshot_mock)

    state = ReplState(snapshot=None)

    from portfotrack.cli.snapshot_cli.snapshot import run_init_snapshot

    run_init_snapshot(state, args)

    # Verify init_snapshot was called exactly once
    init_snapshot_mock.assert_called_once_with()

    # Verify the returned snapshot is assigned to state
    assert state.snapshot is sentinel_snapshot


# ---------------------------
# run_add_snapshot
# ---------------------------


def test_run_add_snapshot_prints_error_when_no_snapshot_initialized(
    state_without_snapshot: ReplState, capsys
) -> None:
    """Test that run_add_snapshot prints error message when state.snapshot is None."""
    from portfotrack.cli.snapshot_cli.snapshot import run_add_snapshot

    run_add_snapshot(
        state_without_snapshot, args=["asset1", "label1", "--amount", "100"]
    )

    captured = capsys.readouterr()
    assert "No snapshot" in captured.out
    assert "init-snapshot" in captured.out


@pytest.mark.parametrize(
    "args",
    [
        [],  # No args at all
        ["only_one"],  # Only one positional arg
    ],
    ids=["no_args", "one_arg"],
)
def test_run_add_snapshot_prints_usage_when_insufficient_args(
    state_with_snapshot: ReplState, args: list[str], capsys
) -> None:
    """Test that run_add_snapshot prints usage when len(args) < 2."""
    from portfotrack.cli.snapshot_cli.snapshot import run_add_snapshot

    run_add_snapshot(state_with_snapshot, args)

    captured = capsys.readouterr()
    assert "Usage: add-snapshot" in captured.out
    assert "--amount" in captured.out


def test_run_add_snapshot_prints_usage_when_parse_results_rest_insufficient(
    state_with_snapshot: ReplState, monkeypatch, capsys
) -> None:
    """Test that run_add_snapshot prints usage when results.rest has < 2 items.

    This covers the case where parse_flags consumes tokens as flags,
    leaving insufficient positional arguments.
    """
    # Mock parse_flags to return only one positional arg
    parse_result = FlagParseResult(rest=["only_one"], flags={"amount": "100"})
    parse_flags_mock = Mock(return_value=parse_result)
    monkeypatch.setattr(f"{MODULE}.parse_flags", parse_flags_mock)

    from portfotrack.cli.snapshot_cli.snapshot import run_add_snapshot

    run_add_snapshot(state_with_snapshot, args=["only_one", "--amount", "100"])

    captured = capsys.readouterr()
    assert "Usage: add-snapshot" in captured.out


def test_run_add_snapshot_happy_path_delegates_to_service(
    state_with_snapshot: ReplState, monkeypatch
) -> None:
    """Test that run_add_snapshot delegates to add_item_to_snapshot with correct args.

    Happy path: snapshot exists, sufficient args, valid flags.
    """
    # Mock parse_flags to return expected positional args and flags
    parse_result = FlagParseResult(
        rest=["asset_id_1", "label_1"], flags={"amount": "50000"}
    )
    parse_flags_mock = Mock(return_value=parse_result)
    monkeypatch.setattr(f"{MODULE}.parse_flags", parse_flags_mock)

    # Mock pop_required_int to return the amount as int
    pop_required_int_mock = Mock(return_value=50000)
    monkeypatch.setattr(f"{MODULE}.pop_required_int", pop_required_int_mock)

    # Mock add_item_to_snapshot to verify it's called correctly
    add_item_mock = Mock()
    monkeypatch.setattr(f"{MODULE}.add_item_to_snapshot", add_item_mock)

    from portfotrack.cli.snapshot_cli.snapshot import run_add_snapshot

    args_input = ["asset_id_1", "label_1", "--amount", "50000"]
    run_add_snapshot(state_with_snapshot, args_input)

    # Verify parse_flags was called with correct args and allowed flags
    parse_flags_mock.assert_called_once_with(args_input, allowed={"amount"})

    # Verify pop_required_int was called
    pop_required_int_mock.assert_called_once_with(parse_result.flags, "amount")

    # Verify add_item_to_snapshot was called with correct parameters
    add_item_mock.assert_called_once_with(
        state_with_snapshot.snapshot, "asset_id_1", "label_1", 50000
    )


@pytest.mark.parametrize(
    "asset_id,label,amount_str,amount_int",
    [
        ("cash", "krw_deposit", "1000000", 1000000),
        ("stocks", "stocks", "500000", 500000),
        ("bond", "bond_etf", "250000", 250000),
    ],
    ids=["cash", "stocks", "bond"],
)
def test_run_add_snapshot_parameterized_happy_paths(
    state_with_snapshot: ReplState,
    monkeypatch,
    asset_id: str,
    label: str,
    amount_str: str,
    amount_int: int,
) -> None:
    """Test run_add_snapshot with multiple valid input combinations.

    Parameterized test to ensure handler works correctly across
    different asset types and amounts.
    """
    parse_result = FlagParseResult(rest=[asset_id, label], flags={"amount": amount_str})
    parse_flags_mock = Mock(return_value=parse_result)
    monkeypatch.setattr(f"{MODULE}.parse_flags", parse_flags_mock)

    pop_required_int_mock = Mock(return_value=amount_int)
    monkeypatch.setattr(f"{MODULE}.pop_required_int", pop_required_int_mock)

    add_item_mock = Mock()
    monkeypatch.setattr(f"{MODULE}.add_item_to_snapshot", add_item_mock)

    from portfotrack.cli.snapshot_cli.snapshot import run_add_snapshot

    args_input = [asset_id, label, "--amount", amount_str]
    run_add_snapshot(state_with_snapshot, args_input)

    add_item_mock.assert_called_once_with(
        state_with_snapshot.snapshot, asset_id, label, amount_int
    )
