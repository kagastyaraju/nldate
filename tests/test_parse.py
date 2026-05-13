"""Tests for nldate.parse().

All tests pin `today` to a fixed Wednesday so that weekday arithmetic is
deterministic regardless of when the suite is run.
"""

from datetime import date

import pytest

from nldate import parse

# Fixed reference date: Wednesday 2025-05-14
TODAY = date(2025, 5, 14)


# ---------------------------------------------------------------------------
# Simple literals
# ---------------------------------------------------------------------------


def test_today() -> None:
    assert parse("today", today=TODAY) == TODAY


def test_tomorrow() -> None:
    assert parse("tomorrow", today=TODAY) == date(2025, 5, 15)


def test_yesterday() -> None:
    assert parse("yesterday", today=TODAY) == date(2025, 5, 13)


def test_day_after_tomorrow() -> None:
    assert parse("the day after tomorrow", today=TODAY) == date(2025, 5, 16)


def test_day_before_yesterday() -> None:
    assert parse("the day before yesterday", today=TODAY) == date(2025, 5, 12)


# ---------------------------------------------------------------------------
# Weekday expressions
# ---------------------------------------------------------------------------


def test_next_monday() -> None:
    # TODAY is Wednesday; next Monday = 5 days ahead
    assert parse("next Monday", today=TODAY) == date(2025, 5, 19)


def test_next_friday() -> None:
    # TODAY is Wednesday; next Friday = 2 days ahead
    assert parse("next Friday", today=TODAY) == date(2025, 5, 16)


def test_last_monday() -> None:
    # TODAY is Wednesday; last Monday = 2 days back
    assert parse("last Monday", today=TODAY) == date(2025, 5, 12)


def test_last_friday() -> None:
    # TODAY is Wednesday; last Friday = 5 days back
    assert parse("last Friday", today=TODAY) == date(2025, 5, 9)


def test_this_wednesday_is_today() -> None:
    # "this Wednesday" when today IS Wednesday → same day
    assert parse("this Wednesday", today=TODAY) == TODAY


def test_this_friday() -> None:
    # TODAY is Wednesday; this Friday = 2 days ahead
    assert parse("this Friday", today=TODAY) == date(2025, 5, 16)


def test_next_monday_when_today_is_monday() -> None:
    monday = date(2025, 5, 12)
    # "next Monday" when today is already Monday → following Monday
    assert parse("next Monday", today=monday) == date(2025, 5, 19)


def test_next_week() -> None:
    assert parse("next week", today=TODAY) == date(2025, 5, 21)


def test_last_week() -> None:
    assert parse("last week", today=TODAY) == date(2025, 5, 7)


# ---------------------------------------------------------------------------
# "in N units" → future
# ---------------------------------------------------------------------------


def test_in_3_days() -> None:
    assert parse("in 3 days", today=TODAY) == date(2025, 5, 17)


def test_in_two_weeks() -> None:
    assert parse("in two weeks", today=TODAY) == date(2025, 5, 28)


def test_in_1_year() -> None:
    assert parse("in 1 year", today=TODAY) == date(2026, 5, 14)


def test_in_3_months() -> None:
    assert parse("in 3 months", today=TODAY) == date(2025, 8, 14)


def test_in_1_year_and_2_months() -> None:
    assert parse("in 1 year and 2 months", today=TODAY) == date(2026, 7, 14)


# ---------------------------------------------------------------------------
# "N units ago" → past
# ---------------------------------------------------------------------------


def test_5_days_ago() -> None:
    assert parse("5 days ago", today=TODAY) == date(2025, 5, 9)


def test_a_week_ago() -> None:
    assert parse("a week ago", today=TODAY) == date(2025, 5, 7)


def test_2_months_ago() -> None:
    assert parse("2 months ago", today=TODAY) == date(2025, 3, 14)


def test_1_year_ago() -> None:
    assert parse("1 year ago", today=TODAY) == date(2024, 5, 14)


def test_one_year_ago() -> None:
    assert parse("one year ago", today=TODAY) == date(2024, 5, 14)


# ---------------------------------------------------------------------------
# "N units later / earlier"
# ---------------------------------------------------------------------------


def test_3_days_later() -> None:
    assert parse("3 days later", today=TODAY) == date(2025, 5, 17)


def test_2_weeks_earlier() -> None:
    assert parse("2 weeks earlier", today=TODAY) == date(2025, 4, 30)


# ---------------------------------------------------------------------------
# "N units from <anchor>"
# ---------------------------------------------------------------------------


def test_2_weeks_from_today() -> None:
    assert parse("2 weeks from today", today=TODAY) == date(2025, 5, 28)


def test_3_days_from_tomorrow() -> None:
    assert parse("3 days from tomorrow", today=TODAY) == date(2025, 5, 18)


def test_a_week_from_yesterday() -> None:
    assert parse("a week from yesterday", today=TODAY) == date(2025, 5, 20)


def test_3_months_from_now() -> None:
    assert parse("3 months from now", today=TODAY) == date(2025, 8, 14)


# ---------------------------------------------------------------------------
# "N units before/after <anchor>"
# ---------------------------------------------------------------------------


def test_5_days_before_absolute() -> None:
    assert parse("5 days before December 1st, 2025", today=TODAY) == date(2025, 11, 26)


def test_1_week_after_absolute() -> None:
    assert parse("1 week after January 1st, 2025", today=TODAY) == date(2025, 1, 8)


def test_1_year_and_2_months_after_yesterday() -> None:
    # yesterday = 2025-05-13; +1yr +2mo = 2026-07-13
    result = parse("1 year and 2 months after yesterday", today=TODAY)
    assert result == date(2026, 7, 13)


def test_3_days_before_next_monday() -> None:
    # next Monday from Wednesday 2025-05-14 = 2025-05-19; minus 3 = 2025-05-16
    assert parse("3 days before next Monday", today=TODAY) == date(2025, 5, 16)


def test_10_days_after_tomorrow() -> None:
    assert parse("10 days after tomorrow", today=TODAY) == date(2025, 5, 25)


def test_2_weeks_before_christmas() -> None:
    result = parse("2 weeks before December 25th, 2025", today=TODAY)
    assert result == date(2025, 12, 11)


# ---------------------------------------------------------------------------
# Absolute date strings
# ---------------------------------------------------------------------------


def test_iso_date() -> None:
    assert parse("2024-01-05", today=TODAY) == date(2024, 1, 5)


def test_month_day_year() -> None:
    assert parse("January 5th, 2024", today=TODAY) == date(2024, 1, 5)


def test_month_day_year_no_ordinal() -> None:
    assert parse("December 25, 2024", today=TODAY) == date(2024, 12, 25)


def test_abbreviated_month() -> None:
    assert parse("Dec 25, 2024", today=TODAY) == date(2024, 12, 25)


def test_today_default_param() -> None:
    """When today is not provided, parse() must not raise an exception."""
    result = parse("tomorrow")
    assert result == date.today() + __import__("datetime").timedelta(days=1)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_invalid_string_raises() -> None:
    with pytest.raises(ValueError):
        parse("not a date at all!!!", today=TODAY)
