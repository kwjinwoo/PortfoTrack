"""Shared validation for user-provided web date values."""

from datetime import date


def is_iso_date(value: str) -> bool:
    """Return whether a value is a real zero-padded ISO calendar date.

    Parsing rejects impossible dates such as February 30, while comparing the
    normalized representation preserves the exact ``YYYY-MM-DD`` web contract.

    Args:
        value: User-provided date text.

    Returns:
        True only for a valid calendar date in exact ISO date form.
    """
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value
