"""Workflow orchestration facade maintaining strict separation of concerns."""
from __future__ import annotations

from .adjustment_flow import resolve_approved_adjustment
from .escalation_flow import escalate_rejection
from .payment_flow import process_incoming_payment, resolve_manager_rejection
from .state_machine import TRANSITIONS, transition, validate_period_open

__all__ = [
    "TRANSITIONS",
    "transition",
    "validate_period_open",
    "resolve_approved_adjustment",
    "escalate_rejection",
    "resolve_manager_rejection",
    "process_incoming_payment",
]
