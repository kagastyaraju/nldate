"""Natural-language date parsing implementation."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta

# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

WEEKDAY_NAMES: dict[str, int] = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

UNIT_MAP: dict[str, str] = {
    "day": "days",
    "days": "days",
    "week": "weeks",
    "weeks": "weeks",
    "month": "months",
    "months": "months",
    "year": "years",
    "years": "years",
}

NUMBER_WORDS: dict[str, int] = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_int(s: str) -> int | None:
    """Convert a token to an integer (digit string or number word)."""
    s = s.strip()
    if s.isdigit():
        return int(s)
    return NUMBER_WORDS.get(s)


def _parse_delta(s: str) -> relativedelta | None:
    """
    Parse a duration string such as:
      "5 days"
      "1 year and 2 months"
      "3 weeks, 4 days"
      "two weeks"
      "a month"
    Returns None if parsing fails.
    """
    # Normalise "," and "and" separators to a single sentinel
    s = re.sub(r",\s*and\s+|,\s*|\s+and\s+", " AND ", s.strip())
    parts = [p.strip() for p in s.split(" AND ") if p.strip()]

    kwargs: dict[str, int] = {}

    for part in parts:
        m = re.match(r"^(\w+)\s+(\w+s?)$", part)
        if not m:
            return None
        n = _to_int(m.group(1))
        if n is None:
            return None
        unit_raw = m.group(2).lower()
        unit = UNIT_MAP.get(unit_raw)
        if unit is None:
            return None
        kwargs[unit] = kwargs.get(unit, 0) + n

    if not kwargs:
        return None
    return relativedelta(**kwargs)  # type: ignore[arg-type]


def _parse_weekday_prefix(s: str, today: date) -> date | None:
    """
    Handle:
      "next <weekday>", "last <weekday>", "this <weekday>"
      "<weekday>" (bare → treated as next occurrence)
      "next week", "last week"
    """
    s = s.strip().lower()

    # next/last/this week (not a specific weekday)
    if s == "next week":
        return today + timedelta(weeks=1)
    if s == "last week":
        return today - timedelta(weeks=1)
    if s == "next month":
        return today + relativedelta(months=1)
    if s == "last month":
        return today - relativedelta(months=1)
    if s == "next year":
        return today + relativedelta(years=1)
    if s == "last year":
        return today - relativedelta(years=1)

    for prefix in ("next ", "last ", "this "):
        if s.startswith(prefix):
            day_name = s[len(prefix) :].strip()
            if day_name not in WEEKDAY_NAMES:
                return None
            target = WEEKDAY_NAMES[day_name]
            current = today.weekday()
            if prefix == "next ":
                days_ahead = (target - current) % 7 or 7
                return today + timedelta(days=days_ahead)
            elif prefix == "last ":
                days_behind = (current - target) % 7 or 7
                return today - timedelta(days=days_behind)
            else:  # "this "
                days_ahead = (target - current) % 7
                return today + timedelta(days=days_ahead)

    # Bare weekday name → next occurrence
    if s in WEEKDAY_NAMES:
        target = WEEKDAY_NAMES[s]
        current = today.weekday()
        days_ahead = (target - current) % 7 or 7
        return today + timedelta(days=days_ahead)

    return None


def _parse_anchor(s: str, today: date) -> date | None:
    """
    Parse an anchor date which may itself be a relative expression or an
    absolute date.  Returns None if it cannot be parsed.
    """
    s_lower = s.strip().lower()

    # Simple literals
    if s_lower in ("today", "now"):
        return today
    if s_lower == "tomorrow":
        return today + timedelta(days=1)
    if s_lower == "yesterday":
        return today - timedelta(days=1)
    if s_lower in ("the day after tomorrow", "day after tomorrow"):
        return today + timedelta(days=2)
    if s_lower in ("the day before yesterday", "day before yesterday"):
        return today - timedelta(days=2)

    # Weekday expressions
    wd = _parse_weekday_prefix(s_lower, today)
    if wd is not None:
        return wd

    # Absolute date via dateutil (case-insensitive, handles ordinals)
    try:
        default = datetime(today.year, today.month, today.day)
        return dateutil_parser.parse(s, default=default).date()
    except (ValueError, OverflowError):
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse(s: str, today: date | None = None) -> date:
    """
    Parse a natural-language date string and return a ``datetime.date``.

    Parameters
    ----------
    s:
        A natural-language date expression, e.g.:
        ``"today"``, ``"tomorrow"``, ``"next Tuesday"``,
        ``"5 days before December 1st, 2025"``,
        ``"1 year and 2 months after yesterday"``.
    today:
        The reference date for relative expressions.  Defaults to
        ``datetime.date.today()``.

    Returns
    -------
    datetime.date
    """
    if today is None:
        today = date.today()

    s_orig = s.strip()
    s_lower = s_orig.lower()

    # ------------------------------------------------------------------
    # Simple literals
    # ------------------------------------------------------------------
    if s_lower == "today":
        return today
    if s_lower == "tomorrow":
        return today + timedelta(days=1)
    if s_lower == "yesterday":
        return today - timedelta(days=1)
    if s_lower in ("the day after tomorrow", "day after tomorrow"):
        return today + timedelta(days=2)
    if s_lower in ("the day before yesterday", "day before yesterday"):
        return today - timedelta(days=2)

    # ------------------------------------------------------------------
    # Weekday / week / month / year prefix expressions
    # ------------------------------------------------------------------
    wd = _parse_weekday_prefix(s_lower, today)
    if wd is not None:
        return wd

    # ------------------------------------------------------------------
    # "in N unit[s]" → future from today
    # ------------------------------------------------------------------
    m = re.fullmatch(r"in\s+(.+)", s_lower)
    if m:
        delta = _parse_delta(m.group(1))
        if delta is not None:
            return today + delta

    # ------------------------------------------------------------------
    # "N unit[s] ago" → past from today
    # ------------------------------------------------------------------
    m = re.fullmatch(r"(.+?)\s+ago", s_lower)
    if m:
        delta = _parse_delta(m.group(1))
        if delta is not None:
            return today - delta

    # ------------------------------------------------------------------
    # "N unit[s] later" / "N unit[s] from now" → future from today
    # ------------------------------------------------------------------
    m = re.fullmatch(r"(.+?)\s+later", s_lower)
    if m:
        delta = _parse_delta(m.group(1))
        if delta is not None:
            return today + delta

    m = re.fullmatch(r"(.+?)\s+earlier", s_lower)
    if m:
        delta = _parse_delta(m.group(1))
        if delta is not None:
            return today - delta

    # ------------------------------------------------------------------
    # "N unit[s] from <anchor>"  (also handles "from now/today")
    # ------------------------------------------------------------------
    m = re.fullmatch(r"(.+?)\s+from\s+(.+)", s_lower)
    if m:
        delta = _parse_delta(m.group(1))
        if delta is not None:
            anchor = _parse_anchor(m.group(2), today)
            if anchor is not None:
                return anchor + delta

    # ------------------------------------------------------------------
    # "N unit[s] after <anchor>"
    # ------------------------------------------------------------------
    # Must be tried *before* "before" to avoid partial overlap.
    m = re.fullmatch(r"(.+?)\s+after\s+(.+)", s_lower)
    if m:
        delta = _parse_delta(m.group(1))
        if delta is not None:
            anchor = _parse_anchor(m.group(2), today)
            if anchor is not None:
                return anchor + delta

    # ------------------------------------------------------------------
    # "N unit[s] before <anchor>"
    # ------------------------------------------------------------------
    m = re.fullmatch(r"(.+?)\s+before\s+(.+)", s_lower)
    if m:
        delta = _parse_delta(m.group(1))
        if delta is not None:
            anchor = _parse_anchor(m.group(2), today)
            if anchor is not None:
                return anchor - delta

    # ------------------------------------------------------------------
    # Absolute date – fall back to dateutil (handles ISO, month names, etc.)
    # ------------------------------------------------------------------
    try:
        default = datetime(today.year, today.month, today.day)
        return dateutil_parser.parse(s_orig, default=default).date()
    except (ValueError, OverflowError):
        pass

    raise ValueError(f"Cannot parse date string: {s!r}")
