import pytest

from portfotrack.cli.parsing.errors import (
    DuplicatedFlagError,
    InvalidFlagError,
    MissingFlagValueError,
)
from portfotrack.cli.parsing.flags import parse_flags


def test_parse_flags_puts_non_flag_tokens_in_rest() -> None:
    tokens = ["foo", "bar"]
    results = parse_flags(tokens)

    assert results.flags == {}
    assert results.rest == ["foo", "bar"]


@pytest.mark.parametrize("tokens", [["--key", "value"], ["--key=value"]])
def test_parse_flags_parses_value_flag_both_forms(tokens: list[str]) -> None:
    results = parse_flags(tokens)

    assert results.flags == {"key": "value"}
    assert results.rest == []


def test_parse_flags_parses_boolean_flag_presence_as_true() -> None:
    tokens = ["--boolean"]
    results = parse_flags(tokens, boolean_flags={"boolean"})

    assert results.flags == {"boolean": True}
    assert results.rest == []


@pytest.mark.parametrize(
    "tokens, expected_value", [(["--boolean=true"], True), (["--boolean=false"], False)]
)
def test_parse_flags_parses_boolean_flag_assignment(
    tokens: list[str], expected_value: bool
) -> None:
    results = parse_flags(tokens, boolean_flags={"boolean"})

    assert results.flags == {"boolean": expected_value}
    assert results.rest == []


def test_parse_flags_keeps_positional_tokens_in_rest_while_parsing_flags() -> None:
    tokens = ["foo", "--name", "alice", "bar", "--verbose"]
    results = parse_flags(tokens, boolean_flags={"verbose"})

    assert results.flags == {"name": "alice", "verbose": True}
    assert results.rest == ["foo", "bar"]


def test_parse_flags_stops_parsing_at_double_dash_by_default() -> None:
    tokens = ["--name", "alice", "--", "--verbose", "x"]
    results = parse_flags(tokens, stop_at_double_dash=True)

    assert results.flags == {"name": "alice"}
    assert results.rest == ["--verbose", "x"]


def test_parse_flags_when_stop_at_double_dash_disabled_treats_double_dash_as_positional() -> (
    None
):
    tokens = ["--", "--name", "alice"]
    results = parse_flags(tokens, stop_at_double_dash=False)

    assert results.flags == {"name": "alice"}
    assert results.rest == ["--"]


def test_parse_flags_raises_duplicated_flag_error_on_duplicate_key() -> None:
    tokens = ["--name", "alice", "--name", "alice"]

    with pytest.raises(DuplicatedFlagError, match="CLI.DUPLICATED_FLAG"):
        _ = parse_flags(tokens)


def test_parse_flags_raises_invalid_flag_error_for_unknown_flag_when_disallowed() -> (
    None
):
    tokens = ["--unknown", "x"]

    with pytest.raises(InvalidFlagError, match="CLI.INVALID_FLAG"):
        _ = parse_flags(tokens, allowed={"name"}, allow_unknown=False)


def test_parse_flags_allows_unknown_flag_when_allow_unknown_true() -> None:
    tokens = ["--unknown", "x"]
    results = parse_flags(tokens, allowed={"name"}, allow_unknown=True)

    assert results.flags == {"unknown": "x"}
    assert results.rest == []


def test_parse_flags_allows_boolean_flag_not_in_allowed_set() -> None:
    tokens = ["--verbose"]
    results = parse_flags(tokens, allowed={"name"}, boolean_flags={"verbose"})

    assert results.flags == {"verbose": True}
    assert results.rest == []


def test_parse_flags_raises_missing_flag_value_when_value_looks_like_flag() -> None:
    tokens = ["--name", "--verbose"]

    with pytest.raises(MissingFlagValueError, match="CLI.MISSING_FLAG_VALUE"):
        _ = parse_flags(tokens)


def test_parse_flags_raises_missing_flag_value_error_when_value_is_missing() -> None:
    tokens = ["--name"]

    with pytest.raises(MissingFlagValueError, match="CLI.MISSING_FLAG_VALUE"):
        _ = parse_flags(tokens)


def test_parse_flags_raises_missing_flag_value_error_for_empty_equals_value() -> None:
    tokens = ["--name="]

    with pytest.raises(MissingFlagValueError, match="CLI.MISSING_FLAG_VALUE"):
        _ = parse_flags(tokens)


def test_parse_flags_treats_non_double_dash_tokens_as_positional() -> None:
    tokens = ["-x", "--name", "alice"]
    results = parse_flags(tokens)

    assert results.flags == {"name": "alice"}
    assert results.rest == ["-x"]
