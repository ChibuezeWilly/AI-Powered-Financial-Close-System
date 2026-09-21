"""Finance admin rejection and manager escalation flow per Non-Negotiables #7 & #11."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schema.models import (
    ApprovalRequest,
    AuditEvent,
    FinancialTransaction,
    Investigation,
    ManagerEscalation,
    Notification,
)
from ..services.slack_service import send_escalation_message
from .state_machine import transition, validate_period_open

logger = logging.getLogger(__name__)


def escalate_rejection(
    db: Session,
    tx: FinancialTransaction,
    actor_id: int,
    reason: str,
) -> dict[str, Any]:
    """Execute finance admin rejection and manager escalation (Non-Negotiable #7 & #11)."""
    validate_period_open(db, tx.period)

    transition(tx, "REJECTED")
    transition(tx, "ESCALATED")
    transition(tx, "AWAITING_MANAGER_APPROVAL")

    investigation = db.scalar(select(Investigation).where(Investigation.transaction_id == tx.id))
    if investigation:
        investigation.status = "ESCALATED"

    # Save manager approval request
    db.add(
        ApprovalRequest(
            transaction_id=tx.id,
            requested_by=actor_id,
            approver_role="FINANCE_MANAGER",
            status="pending",
        )
    )
    db.add(AuditEvent(actor_id=actor_id, action="MANAGER_APPROVAL_REQUESTED", subject=tx.id))
    db.add(
        Notification(
            user_id=None,
            event="MANAGER_ESCALATION",
            message=f"Decision required for {tx.id}: {reason}",
            status="PENDING",
        )
    )

    # Send Rich Slack escalation message with buttons (Non-Negotiable #11)
    try:
        slack_result = send_escalation_message(
            transaction_id=tx.id,
            customer=tx.customer,
            amount=float(abs(tx.difference)),
            reason=reason,
            invoice_id=tx.invoice_id,
            discrepancy_type=tx.discrepancy_type,
            root_cause=tx.root_cause or (investigation.root_cause if investigation else None),
            evidence_summary=investigation.evidence if investigation else None,
            recommendation=tx.recommendation or (investigation.recommendation if investigation else None),
        )
        if slack_result:
            db.add(
                ManagerEscalation(
                    transaction_id=tx.id,
                    escalated_by=actor_id,
                    reason=reason,
                    slack_message_id=slack_result.get("message_id"),
                    slack_channel=slack_result.get("channel"),
                    status="pending",
                )
            )
    except Exception as exc:
        logger.warning("Decoupled Slack escalation failed: %s", exc)

    return {"status": tx.status, "message": "Escalated to Finance Manager"}
