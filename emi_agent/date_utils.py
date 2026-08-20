"""Date formatting utilities for spoken output."""

from __future__ import annotations

from datetime import datetime


def _ordinal(day: int) -> str:
    """Return day with ordinal suffix (1st, 2nd, 3rd, 4th, ..., 11th-13th, 21st, etc.)."""
    if 11 <= day % 100 <= 13:
        return f"{day}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def to_spoken_date(iso_date: str) -> str:
    """Convert YYYY-MM-DD to spoken format, e.g. '15th September 2026'.

    Args:
        iso_date: Date string in ISO format (``YYYY-MM-DD``).

    Returns:
        Human-readable spoken date string.
    """
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{_ordinal(dt.day)} {dt.strftime('%B')} {dt.year}"
