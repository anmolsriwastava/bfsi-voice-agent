"""Transition logger — every state change is recorded with a timestamp."""

from __future__ import annotations

import sys
from datetime import datetime

from emi_agent.models import CallContext, CallState, TransitionRecord


def log_transition(
    ctx: CallContext,
    from_state: CallState,
    to_state: CallState,
    trigger: str,
) -> None:
    """Append a timestamped transition record and print to stderr.

    Args:
        ctx: The mutable call context.
        from_state: State we are leaving.
        to_state: State we are entering.
        trigger: Human-readable reason for the transition.
    """
    record = TransitionRecord(
        timestamp=datetime.now(),
        from_state=from_state,
        to_state=to_state,
        trigger=trigger,
    )
    ctx.transitions.append(record)

    # Structured log line to stderr (won't interfere with agent text output)
    print(
        f"[TRANSITION] {record.timestamp.isoformat()} "
        f"{from_state.value} -> {to_state.value} | {trigger}",
        file=sys.stderr,
    )


def dump_log(ctx: CallContext) -> list[dict[str, str]]:
    """Serialise the full transition history to a list of dicts.

    Useful for JSON export or evidence/reproducibility writeups.
    """
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "from_state": r.from_state.value,
            "to_state": r.to_state.value,
            "trigger": r.trigger,
        }
        for r in ctx.transitions
    ]
