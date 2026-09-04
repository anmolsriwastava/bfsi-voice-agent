"""End-to-end call-flow tests for the EMI voice agent state machine.

Three scenarios:
  (a) Clean will-pay path
  (b) Dispute path
  (c) Unclear / re-prompt → callback path
"""

from __future__ import annotations

import unittest

from emi_agent.intent import classify_identity, classify_intent, compute_reschedule_date
from emi_agent.models import CallContext, CallState
from emi_agent.state_machine import run_call


def _make_ctx() -> CallContext:
    """Create a fresh CallContext with sample loan data."""
    return CallContext(
        customer_name="Rahul Sharma",
        emi_amount=12500.00,
        due_date="2026-09-15",
        account_last4="4521",
        classify_identity=classify_identity,
        classify_intent=classify_intent,
        compute_reschedule_date=compute_reschedule_date,
    )


class TestCleanWillPayPath(unittest.TestCase):
    """(a) Customer confirms identity and says they will pay."""

    def test_full_flow(self) -> None:
        ctx = _make_ctx()
        inputs = ["yes", "I will pay"]
        replies = run_call(ctx, inputs)

        # --- State assertions ---
        self.assertEqual(ctx.state, CallState.ENDED)
        self.assertEqual(ctx.resolution, "WILL_PAY")

        # --- Transition count ---
        # IDENTITY_CONFIRM -> REMINDER_DELIVERY -> RESPONSE_HANDLING -> CLOSE -> ENDED
        self.assertEqual(len(ctx.transitions), 4)

        # --- Every record has a timestamp ---
        for record in ctx.transitions:
            self.assertIsNotNone(record.timestamp)

        # --- Trigger strings are human-readable ---
        for record in ctx.transitions:
            self.assertIsInstance(record.trigger, str)
            self.assertGreater(len(record.trigger), 0)

        # --- Replies contain key content ---
        full_text = " ".join(replies)
        self.assertIn("Rahul Sharma", full_text)         # identity prompt
        self.assertIn("4521", full_text)                   # account last 4
        self.assertIn("12,500.00", full_text)              # EMI amount
        self.assertIn("will pay", full_text.lower())       # confirmation


class TestDisputePath(unittest.TestCase):
    """(b) Customer confirms identity but disputes the charge."""

    def test_full_flow(self) -> None:
        ctx = _make_ctx()
        inputs = ["yes", "this is wrong, I dispute this"]
        replies = run_call(ctx, inputs)

        # --- State assertions ---
        self.assertEqual(ctx.state, CallState.ENDED)
        self.assertEqual(ctx.resolution, "DISPUTE")
        self.assertTrue(ctx.dispute_logged)

        # --- Transition count ---
        # IDENTITY_CONFIRM -> REMINDER_DELIVERY -> RESPONSE_HANDLING -> CLOSE -> ENDED
        self.assertEqual(len(ctx.transitions), 4)

        # --- Every record has a timestamp ---
        for record in ctx.transitions:
            self.assertIsNotNone(record.timestamp)

        # --- Replies mention dispute ---
        full_text = " ".join(replies)
        self.assertIn("dispute", full_text.lower())


class TestUnclearRepromptPath(unittest.TestCase):
    """(c) Customer confirms identity but gives unclear responses twice."""

    def test_full_flow(self) -> None:
        ctx = _make_ctx()
        # Two unclear inputs — first triggers re-prompt, second triggers callback
        inputs = ["yes", "hmm what?", "blah blah"]
        replies = run_call(ctx, inputs)

        # --- State assertions ---
        self.assertEqual(ctx.state, CallState.ENDED)
        self.assertEqual(ctx.resolution, "CALLBACK")

        # --- Transition count ---
        # IDENTITY_CONFIRM -> REMINDER_DELIVERY -> RESPONSE_HANDLING
        #   -> RESPONSE_HANDLING (retry, same state so no transition logged)
        #   -> CLOSE -> ENDED
        # Wait — re-prompt stays in RESPONSE_HANDLING (no state change), so:
        # IDENTITY -> REMINDER (1) -> RESPONSE (2) -> CLOSE (3) -> ENDED (4)
        # But the unclear re-prompt does NOT change state, so no extra transition.
        # However on second unclear it goes RESPONSE -> CLOSE.
        # Total: 4 transitions
        self.assertEqual(len(ctx.transitions), 4)

        # --- Every record has a timestamp ---
        for record in ctx.transitions:
            self.assertIsNotNone(record.timestamp)

        # --- Retry counter was used ---
        self.assertGreaterEqual(ctx.response_retries, 2)

        # --- Summary mentions callback ---
        full_text = " ".join(replies)
        self.assertIn("call you back", full_text.lower())


if __name__ == "__main__":
    unittest.main()
