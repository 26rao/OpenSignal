"""Deadline parsing, normalization, and enrichment."""
from __future__ import annotations

import concurrent.futures
import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

# Standard browser headers for detail-page extraction
_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Regex patterns for explicit deadline phrases
_DEADLINE_PATTERNS = [
    re.compile(
        r"(?:application\s+deadline|submission\s+deadline|apply\s+by\s+deadline|entry\s+deadline|deadline|due\s+date|apply\s+by|closes?)\s*[:\s–\-]+\s*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"deadline\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:deadline|due|closes?)\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})",
        re.IGNORECASE,
    ),
]


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


def normalize_deadline(value: Any, today: Optional[date] = None) -> Optional[str]:
    """Normalize a deadline to ISO YYYY-MM-DD string, or None if unavailable/rolling."""
    d = parse_deadline(value, today=today)
    return d.isoformat() if d else None


def extract_deadline_from_text(text: Optional[str], today: Optional[date] = None) -> Optional[str]:
    """Extract an explicit application/submission deadline date from text/titles."""
    if not text:
        return None

    for pat in _DEADLINE_PATTERNS:
        match = pat.search(text)
        if match:
            raw_date = match.group(1).strip()
            # Clean ordinal suffixes like 15th -> 15
            cleaned = re.sub(r"(\d+)(?:st|nd|rd|th)", r"\1", raw_date)
            normalized = normalize_deadline(cleaned, today=today)
            if normalized:
                return normalized

    return None


def fetch_detail_page_deadline(url: str, timeout: float = 5.0) -> Optional[str]:
    """Fetch an opportunity detail page and extract an explicit deadline if present.

    Resilient to 403, 404, timeouts, and network errors without crashing.
    """
    if not url or not url.startswith("http"):
        return None

    try:
        resp = requests.get(url, headers=_HTTP_HEADERS, timeout=timeout)
        if resp.status_code == 200 and resp.text:
            return extract_deadline_from_text(resp.text)
    except Exception as exc:
        logger.debug("Detail page deadline fetch skipped for %s: %s", url, exc)

    return None


def enrich_opportunity_deadlines(
    records: List[Dict[str, Any]],
    max_workers: int = 5,
    today: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Enrich a batch of opportunities with normalized deadlines.

    Guarantees that every opportunity has:
    - title
    - deadline (normalized ISO YYYY-MM-DD string, or None)
    - location
    - organization
    - url
    """
    if not records:
        return []

    def _enrich_single(rec: Dict[str, Any]) -> Dict[str, Any]:
        item = dict(rec)
        # Ensure standard keys exist
        item.setdefault("title", None)
        item.setdefault("location", None)
        item.setdefault("organization", None)
        item.setdefault("url", None)

        raw_deadline = item.get("deadline")
        deadline = normalize_deadline(raw_deadline, today=today)

        # If not present in raw deadline field, try extracting from title
        if not deadline:
            deadline = extract_deadline_from_text(item.get("title"), today=today)

        # If still not found, try detail page enrichment
        if not deadline and item.get("url"):
            deadline = fetch_detail_page_deadline(str(item["url"]))

        item["deadline"] = deadline
        return item

    # Use ThreadPoolExecutor for fast, concurrent detail page lookups
    enriched: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_enrich_single, records))
        enriched.extend(results)

    return enriched


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

