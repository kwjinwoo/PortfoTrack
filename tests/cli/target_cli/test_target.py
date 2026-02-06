from unittest.mock import Mock

import pytest

from portfotrack.cli.parsing.flags import FlagParseResult
from portfotrack.cli.state import ReplState
from portfotrack.domain.target_allocation import TargetAllocation

MODULE = "portfotrack.cli.target_cli.target"

USAGE = "Usage: add-asset <id> <name> <purpose> --ratio <r> --lower <l> --upper <u>"


# ---------------------------
# Fixtures
# ---------------------------


@pytest.fixture()
def empty_target() -> TargetAllocation:
    # TargetAllocation is cheap and pure; safe to instantiate directly
    return TargetAllocation()


@pytest.fixture()
def state_without_target() -> ReplState:
    return ReplState(target=None)


@pytest.fixture()
def state_with_target(empty_target: TargetAllocation) -> ReplState:
    return ReplState(target=empty_target)


# ---------------------------
# run_init_target
# ---------------------------


def test_run_init_target_sets_state_target_and_prints(monkeypatch, capsys) -> None:
    sentinel_target = TargetAllocation()
    init_target_mock = Mock(return_value=sentinel_target)
    monkeypatch.setattr(f"{MODULE}.init_target", init_target_mock)

    state = ReplState(target=None)

    from portfotrack.cli.target_cli.target import run_init_target

    run_init_target(state, args=[])

    assert state.target is sentinel_target
    init_target_mock.assert_called_once_with()

    out = capsys.readouterr().out
    assert "Target initialized." in out


def test_run_init_target_ignores_args(
    monkeypatch, capsys, empty_target: TargetAllocation
) -> None:
    sentinel_target = TargetAllocation()
    init_target_mock = Mock(return_value=sentinel_target)
    monkeypatch.setattr(f"{MODULE}.init_target", init_target_mock)

    state = ReplState(target=empty_target)

    from portfotrack.cli.target_cli.target import run_init_target

    run_init_target(state, args=["foo", "--bar"])

    assert state.target is sentinel_target

    out = capsys.readouterr().out
    assert "Target initialized." in out


# ---------------------------
# run_add_asset
# ---------------------------


def test_run_add_asset_no_target_prints_guard_message(
    monkeypatch, capsys, state_without_target: ReplState
) -> None:
    parse_flags_mock = Mock()
    add_asset_to_target_mock = Mock()
    monkeypatch.setattr(f"{MODULE}.parse_flags", parse_flags_mock)
    monkeypatch.setattr(f"{MODULE}.add_asset_to_target", add_asset_to_target_mock)

    from portfotrack.cli.target_cli.target import run_add_asset

    run_add_asset(
        state_without_target,
        args=[
            "A1",
            "Apple",
            "growth",
            "--ratio",
            "0.2",
            "--lower",
            "0.1",
            "--upper",
            "0.3",
        ],
    )

    out = capsys.readouterr().out
    assert "No target. Run `init-target` first." in out
    parse_flags_mock.assert_not_called()
    add_asset_to_target_mock.assert_not_called()


@pytest.mark.parametrize("args", [[], ["A1"], ["A1", "Apple"]])
def test_run_add_asset_len_args_lt_3_prints_usage_and_returns(
    monkeypatch, capsys, state_with_target: ReplState, args: list[str]
) -> None:
    parse_flags_mock = Mock()
    add_asset_to_target_mock = Mock()
    monkeypatch.setattr(f"{MODULE}.parse_flags", parse_flags_mock)
    monkeypatch.setattr(f"{MODULE}.add_asset_to_target", add_asset_to_target_mock)

    from portfotrack.cli.target_cli.target import run_add_asset

    run_add_asset(state_with_target, args=args)

    out = capsys.readouterr().out
    assert USAGE in out
    parse_flags_mock.assert_not_called()
    add_asset_to_target_mock.assert_not_called()


@pytest.mark.parametrize(
    "rest",
    [
        [],  # 0
        ["A1", "Apple"],  # 2
        ["A1", "Apple", "growth", "extra"],  # 4
    ],
)
def test_run_add_asset_rest_len_not_3_prints_usage_and_returns(
    monkeypatch, capsys, state_with_target: ReplState, rest: list[str]
) -> None:
    # len(args) must be >= 3 to get past the early guard.
    args = [
        "dummy1",
        "dummy2",
        "dummy3",
        "--ratio",
        "0.2",
        "--lower",
        "0.1",
        "--upper",
        "0.3",
    ]

    parse_flags_mock = Mock(
        return_value=FlagParseResult(
            flags={"ratio": "0.2", "lower": "0.1", "upper": "0.3"}, rest=rest
        )
    )
    pop_required_float_mock = Mock(return_value=0.0)
    add_asset_to_target_mock = Mock()

    monkeypatch.setattr(f"{MODULE}.parse_flags", parse_flags_mock)
    monkeypatch.setattr(f"{MODULE}.pop_required_float", pop_required_float_mock)
    monkeypatch.setattr(f"{MODULE}.add_asset_to_target", add_asset_to_target_mock)

    from portfotrack.cli.target_cli.target import run_add_asset

    run_add_asset(state_with_target, args=args)

    out = capsys.readouterr().out
    assert USAGE in out

    parse_flags_mock.assert_called_once()
    pop_required_float_mock.assert_not_called()
    add_asset_to_target_mock.assert_not_called()


