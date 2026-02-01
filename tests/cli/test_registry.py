from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from portfotrack.cli.errors import InvalidCommandError
from portfotrack.cli.registry import CommandRegistry, CommandSpec
from portfotrack.cli.state import ReplState


@pytest.fixture()
def dummy_state() -> ReplState:
    return ReplState()


def test_command_spec_default_help_and_frozen() -> None:
    handler = Mock()
    spec = CommandSpec(name="help", handler=handler)

    assert spec.help == ""

    with pytest.raises(FrozenInstanceError):
        # frozen=True should prevent mutation
        spec.name = "mutated"  # type: ignore[misc]


def test_register_success_then_list_contains_command() -> None:
    reg = CommandRegistry()
    handler = Mock()
    spec = CommandSpec(name="add-asset", handler=handler, help="Add an asset")

    reg.register(spec)

    cmds = reg.list_commands()
    assert len(cmds) == 1
    assert cmds[0].name == "add-asset"
    assert cmds[0].handler is handler
    assert cmds[0].help == "Add an asset"


def test_register_duplicate_name_raises_value_error() -> None:
    reg = CommandRegistry()
    reg.register(CommandSpec(name="help", handler=Mock()))
    with pytest.raises(ValueError) as e:
        reg.register(CommandSpec(name="help", handler=Mock()))

    # Optional: message contract
    assert "Duplicated command name" in str(e.value)
    assert "help" in str(e.value)


@pytest.mark.parametrize("raw", ["", "   ", "\t\t", "\n"])
def test_dispatch_empty_or_whitespace_is_noop(raw: str, dummy_state: ReplState) -> None:
    reg = CommandRegistry()
    handler = Mock()
    reg.register(CommandSpec(name="help", handler=handler))

    reg.dispatch(raw=raw, state=dummy_state)  # should not raise
    handler.assert_not_called()


@pytest.mark.parametrize(
    "raw, expected_args",
    [
        ("help", []),
        ("add-asset AAPL Apple growth", ["AAPL", "Apple", "growth"]),
        ("add-asset   AAPL\tApple   growth", ["AAPL", "Apple", "growth"]),
    ],
)
def test_dispatch_calls_registered_handler_with_args(
    raw: str, expected_args: list[str], dummy_state: ReplState
) -> None:
    reg = CommandRegistry()
    state = dummy_state

    help_handler = Mock()
    add_handler = Mock()

    reg.register(CommandSpec(name="help", handler=help_handler))
    reg.register(CommandSpec(name="add-asset", handler=add_handler))

    reg.dispatch(raw=raw, state=state)

    cmd = raw.split()[0]
    if cmd == "help":
        help_handler.assert_called_once_with(state, expected_args)
        add_handler.assert_not_called()
    else:
        add_handler.assert_called_once_with(state, expected_args)
        help_handler.assert_not_called()


def test_dispatch_unknown_command_raises_invalid_command_error(
    dummy_state: ReplState,
) -> None:
    reg = CommandRegistry()
    reg.register(CommandSpec(name="help", handler=Mock()))

    with pytest.raises(InvalidCommandError) as e:
        reg.dispatch(raw="unknown", state=dummy_state)

    # Optional: if your InvalidCommandError sets details["command"]
    exc = e.value
    details = getattr(exc, "details", {})
    if isinstance(details, dict):
        assert details.get("command") == "unknown"


def test_dispatch_propagates_handler_exception(dummy_state: ReplState) -> None:
    reg = CommandRegistry()

    def boom(_state: object, _args: list[str]) -> None:
        raise RuntimeError("boom")

    reg.register(CommandSpec(name="boom", handler=boom))

    with pytest.raises(RuntimeError, match="boom"):
        reg.dispatch(raw="boom", state=dummy_state)


def test_list_commands_sorted_by_name() -> None:
    reg = CommandRegistry()
    reg.register(CommandSpec(name="z", handler=Mock()))
    reg.register(CommandSpec(name="a", handler=Mock()))
    reg.register(CommandSpec(name="m", handler=Mock()))

    names = [c.name for c in reg.list_commands()]
    assert names == ["a", "m", "z"]


def test_list_commands_returns_copy_not_live_view() -> None:
    reg = CommandRegistry()
    reg.register(CommandSpec(name="a", handler=Mock()))
    reg.register(CommandSpec(name="b", handler=Mock()))

    cmds = reg.list_commands()
    cmds.clear()

    names = [c.name for c in reg.list_commands()]
    assert names == ["a", "b"]
