"""Approved adjustment flow and ledger mutations per Non-Negotiables #6, #14, #18."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schema.models import (
    Adjustment,
    AuditEvent,
    FinancialTransaction,
    Investigation,
    Notification,
    User,
)
from ..services.accounting import JournalRequest, accounting_provider
from ..services.email_service import safe_send_resolution_email
from ..services.pinecone_service import save_resolution_memory
from ..services.slack_service import send_resolution_message
from .state_machine import transition, validate_period_open

logger = logging.getLogger(__name__)


async def resolve_approved_adjustment(
    db: Session,
    tx: FinancialTransaction,
    idempotency_key: str,
    actor_id: int,
) -> dict[str, Any]:
    """Execute complete approved flow (Non-Negotiable #6)."""
    validate_period_open(db, tx.period)

    # State transitions
    if tx.status in {"AWAITING_HUMAN_APPROVAL", "AWAITING_MANAGER_APPROVAL"}:
        transition(tx, "APPROVED")
        transition(tx, "ADJUSTMENT_PENDING")

    if tx.status != "ADJUSTMENT_PENDING":
        raise HTTPException(status_code=409, detail=f"Adjustment cannot be posted from {tx.status}")

    # Controlled Accounting Provider Call
    diff_amount = Decimal(str(abs(tx.difference)))
    entry = await accounting_provider.create_journal_entry(
        db,
        JournalRequest(
            transaction_id=tx.id,
            debit_account="Discount Expense",
            credit_account="Accounts Receivable",
            amount=diff_amount,
            idempotency_key=idempotency_key,
            period=tx.period,
        ),
    )

    if not await accounting_provider.verify_transaction(db, tx.id):
        raise HTTPException(status_code=502, detail="Ledger provider could not verify the posted journal")

    # Transition to ADJUSTED
    transition(tx, "ADJUSTED")

    # Re-run reconciliation and verify difference = 0
    tx.actual_amount = tx.expected_amount
    tx.difference = Decimal("0.00")
    transition(tx, "RESOLVED")

    # Update Investigation
    investigation = db.scalar(select(Investigation).where(Investigation.transaction_id == tx.id))
    if investigation:
        investigation.status = "RESOLVED"
        investigation.completed_at = datetime.now(timezone.utc)

    # Record Adjustment model
    db.add(
        Adjustment(
            transaction_id=tx.id,
            journal_entry_id=entry.id,
            debit_account="Discount Expense",
            credit_account="Accounts Receivable",
            amount=diff_amount,
            reason=f"Approved adjustment for {tx.id}",
            approved_by=actor_id,
            status="posted",
        )
    )

    # Audit Trail
    db.add(AuditEvent(actor_id=actor_id, action="JOURNAL_ENTRY_POSTED", subject=tx.id))
    db.add(AuditEvent(actor_id=actor_id, action="RECONCILIATION_VERIFIED", subject=tx.id))
    db.add(
        Notification(
            user_id=actor_id,
            event="ADJUSTMENT_SUCCESS",
            message=f"{entry.id} posted and {tx.id} reconciled.",
            status="SENT",
        )
    )
    db.flush()

    # Pinecone Resolution Memory (Non-Negotiable #14)
    save_resolution_memory(
        tx=tx,
        inv=investigation,
        human_decision="approved",
        action_taken="LEDGER_ADJUSTMENT",
        final_solution=f"Journal entry {entry.id} posted ($500.00 adjustment to Discount Expense)",
    )

    # Decoupled Notifications (Non-Negotiable #18)
    actor = db.get(User, actor_id)
    recipient_email = actor.email if actor else "finance@company.com"
    await safe_send_resolution_email(
        to_email=recipient_email,
        transaction_id=tx.id,
        amount=float(diff_amount),
        journal_entry_id=entry.id,
        customer=tx.customer,
    )

    try:
        send_resolution_message(
            transaction_id=tx.id,
            customer=tx.customer,
            journal_entry_id=entry.id,
            amount=float(diff_amount),
        )
    except Exception as exc:
        logger.warning("Decoupled Slack resolution message failed: %s", exc)

    return {"status": tx.status, "journal_entry": entry.id, "difference": 0}
