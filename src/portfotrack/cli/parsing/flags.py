from collections.abc import Iterator
from dataclasses import dataclass

from portfotrack.cli.parsing.errors import (
    DuplicatedFlagError,
    InvalidFlagError,
    InvalidValueTypeError,
    MissingFlagValueError,
)


@dataclass(slots=True)
class FlagParseResult:
    """Parsed representation of CLI-style flags.

    This is the return type of `parse_flags()`. It contains a mapping of
    parsed `--key` flags (without the leading dashes) and any remaining
    positional tokens that were not interpreted as flags.

    Attributes:
        flags: Mapping of parsed flag keys to their values. Keys never
            include the leading `--`. Values are `True` for boolean flags,
            booleans for `--bool=...` forms, or strings for value flags.
        rest: Positional tokens that were not parsed as flags. This may
            include tokens that appear after a `--` delimiter when
            `stop_at_double_dash=True`.
    """

    flags: dict[str, object]
    rest: list[str]


def parse_flags(
    tokens: list[str],
    *,
    allowed: set[str] | None = None,
    boolean_flags: set[str] | None = None,
    allow_unknown: bool = False,
    stop_at_double_dash: bool = True,
) -> FlagParseResult:
    """Parse CLI-style `--key` flags from a token list.

    Supported forms:
      - `--key value` (consumes one additional token)
      - `--key=value`
      - `--bool-flag` (boolean presence flag)
      - `--bool-flag=true|false|1|0|...` (boolean assignment)

    Tokens that are not flags (do not start with `--`, or are exactly `--`)
    are preserved in `rest`. If `stop_at_double_dash=True`, a standalone
    `--` ends flag parsing and all remaining tokens are appended to `rest`
    verbatim.

    Validation behavior:
      - If `allowed` is provided and `allow_unknown=False`, then any flag
        not listed in `allowed` or `boolean_flags` raises `InvalidFlagError`.
      - Duplicate flags raise `DuplicatedFlagError`.
      - Missing values for non-boolean flags raise `MissingFlagValueError`.

    Args:
        tokens: Tokenized CLI arguments (e.g., `sys.argv[1:]`).
        allowed: Allowed non-boolean flag names (without leading dashes).
            If `None` or empty, no allowlist validation is enforced unless
            `allow_unknown=False` and `allowed` is non-empty.
        boolean_flags: Flag names that are treated as booleans. Presence
            (e.g., `--verbose`) yields `True`. Assignment (e.g.,
            `--verbose=false`) is parsed into a boolean.
        allow_unknown: Whether to allow flags not present in `allowed` /
            `boolean_flags`. When `False` and `allowed` is non-empty,
            unknown flags raise `InvalidFlagError`.
        stop_at_double_dash: Whether a standalone `--` terminates flag
            parsing and treats the remainder as positional tokens.

    Returns:
        A `FlagParseResult` containing parsed flags and remaining tokens.

    Raises:
        DuplicatedFlagError: If the same flag key appears more than once.
        InvalidFlagError: If a flag token is malformed or not allowed by
            the allowlist policy.
        MissingFlagValueError: If a non-boolean flag is missing its value,
            or if a boolean assignment cannot be parsed.
    """
    allowed = allowed or set()
    boolean_flags = boolean_flags or set()

    flags: dict[str, object] = {}
    rest: list[str] = []

    it = iter(tokens)
    for tok in it:
        if stop_at_double_dash and tok == "--":
            rest.extend(list(it))
            break

        if not tok.startswith("--") or tok == "--":
            rest.append(tok)
            continue

        key, value = parse_single_flag(
            tok,
            it,
            allowed=allowed,
            boolean_flags=boolean_flags,
            allow_unknown=allow_unknown,
        )

        if key in flags:
            raise DuplicatedFlagError(flag=key)

        flags[key] = value

    return FlagParseResult(flags=flags, rest=rest)


