"""Stubbed intent classifiers — keyword-matching placeholders.

Replace these with LLM-based classifiers later.  The signatures match
the ``IdentityClassifier`` and ``IntentClassifier`` type aliases in
``models.py``, so any replacement is a drop-in swap.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from emi_agent.models import CustomerIntent, IdentityResponse


# ---------------------------------------------------------------------------
# Identity classification (stub)
# ---------------------------------------------------------------------------

_YES_KEYWORDS = {"yes", "yeah", "yep", "correct", "speaking", "that's me", "haan", "ha"}
_NO_KEYWORDS = {"no", "nope", "wrong", "not me", "nahi", "galat"}


def classify_identity(text: str) -> IdentityResponse:
    """Keyword-based identity confirmation.

    Returns CONFIRMED / DENIED / UNCLEAR based on simple keyword matching.
    """
    lowered = text.strip().lower()
    if any(kw in lowered for kw in _YES_KEYWORDS):
        return IdentityResponse.CONFIRMED
    if any(kw in lowered for kw in _NO_KEYWORDS):
        return IdentityResponse.DENIED
    return IdentityResponse.UNCLEAR


# ---------------------------------------------------------------------------
# Intent classification (stub)
# ---------------------------------------------------------------------------

_PAY_KEYWORDS = {"pay", "will pay", "paying", "okay", "sure", "fine", "i'll pay"}
_DISPUTE_KEYWORDS = {"wrong", "incorrect", "dispute", "not right", "error", "mistake"}
_RESCHEDULE_KEYWORDS = {"later", "reschedule", "next week", "postpone", "delay", "extend"}


def classify_intent(text: str) -> CustomerIntent:
    """Keyword-based intent classification for customer response.

    Returns WILL_PAY / DISPUTE / RESCHEDULE / UNCLEAR.
    """
    lowered = text.strip().lower()
    if any(kw in lowered for kw in _PAY_KEYWORDS):
        return CustomerIntent.WILL_PAY
    if any(kw in lowered for kw in _DISPUTE_KEYWORDS):
        return CustomerIntent.DISPUTE
    if any(kw in lowered for kw in _RESCHEDULE_KEYWORDS):
        return CustomerIntent.RESCHEDULE
    return CustomerIntent.UNCLEAR


# ---------------------------------------------------------------------------
# Reschedule date computation (stub)
# ---------------------------------------------------------------------------

def compute_reschedule_date(current_due: str) -> str:
    """Return a new due date 7 days after *current_due*.

    Args:
        current_due: ISO-format date string (``YYYY-MM-DD``).

    Returns:
        New date string in the same format.
    """
    dt = datetime.strptime(current_due, "%Y-%m-%d")
    new_dt = dt + timedelta(days=7)
    return new_dt.strftime("%Y-%m-%d")
