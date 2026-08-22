"""Deadline parsing and urgency sorting."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from dateutil import parser as date_parser


def parse_deadline(value: Any, today: Optional[date] = None) -> Optional[date]:
    """Best-effort parse. Returns None for rolling/unknown/empty values."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered in {"rolling", "ongoing", "open", "n/a", "na", "none", "null", "-"}:
        return None

    today = today or date.today()
    try:
        # If the string has no year, prefer "this year" over a far-future default.
        has_year = any(ch.isdigit() for ch in text) and (
            str(today.year) in text
            or str(today.year - 1) in text
            or str(today.year + 1) in text
            or any(y in text for y in (str(y) for y in range(2020, 2036)))
        )
        default = datetime(today.year if not has_year else 2099, 1, 1)
        dt = date_parser.parse(text, fuzzy=True, default=default)
        parsed = dt.date()
        # If we assumed this year and the date already passed by >60 days,
        # roll forward one year (common for "September 10" scraped mid-year).
        if not has_year and (today - parsed).days > 60:
            try:
                parsed = parsed.replace(year=parsed.year + 1)
            except ValueError:
                pass
        return parsed
    except (ValueError, OverflowError, TypeError):
        return None


def urgency_key(record: Dict[str, Any], today: Optional[date] = None) -> Tuple[int, date]:
    today = today or date.today()
    parsed = parse_deadline(record.get("deadline"), today=today)
    if parsed is None:
        return (1, date.max)
    return (0, parsed)


def sort_by_urgency(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(records, key=urgency_key)


def days_until(value: Any, today: Optional[date] = None) -> Optional[int]:
    today = today or date.today()
    parsed = parse_deadline(value, today=today)
    if parsed is None:
        return None
    return (parsed - today).days
