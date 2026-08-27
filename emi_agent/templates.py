"""Deterministic script templates — pure functions, no LLM calls.

Every function here takes structured data and returns a spoken-style string.
These are fully testable in isolation.
"""

from __future__ import annotations

from emi_agent.date_utils import to_spoken_date

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from emi_agent.models import CallContext


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

def identity_prompt(customer_name: str) -> str:
    """Opening line: confirm who we're speaking with."""
    return f"Am I speaking with {customer_name}?"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def to_spoken_currency_hindi(amount: float) -> str:
    """Format currency for Hindi/Hinglish TTS, avoiding the ₹ symbol.
    Removes decimal places if they are .00 to sound natural.
    e.g., 12500.00 -> "12,500 rupaye"
    """
    if amount.is_integer():
        return f"{int(amount):,} rupaye"
    return f"{amount:,.2f} rupaye"


# ---------------------------------------------------------------------------
# Reminder delivery
# ---------------------------------------------------------------------------

def reminder_message(amount: float, date: str, account_last4: str) -> str:
    """Build a spoken-style EMI reminder from structured data.

    Args:
        amount: EMI amount (e.g. 12500.00).
        date: Due date in ISO format (YYYY-MM-DD) — converted to spoken style internally.
        account_last4: Last 4 digits of the loan account.

    Returns:
        A deterministic, spoken-style reminder string.
    """
    formatted_amount = f"\u20b9{amount:,.2f}"  # ₹12,500.00
    spoken_date = to_spoken_date(date)
    return (
        f"This is a reminder for your loan account ending in {account_last4}. "
        f"Your EMI of {formatted_amount} is due on {spoken_date}. "
        f"Please ensure timely payment to avoid any late fees."
    )


# ---------------------------------------------------------------------------
# Response-handling replies
# ---------------------------------------------------------------------------

def will_pay_confirmation(amount: float, date: str) -> str:
    formatted_amount = f"\u20b9{amount:,.2f}"
    spoken_date = to_spoken_date(date)
    return (
        f"Thank you for confirming. We have noted that you will make the "
        f"payment of {formatted_amount} by {spoken_date}."
    )


def dispute_acknowledgement() -> str:
    return (
        "I understand you have a concern regarding this amount. "
        "Your dispute has been noted and our team will review it. "
        "You will receive an update within 3 business days."
    )


def reschedule_offer(new_date: str) -> str:
    spoken = to_spoken_date(new_date)
    return (
        f"We can reschedule your payment to {spoken}. "
        f"Shall I confirm this new date for you?"
    )


def reschedule_confirmation(new_date: str) -> str:
    return f"Your payment has been rescheduled to {to_spoken_date(new_date)}."


# ---------------------------------------------------------------------------
# Re-prompt & fallback
# ---------------------------------------------------------------------------

def unclear_reprompt() -> str:
    return "I'm sorry, I didn't quite catch that. Could you please repeat?"


def call_back_note() -> str:
    return (
        "I wasn't able to get a clear response. "
        "We will call you back at a more convenient time."
    )


# ---------------------------------------------------------------------------
# Close & goodbye
# ---------------------------------------------------------------------------

def close_summary(ctx: "CallContext") -> str:
    """Build a summary of what was agreed during the call."""
    lines = [f"To summarize this call with {ctx.customer_name}:"]

    if ctx.resolution == "WILL_PAY":
        formatted = f"\u20b9{ctx.emi_amount:,.2f}"
        spoken_date = to_spoken_date(ctx.due_date)
        lines.append(
            f"You have confirmed that you will pay {formatted} by {spoken_date}."
        )
    elif ctx.resolution == "DISPUTE":
        lines.append(
            "Your dispute has been logged and will be reviewed by our team."
        )
    elif ctx.resolution == "RESCHEDULE":
        lines.append(
            f"Your payment has been rescheduled to {to_spoken_date(ctx.rescheduled_date)}."
        )
    elif ctx.resolution == "CALLBACK":
        lines.append(
            "We were unable to reach a resolution. We will call you back."
        )
    elif ctx.resolution == "WRONG_PERSON":
        lines.append(
            "This call was ended as we could not confirm your identity."
        )
    else:
        lines.append("No resolution was reached.")

    return " ".join(lines)


def goodbye() -> str:
    return "Thank you for your time. Have a good day!"
