"""Tests for shared web date validation."""

import pytest

from portfotrack.web.date_validation import is_iso_date


@pytest.mark.parametrize("value", ["2024-02-29", "2026-12-31"])
def test_accepts_real_zero_padded_iso_dates(value: str) -> None:
    """Calendar-valid, zero-padded ISO dates are accepted."""
    assert is_iso_date(value) is True


@pytest.mark.parametrize(
    "value",
    ["2026-2-03", "not-a-date", "2026-02-30", "2025-02-29"],
)
def test_rejects_wrong_shape_and_impossible_calendar_dates(value: str) -> None:
    """Validation rejects both malformed and calendar-invalid values."""
    assert is_iso_date(value) is False