def test_run_add_asset_happy_path_calls_service_and_prints(
    monkeypatch, capsys, state_with_target: ReplState
) -> None:
    # Deterministic parse result
    parse_flags_mock = Mock(
        return_value=Mock(
            flags={"ratio": "0.2", "lower": "0.15", "upper": "0.25"},
            rest=["A1", "Apple", "growth"],
        )
    )
    monkeypatch.setattr(f"{MODULE}.parse_flags", parse_flags_mock)

    # Make pop_required_float behave like the real one (consume + cast)
    def _pop_required_float(flags: dict[str, object], key: str) -> float:
        v = flags.pop(key)
        assert isinstance(v, str)
        return float(v)

    monkeypatch.setattr(f"{MODULE}.pop_required_float", _pop_required_float)

    add_asset_to_target_mock = Mock()
    monkeypatch.setattr(f"{MODULE}.add_asset_to_target", add_asset_to_target_mock)

    from portfotrack.cli.target_cli.target import run_add_asset

    run_add_asset(
        state_with_target,
        args=[
            "A1",
            "Apple",
            "growth",
            "--ratio",
            "0.2",
            "--lower",
            "0.15",
            "--upper",
            "0.25",
        ],
    )

    add_asset_to_target_mock.assert_called_once_with(
        state_with_target.target,
        "A1",
        "Apple",
        "growth",
        0.2,
        0.15,
        0.25,
    )

    out = capsys.readouterr().out
    assert "Asset added." in out


@pytest.mark.parametrize("missing_key", ["ratio", "lower", "upper"])
def test_run_add_asset_missing_required_flag_raises_and_does_not_call_service(
    monkeypatch, capsys, state_with_target: ReplState, missing_key: str
) -> None:
    # Use real pop_required_float to assert "policy: exception is propagated"
    from portfotrack.cli.errors import MissingFlagValueError
    from portfotrack.cli.parsing.flags import pop_required_float

    flags: dict[str, object] = {"ratio": "0.2", "lower": "0.1", "upper": "0.3"}
    flags.pop(missing_key)

    parse_flags_mock = Mock(
        return_value=Mock(flags=flags, rest=["A1", "Apple", "growth"])
    )
    monkeypatch.setattr(f"{MODULE}.parse_flags", parse_flags_mock)
    monkeypatch.setattr(f"{MODULE}.pop_required_float", pop_required_float)

    add_asset_to_target_mock = Mock()
    monkeypatch.setattr(f"{MODULE}.add_asset_to_target", add_asset_to_target_mock)

    from portfotrack.cli.target_cli.target import run_add_asset

    with pytest.raises(MissingFlagValueError):
        run_add_asset(
            state_with_target,
            args=[
                "A1",
                "Apple",
                "growth",
                "--ratio",
                "0.2",
                "--lower",
                "0.1",
                "--upper",
                "0.3",
            ],
        )

    add_asset_to_target_mock.assert_not_called()
    out = capsys.readouterr().out
    assert "Asset added." not in out


def test_run_add_asset_invalid_float_raises_and_does_not_call_service(
    monkeypatch, capsys, state_with_target: ReplState
) -> None:
    from portfotrack.cli.errors import InvalidValueTypeError
    from portfotrack.cli.parsing.flags import pop_required_float

    parse_flags_mock = Mock(
        return_value=Mock(
            flags={"ratio": "foo", "lower": "0.1", "upper": "0.3"},
            rest=["A1", "Apple", "growth"],
        )
    )
    monkeypatch.setattr(f"{MODULE}.parse_flags", parse_flags_mock)
    monkeypatch.setattr(f"{MODULE}.pop_required_float", pop_required_float)

    add_asset_to_target_mock = Mock()
    monkeypatch.setattr(f"{MODULE}.add_asset_to_target", add_asset_to_target_mock)

    from portfotrack.cli.target_cli.target import run_add_asset

    with pytest.raises(InvalidValueTypeError):
        run_add_asset(
            state_with_target,
            args=[
                "A1",
                "Apple",
                "growth",
                "--ratio",
                "foo",
                "--lower",
                "0.1",
                "--upper",
                "0.3",
            ],
        )

    add_asset_to_target_mock.assert_not_called()
    out = capsys.readouterr().out
    assert "Asset added." not in out


def test_run_add_asset_unknown_flag_raises(state_with_target: ReplState) -> None:
    # This one intentionally does NOT mock parse_flags to verify allowed={"ratio","lower","upper"} integration.
    from portfotrack.cli.errors import InvalidFlagError
    from portfotrack.cli.target_cli.target import run_add_asset

    with pytest.raises(InvalidFlagError):
        run_add_asset(
            state_with_target,
            args=[
                "A1",
                "Apple",
                "growth",
                "--wat",
                "1",
                "--ratio",
                "0.2",
                "--lower",
                "0.1",
                "--upper",
                "0.3",
            ],
        )


# ---------------------------
# register_target_commands
# ---------------------------


def test_register_target_commands_registers_four_commands() -> None:
    registry = Mock()

    from portfotrack.cli.target_cli.target import (
        register_target_commands,
        run_add_asset,
        run_init_target,
        run_load_target,
        run_save_target,
    )

    register_target_commands(registry)

    assert registry.register.call_count == 4

    first_spec = registry.register.call_args_list[0].args[0]
    second_spec = registry.register.call_args_list[1].args[0]
    third_spec = registry.register.call_args_list[2].args[0]
    fourth_spec = registry.register.call_args_list[3].args[0]

    assert first_spec.name == "init-target"
    assert first_spec.handler is run_init_target
    assert first_spec.help == "Initialize target allocation"

    assert second_spec.name == "add-asset"
    assert second_spec.handler is run_add_asset
    assert second_spec.help == "Add asset to the active target"

    assert third_spec.name == "save-target"
    assert third_spec.handler is run_save_target
    assert third_spec.help == "Save current target allocation"

    assert fourth_spec.name == "load-target"
    assert fourth_spec.handler is run_load_target
    assert fourth_spec.help == "Load latest target allocation"
