"""Core state machine engine for the EMI voice agent.

Design:
- A dispatch table (``_HANDLERS``) maps each ``CallState`` to a handler.
- Each handler receives ``(ctx, user_input)`` and returns ``(reply, next_state)``.
- ``run_step`` is the public single-turn API.
- ``run_call`` loops ``run_step`` over a sequence of inputs for batch / test use.
"""

from __future__ import annotations

from typing import Callable

from emi_agent.logger import log_transition
from emi_agent.models import (
    CallContext,
    CallState,
    CustomerIntent,
    IdentityResponse,
)
from emi_agent import templates


# ---------------------------------------------------------------------------
# Type alias for state handlers
# ---------------------------------------------------------------------------

# (ctx, user_input) -> (agent_reply, next_state)
StateHandler = Callable[[CallContext, str | None], tuple[str, CallState]]


# ---------------------------------------------------------------------------
# Individual state handlers
# ---------------------------------------------------------------------------

def _handle_identity_confirm(ctx: CallContext, user_input: str | None) -> tuple[str, CallState]:
    """IDENTITY_CONFIRM state handler.

    First call (user_input is None): emit the identity prompt.
    Subsequent calls: classify the response.
    """
    if user_input is None:
        # Opening turn — just ask the question
        return templates.identity_prompt(ctx.customer_name), CallState.IDENTITY_CONFIRM

    result = ctx.classify_identity(user_input)

    if result == IdentityResponse.CONFIRMED:
        return "", CallState.REMINDER_DELIVERY

    if result == IdentityResponse.DENIED:
        ctx.resolution = "WRONG_PERSON"
        return "I'm sorry for the inconvenience.", CallState.CLOSE

    # UNCLEAR
    ctx.identity_retries += 1
    if ctx.identity_retries <= 1:
        return templates.unclear_reprompt(), CallState.IDENTITY_CONFIRM
    else:
        ctx.resolution = "WRONG_PERSON"
        return "I was unable to confirm your identity.", CallState.CLOSE


def _handle_reminder_delivery(ctx: CallContext, _user_input: str | None) -> tuple[str, CallState]:
    """REMINDER_DELIVERY — auto-advance, no user input needed."""
    msg = templates.reminder_message(
        amount=ctx.emi_amount,
        date=ctx.due_date,
        account_last4=ctx.account_last4,
    )
    return msg, CallState.RESPONSE_HANDLING


def _handle_response(ctx: CallContext, user_input: str | None) -> tuple[str, CallState]:
    """RESPONSE_HANDLING — classify customer intent and branch."""
    if user_input is None:
        # Shouldn't happen in normal flow, but guard anyway
        return templates.unclear_reprompt(), CallState.RESPONSE_HANDLING

    intent = ctx.classify_intent(user_input)

    if intent == CustomerIntent.WILL_PAY:
        ctx.resolution = "WILL_PAY"
        reply = templates.will_pay_confirmation(ctx.emi_amount, ctx.due_date)
        return reply, CallState.CLOSE

    if intent == CustomerIntent.DISPUTE:
        ctx.resolution = "DISPUTE"
        ctx.dispute_logged = True
        reply = templates.dispute_acknowledgement()
        return reply, CallState.CLOSE

    if intent == CustomerIntent.RESCHEDULE:
        new_date = ctx.compute_reschedule_date(ctx.due_date)
        ctx.rescheduled_date = new_date
        ctx.resolution = "RESCHEDULE"
        reply = templates.reschedule_confirmation(new_date)
        return reply, CallState.CLOSE

    # UNCLEAR
    ctx.response_retries += 1
    if ctx.response_retries <= 1:
        return templates.unclear_reprompt(), CallState.RESPONSE_HANDLING
    else:
        ctx.resolution = "CALLBACK"
        return templates.call_back_note(), CallState.CLOSE


def _handle_close(ctx: CallContext, _user_input: str | None) -> tuple[str, CallState]:
    """CLOSE — read back summary and end."""
    summary = templates.close_summary(ctx)
    bye = templates.goodbye()
    return f"{summary} {bye}", CallState.ENDED


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_HANDLERS: dict[CallState, StateHandler] = {
    CallState.IDENTITY_CONFIRM: _handle_identity_confirm,
    CallState.REMINDER_DELIVERY: _handle_reminder_delivery,
    CallState.RESPONSE_HANDLING: _handle_response,
    CallState.CLOSE: _handle_close,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_step(ctx: CallContext, user_input: str | None = None) -> str:
    """Execute one turn of the state machine.

    Looks up the handler for ``ctx.state``, calls it, logs the transition
    (if state changed), advances ``ctx.state``, and returns the agent reply.

    Args:
        ctx: Mutable call context.
        user_input: The customer's text input (``None`` for auto-advance states).

    Returns:
        The agent's spoken reply for this turn.

    Raises:
        RuntimeError: If the call has already ended.
    """
    if ctx.state == CallState.ENDED:
        raise RuntimeError("Call has already ended.")

    handler = _HANDLERS[ctx.state]
    old_state = ctx.state
    reply, new_state = handler(ctx, user_input)

    if new_state != old_state:
        trigger = _build_trigger(old_state, new_state, user_input)
        log_transition(ctx, old_state, new_state, trigger)
        ctx.state = new_state

    return reply


def run_call(ctx: CallContext, inputs: list[str]) -> list[str]:
    """Run a full call, feeding *inputs* one at a time.

    Auto-advance states (REMINDER_DELIVERY, CLOSE) consume no input.
    Returns the list of all agent replies.
    """
    replies: list[str] = []
    input_iter = iter(inputs)

    # First turn: opening prompt (no user input yet)
    reply = run_step(ctx, user_input=None)
    replies.append(reply)

    for user_text in input_iter:
        # Feed user input to current state
        reply = run_step(ctx, user_input=user_text)
        if reply:
            replies.append(reply)

        # Auto-advance through states that don't need user input
        while ctx.state in {CallState.REMINDER_DELIVERY, CallState.CLOSE} and ctx.state != CallState.ENDED:
            reply = run_step(ctx)
            if reply:
                replies.append(reply)

        if ctx.state == CallState.ENDED:
            break

    return replies


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_trigger(old: CallState, new: CallState, user_input: str | None) -> str:
    """Build a human-readable trigger string for the transition log."""
    if user_input:
        return f"User said: \"{user_input}\""
    return f"Auto-advance from {old.value}"
