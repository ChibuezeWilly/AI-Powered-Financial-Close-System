"""Strict 15-state financial transition rules per Non-Negotiable #5 and #20."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schema.models import AccountingPeriod, FinancialTransaction

# Strict 15-state transition rules per Non-Negotiable #5
TRANSITIONS: dict[str, set[str]] = {
    "RECONCILED": {"DISCREPANCY_DETECTED"},
    "DISCREPANCY_DETECTED": {"INVESTIGATING", "FAILED"},
    "INVESTIGATING": {"AWAITING_HUMAN_APPROVAL", "RECONCILED", "FAILED"},
    "AWAITING_HUMAN_APPROVAL": {"APPROVED", "REJECTED", "FAILED"},
    "APPROVED": {"ADJUSTMENT_PENDING", "FAILED"},
    "ADJUSTMENT_PENDING": {"ADJUSTED", "FAILED"},
    "ADJUSTED": {"RESOLVED", "FAILED"},
    "REJECTED": {"ESCALATED", "PAYMENT_REQUESTED", "FAILED"},
    "ESCALATED": {"AWAITING_MANAGER_APPROVAL", "FAILED"},
    "AWAITING_MANAGER_APPROVAL": {"APPROVED", "REJECTED", "FAILED"},
    "PAYMENT_REQUESTED": {"PAYMENT_PENDING", "FAILED"},
    "PAYMENT_PENDING": {"PAYMENT_RECEIVED", "FAILED"},
    "PAYMENT_RECEIVED": {"RESOLVED", "FAILED"},
    "RESOLVED": set(),
    "FAILED": {"INVESTIGATING", "AWAITING_HUMAN_APPROVAL"},
}


def transition(transaction: FinancialTransaction, target: str) -> None:
    """Validate and execute a persisted financial status transition."""
    current = transaction.status
    allowed = TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Invalid financial-state transition: {current} → {target}",
        )
    transaction.status = target


def validate_period_open(db: Session, period_code: str) -> None:
    """Enforce Accounting Period Safety (Non-Negotiable #20)."""
    period = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == period_code))
    if not period or period.status != "OPEN":
        raise HTTPException(
            status_code=409,
            detail=f"Financial mutations are blocked for closed period '{period_code}'",
        )
