"""Core data models and enums for the EMI voice agent."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CallState(enum.Enum):
    """Explicit states in the call flow."""

    IDENTITY_CONFIRM = "IDENTITY_CONFIRM"
    REMINDER_DELIVERY = "REMINDER_DELIVERY"
    RESPONSE_HANDLING = "RESPONSE_HANDLING"
    CLOSE = "CLOSE"
    ENDED = "ENDED"


class IdentityResponse(enum.Enum):
    """Possible outcomes of the identity-confirmation step."""

    CONFIRMED = "CONFIRMED"
    DENIED = "DENIED"
    UNCLEAR = "UNCLEAR"


class CustomerIntent(enum.Enum):
    """Customer intent during the response-handling step."""

    WILL_PAY = "WILL_PAY"
    DISPUTE = "DISPUTE"
    RESCHEDULE = "RESCHEDULE"
    UNCLEAR = "UNCLEAR"


# ---------------------------------------------------------------------------
# Transition record (immutable once created)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TransitionRecord:
    """A single logged state transition with a timestamp."""

    timestamp: datetime
    from_state: CallState
    to_state: CallState
    trigger: str  # human-readable reason for the transition


# ---------------------------------------------------------------------------
# Classifier protocol types (for dependency injection)
# ---------------------------------------------------------------------------

IdentityClassifier = Callable[[str], IdentityResponse]
IntentClassifier = Callable[[str], CustomerIntent]
RescheduleDateFn = Callable[[str], str]


# ---------------------------------------------------------------------------
# Call context — the single mutable object threaded through the call
# ---------------------------------------------------------------------------

@dataclass
class CallContext:
    """Mutable state for one call session."""

    # Customer & loan info
    customer_name: str
    emi_amount: float
    due_date: str          # ISO format "YYYY-MM-DD"
    account_last4: str     # last 4 digits of loan account

    # Pluggable classifiers (swap for LLM-based versions later)
    classify_identity: IdentityClassifier
    classify_intent: IntentClassifier
    compute_reschedule_date: RescheduleDateFn

    # Runtime state
    state: CallState = CallState.IDENTITY_CONFIRM
    identity_retries: int = 0
    response_retries: int = 0
    resolution: str = ""          # populated by RESPONSE_HANDLING
    rescheduled_date: str = ""    # populated only on RESCHEDULE
    dispute_logged: bool = False

    # Audit trail
    transitions: list[TransitionRecord] = field(default_factory=list)
