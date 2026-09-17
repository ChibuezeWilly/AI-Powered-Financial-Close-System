"""Persisted state transitions for human-controlled reconciliation resolution."""
from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..schema.models import AuditEvent, FinancialTransaction, Investigation, Notification
from .accounting import JournalRequest, accounting_provider

TRANSITIONS = {
    "AWAITING_HUMAN_APPROVAL": {"APPROVED", "REJECTED"},
    "REJECTED": {"ESCALATED"},
    "ESCALATED": {"AWAITING_MANAGER_APPROVAL"},
    "AWAITING_MANAGER_APPROVAL": {"APPROVED", "REJECTED"},
    "APPROVED": {"ADJUSTMENT_PENDING"},
    "ADJUSTMENT_PENDING": {"ADJUSTED"},
    "ADJUSTED": {"RESOLVED"},
    "REJECTED_MANAGER": {"PAYMENT_REQUESTED"},
    "PAYMENT_REQUESTED": {"PAYMENT_PENDING"},
    "PAYMENT_PENDING": {"PAYMENT_RECEIVED"},
    "PAYMENT_RECEIVED": {"RESOLVED"},
}


def transition(transaction: FinancialTransaction, target: str) -> None:
    current = transaction.status
    allowed = TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(status_code=409, detail=f"Invalid financial-state transition: {current} → {target}")
    transaction.status = target


def resolve_approved_adjustment(db: Session, tx: FinancialTransaction, idempotency_key: str, actor_id: int) -> dict:
    if tx.status == "AWAITING_HUMAN_APPROVAL":
        transition(tx, "APPROVED")
        transition(tx, "ADJUSTMENT_PENDING")
    if tx.status != "ADJUSTMENT_PENDING":
        raise HTTPException(status_code=409, detail=f"Adjustment cannot be posted from {tx.status}")
    entry = accounting_provider.create_journal_entry(
        db,
        JournalRequest(tx.id, "Discount Expense", "Accounts Receivable", Decimal(str(abs(tx.difference))), idempotency_key),
    )
    if not accounting_provider.verify_transaction(db, tx.id):
        raise HTTPException(status_code=502, detail="Ledger provider could not verify the posted journal")
    transition(tx, "ADJUSTED")
    tx.actual_amount = tx.expected_amount
    tx.difference = Decimal("0.00")
    transition(tx, "RESOLVED")
    investigation = db.query(Investigation).filter(Investigation.transaction_id == tx.id).first()
    if investigation:
        investigation.status = "RESOLVED"
    db.add(AuditEvent(actor_id=actor_id, action="JOURNAL_ENTRY_POSTED", subject=tx.id))
    db.add(AuditEvent(actor_id=actor_id, action="RECONCILIATION_VERIFIED", subject=tx.id))
    db.add(Notification(user_id=actor_id, event="ADJUSTMENT_SUCCESS", message=f"{entry.id} posted and {tx.id} reconciled.", status="SENT"))
    return {"status": tx.status, "journal_entry": entry.id, "difference": 0}


def escalate_rejection(db: Session, tx: FinancialTransaction, actor_id: int, reason: str) -> dict:
    transition(tx, "REJECTED")
    transition(tx, "ESCALATED")
    transition(tx, "AWAITING_MANAGER_APPROVAL")
    investigation = db.query(Investigation).filter(Investigation.transaction_id == tx.id).first()
    if investigation:
        investigation.status = "ESCALATED"
    db.add(AuditEvent(actor_id=actor_id, action="MANAGER_APPROVAL_REQUESTED", subject=tx.id))
    db.add(Notification(user_id=None, event="MANAGER_ESCALATION", message=f"Decision required for {tx.id}: {reason}", status="PENDING"))

    # Send Slack escalation notification
    try:
        from .slack_service import send_escalation_message
        slack_result = send_escalation_message(
            transaction_id=tx.id,
            customer=tx.customer,
            amount=float(abs(tx.difference)),
            reason=reason,
            invoice_id=tx.invoice_id,
        )
        if slack_result:
            from ..schema.models import ManagerEscalation
            db.add(ManagerEscalation(
                transaction_id=tx.id,
                escalated_by=actor_id,
                reason=reason,
                slack_message_id=slack_result.get("message_id"),
                slack_channel=slack_result.get("channel"),
                status="pending",
            ))
    except Exception:
        pass  # Slack is non-critical; don't block the workflow

    return {"status": tx.status, "message": "Escalated to Finance Manager"}