def parse_single_flag(
    tok: str,
    it: Iterator[str],
    *,
    allowed: set[str],
    boolean_flags: set[str],
    allow_unknown: bool,
) -> tuple[str, object]:
    """Parse a single flag token into a `(key, value)` pair.

    This function handles both `--key=value` and `--key value` forms. For
    the space-separated form, it may consume one additional token from the
    iterator.

    Boolean flags behave as follows:
      - `--flag` returns `(flag, True)`
      - `--flag=true|false|1|0|...` returns `(flag, <bool>)`

    Non-boolean flags require a value:
      - `--key=value` requires a non-empty value string
      - `--key value` requires the next token and rejects another flag token
        as the value (e.g., `--key --other`).

    Args:
        tok: A token expected to start with `--` (e.g., `--name` or
            `--name=alice`).
        it: Iterator over remaining tokens. May be advanced by one element
            when parsing the `--key value` form.
        allowed: Allowed non-boolean flag keys (without leading dashes).
        boolean_flags: Set of boolean flag keys (without leading dashes).
        allow_unknown: Whether to allow keys not present in `allowed` /
            `boolean_flags`.

    Returns:
        A tuple `(key, value)` where `key` does not include leading dashes.

    Raises:
        InvalidFlagError: If the token is malformed (e.g., `--` or `--=x`),
            or the key is not permitted by the allowlist policy.
        MissingFlagValueError: If a required value is missing, the value
            token looks like another flag, or a boolean assignment value
            is not parseable.
    """
    body = tok[2:]
    if not body:
        raise InvalidFlagError(
            flag="--",
            reason="A flag name is required after '--'.",
        )

    # --key=value
    if "=" in body:
        key, value = body.split("=", 1)
        if not key:
            raise InvalidFlagError(
                flag=tok,
                reason="Missing flag name before '='.",
            )
        _validate_key(key, allowed, boolean_flags, allow_unknown)

        if key in boolean_flags:
            return key, _parse_bool(value, key=key)

        if value == "":
            raise MissingFlagValueError(flag=key)

        return key, value

    # --key  or --bool-flag
    key = body
    _validate_key(key, allowed, boolean_flags, allow_unknown)

    if key in boolean_flags:
        return key, True

    # --key value
    try:
        value = next(it)
    except StopIteration as e:
        raise MissingFlagValueError(flag=key, cause=e) from e

    if value.startswith("--") and value != "--":
        raise MissingFlagValueError(flag=key, value=value)

    return key, value


def _validate_key(
    key: str,
    allowed: set[str],
    boolean_flags: set[str],
    allow_unknown: bool,
) -> None:
    """Validate that a parsed key is permitted under the allowlist policy.

    If `allowed` is empty, this function performs no validation. Otherwise,
    when `allow_unknown=False`, the key must be present in either `allowed`
    or `boolean_flags`.

    Args:
        key: Flag key without leading dashes.
        allowed: Allowed non-boolean keys.
        boolean_flags: Allowed boolean keys.
        allow_unknown: Whether to allow keys not present in `allowed` /
            `boolean_flags`.

    Raises:
        InvalidFlagError: If the key is not allowed.
    """
    if (
        allowed
        and not allow_unknown
        and key not in allowed
        and key not in boolean_flags
    ):
        raise InvalidFlagError(flag=key)


def _parse_bool(raw: str, *, key: str) -> bool:
    """Parse a boolean flag assignment value.

    Accepted truthy values (case-insensitive, surrounding whitespace ignored):
    `1, true, t, yes, y, on`

    Accepted falsy values:
    `0, false, f, no, n, off`

    Args:
        raw: Raw value string to parse (e.g., from `--flag=<raw>`).
        key: Flag key (without leading dashes), used for error context.

    Returns:
        The parsed boolean value.

    Raises:
        MissingFlagValueError: If `raw` is not one of the accepted boolean
            tokens.
    """
    v = raw.strip().lower()
    if v in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise MissingFlagValueError(flag=key, value=v)


def pop_required_float(flags: dict[str, object], key: str) -> float:
    """Pop and return a required float flag value.

    This function retrieves the value associated with `key` from the given
    flags dictionary, validates that it is present and convertible to `float`,
    and removes it from the dictionary.

    Args:
        flags: Dictionary of parsed CLI flags. This dictionary is mutated by
            removing the consumed flag.
        key: Flag name (without leading `--`) to retrieve.

    Returns:
        The flag value converted to `float`.

    Raises:
        MissingFlagValueError: If the flag is missing or its value is an empty
            string.
        InvalidValueTypeError: If the flag value cannot be converted to a
            float.

    """
    s = pop_required_str(flags, key)
    try:
        return float(s)
    except ValueError as e:
        raise InvalidValueTypeError(
            flag=key, required_type="float", wrong_value=s
        ) from e


def pop_required_str(flags: dict[str, object], key: str) -> str:
    """Pop and return a required string flag value.

    This function retrieves the value associated with `key` from the given
    flags dictionary, validates that it is a non-empty string, and removes
    it from the dictionary.

    Args:
        flags: Dictionary of parsed CLI flags. This dictionary is mutated by
            removing the consumed flag.
        key: Flag name (without leading `--`) to retrieve.

    Returns:
        The non-empty string value of the flag.

    Raises:
        MissingFlagValueError: If the flag is missing or its value is an empty
            string.
        InvalidValueTypeError: If the flag value is not a string.

    """
    if key not in flags:
        raise MissingFlagValueError(flag=key)
    v = flags.pop(key)
    if not isinstance(v, str):
        raise InvalidValueTypeError(flag=key, required_type="string")
    if v == "":
        raise MissingFlagValueError(flag=key)
    return v
