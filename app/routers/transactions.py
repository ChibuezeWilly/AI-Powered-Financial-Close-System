from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..schema.models import AccountingPeriod, Approval, AuditEvent, FinancialTransaction, IdempotentAction, Investigation, JournalEntry
from .auth import DecisionUser, FinanceUser, ManagerUser, audit
from ..schemas import DecisionRequest, ManagerDecisionRequest
from ..services.reconciliation_graph import run_human_decision
from ..services.ai_investigation import investigate_transaction
from ..services.workflow import resolve_approved_adjustment, transition

router = APIRouter(prefix="/api/v1", tags=["financial-close"])
DOCUMENT_ROOT = Path(__file__).resolve().parents[2] / "documents" / "invoices"


def tx_payload(tx: FinancialTransaction) -> dict:
    return {
        "id": tx.id,
        "period": tx.period,
        "date": tx.transaction_date,
        "customer": tx.customer,
        "invoice_id": tx.invoice_id,
        "payment_id": tx.payment_id,
        "account": tx.account,
        "currency": tx.currency,
        "expected_amount": float(tx.expected_amount),
        "actual_amount": float(tx.actual_amount),
        "difference": float(tx.difference),
        "discrepancy_type": tx.discrepancy_type,
        "severity": tx.severity,
        "status": tx.status,
        "root_cause": tx.root_cause,
        "recommendation": tx.recommendation,
        "confidence": float(tx.confidence) if tx.confidence is not None else None,
    }


@router.get("/transactions")
def transactions(period: str, _: FinanceUser, db: Session = Depends(get_db)):
    return [
        tx_payload(tx)
        for tx in db.scalars(
            select(FinancialTransaction)
            .where(FinancialTransaction.period == period)
            .order_by(FinancialTransaction.transaction_date.desc())
        )
    ]


@router.get("/transactions/{transaction_id}")
def transaction_detail(transaction_id: str, _: FinanceUser, db: Session = Depends(get_db)):
    tx = db.get(FinancialTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    inv = db.scalar(select(Investigation).where(Investigation.transaction_id == transaction_id))
    journal = db.scalar(select(JournalEntry).where(JournalEntry.transaction_id == transaction_id))
    return {
        **tx_payload(tx),
        "investigation": (
            {
                "id": inv.id,
                "status": inv.status,
                "evidence": json.loads(inv.evidence),
                "timeline": json.loads(inv.timeline),
            }
            if inv
            else None
        ),
        "journal_entry": (
            {
                "id": journal.id,
                "amount": float(journal.amount),
                "status": journal.status,
                "debit": journal.debit_account,
                "credit": journal.credit_account,
            }
            if journal
            else None
        ),
        "evidence_graph": [
            "Customer",
            tx.customer,
            "Invoice",
            tx.invoice_id,
            "Payment",
            tx.payment_id,
            "Ledger",
            "Accounts Receivable",
            "Policy",
            "FIN-042",
            "Approval",
        ],
    }


@router.post("/transactions/{transaction_id}/investigate")
def investigate(transaction_id: str, user: DecisionUser, db: Session = Depends(get_db)):
    """Run AI analysis only; approvals and accounting actions remain separate."""
    tx = db.get(FinancialTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    try:
        result = investigate_transaction(db, tx)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI investigation failed; no financial state was changed") from exc
    audit(db, user.id, "AI_INVESTIGATION_COMPLETED", tx.id)
    db.commit()
    return result


@router.post("/transactions/{transaction_id}/decision")
def decide(
    transaction_id: str,
    payload: DecisionRequest,
    user: DecisionUser,
    request: Request,
    db: Session = Depends(get_db),
):
    tx = db.get(FinancialTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    accounting_period = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == tx.period))
    if not accounting_period or accounting_period.status != "OPEN":
        raise HTTPException(status_code=409, detail="Financial decisions are blocked for a closed accounting period")
    if tx.status != "AWAITING_HUMAN_APPROVAL":
        raise HTTPException(status_code=409, detail=f"Cannot decide a transaction in {tx.status}")
    key = request.headers.get("Idempotency-Key", f"{transaction_id}:{payload.decision}")
    prior = db.scalar(select(IdempotentAction).where(IdempotentAction.key == key))
    if prior:
        return json.loads(prior.result)
    db.add(
        Approval(
            transaction_id=tx.id,
            decision=payload.decision,
            reason=payload.reason,
            decided_by=user.id,
        )
    )
    inv = db.scalar(select(Investigation).where(Investigation.transaction_id == tx.id))
    result = run_human_decision(
        db=db,
        transaction=tx,
        actor_id=user.id,
        decision=payload.decision,
        reason=payload.reason,
        idempotency_key=key,
    )
    audit(db, user.id, f"TRANSACTION_{payload.decision.upper()}", tx.id)
    db.add(IdempotentAction(key=key, result=json.dumps(result)))
    db.commit()
    return result


@router.post("/transactions/{transaction_id}/manager-decision")
def manager_decide(
    transaction_id: str,
    payload: ManagerDecisionRequest,
    user: ManagerUser,
    db: Session = Depends(get_db),
):
    tx = db.get(FinancialTransaction, transaction_id)
    if not tx or tx.status != "AWAITING_MANAGER_APPROVAL":
        raise HTTPException(status_code=409, detail="No manager decision is pending")
    accounting_period = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == tx.period))
    if not accounting_period or accounting_period.status != "OPEN":
        raise HTTPException(status_code=409, detail="Financial decisions are blocked for a closed accounting period")
    db.add(
        Approval(
            transaction_id=tx.id,
            decision=f"manager_{payload.decision}",
            reason=payload.reason,
            decided_by=user.id,
        )
    )
    if payload.decision == "approved":
        transition(tx, "APPROVED")
        transition(tx, "ADJUSTMENT_PENDING")
        result = resolve_approved_adjustment(db, tx, f"manager:{tx.id}", user.id)
    else:
        tx.status = "REJECTED_MANAGER"
        transition(tx, "PAYMENT_REQUESTED")
        transition(tx, "PAYMENT_PENDING")
        result = {"status": tx.status, "message": "Receivable and payment request recorded"}
    audit(db, user.id, "MANAGER_DECISION", tx.id)
    db.commit()
    return result


@router.get("/transactions/{transaction_id}/audit")
def transaction_audit(transaction_id: str, _: FinanceUser, db: Session = Depends(get_db)):
    """Return persisted human decisions and system actions for a case."""
    if not db.get(FinancialTransaction, transaction_id):
        raise HTTPException(status_code=404, detail="Transaction not found")
    approvals = db.scalars(select(Approval).where(Approval.transaction_id == transaction_id).order_by(Approval.created_at)).all()
    events = db.scalars(select(AuditEvent).where(AuditEvent.subject == transaction_id).order_by(AuditEvent.created_at)).all()
    return {"approvals": [{"decision": a.decision, "reason": a.reason, "decided_by": a.decided_by, "created_at": a.created_at} for a in approvals], "events": [{"action": e.action, "actor_id": e.actor_id, "created_at": e.created_at} for e in events]}


@router.get("/evidence/{source_id}")
def evidence_document(source_id: str, _: FinanceUser):
    """Expose allow-listed source material, never arbitrary filesystem paths."""
    if not source_id.startswith("INV-"):
        raise HTTPException(status_code=404, detail="Evidence source not available")
    matches = list(DOCUMENT_ROOT.glob(f"{source_id.lower()}_*.md"))
    if not matches:
        raise HTTPException(status_code=404, detail="Document not found")
    document = matches[0]
    return {"source_id": source_id, "document": document.name, "page": 1, "content": document.read_text(encoding="utf-8")}
