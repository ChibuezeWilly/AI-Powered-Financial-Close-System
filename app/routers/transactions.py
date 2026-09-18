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
from ..services.investigation_queue import enqueue_investigation
from ..services.workflow import resolve_approved_adjustment, transition

router = APIRouter(prefix="/api/v1", tags=["financial-close"])
from sqlalchemy import or_, select

DOCUMENT_ROOT = Path(__file__).resolve().parents[2] / "documents" / "invoices"


def tx_payload(tx: FinancialTransaction) -> dict:
    computed_status = tx.status
    if hasattr(tx, "investigations") and tx.investigations:
        latest_inv = tx.investigations[-1]
        if latest_inv.status in {"PENDING", "RUNNING"}:
            computed_status = "INVESTIGATING"
    elif tx.status == "INVESTIGATING":
        computed_status = "INVESTIGATING"

    user_data = None
    if tx.user:
        user_data = {
            "id": tx.user.id,
            "full_name": tx.user.full_name,
            "email": tx.user.email,
            "role": tx.user.role,
        }

    invoice_data = None
    if tx.invoice:
        invoice_data = {
            "id": tx.invoice.id,
            "subtotal": float(tx.invoice.subtotal),
            "tax": float(tx.invoice.tax),
            "discount": float(tx.invoice.discount),
            "total": float(tx.invoice.total),
            "balance": float(tx.invoice.balance),
            "status": tx.invoice.status,
            "due_date": tx.invoice.due_date,
        }

    return {
        "id": tx.id,
        "period": tx.period,
        "date": tx.transaction_date,
        "customer": tx.customer,
        "customer_id": tx.customer_id,
        "user_id": tx.user_id,
        "user": user_data,
        "invoice_id": tx.invoice_id,
        "invoice": invoice_data,
        "payment_id": tx.payment_id,
        "bank_transaction_id": tx.bank_transaction_id,
        "account": tx.account,
        "currency": tx.currency,
        "expected_amount": float(tx.expected_amount),
        "actual_amount": float(tx.actual_amount),
        "difference": float(tx.difference),
        "discrepancy_type": tx.discrepancy_type,
        "severity": tx.severity,
        "status": computed_status,
        "root_cause": tx.root_cause,
        "recommendation": tx.recommendation,
        "confidence": float(tx.confidence) if tx.confidence is not None else None,
    }


@router.get("/transactions")
def transactions(period: str = "2026-09", q: str | None = None, _: FinanceUser = None, db: Session = Depends(get_db)):
    query = select(FinancialTransaction).where(FinancialTransaction.period == period)
    if q:
        pat = f"%{q}%"
        query = query.where(
            or_(
                FinancialTransaction.customer.ilike(pat),
                FinancialTransaction.invoice_id.ilike(pat),
                FinancialTransaction.id.ilike(pat),
                FinancialTransaction.account.ilike(pat),
            )
        )
    return [
        tx_payload(tx)
        for tx in db.scalars(query.order_by(FinancialTransaction.transaction_date.desc()))
    ]


@router.get("/transactions/{transaction_id}")
def transaction_detail(transaction_id: str, _: FinanceUser, db: Session = Depends(get_db)):
    tx = db.get(FinancialTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    inv = db.scalar(select(Investigation).where(Investigation.transaction_id == transaction_id).order_by(Investigation.created_at.desc()))
    journal = db.scalar(select(JournalEntry).where(JournalEntry.transaction_id == transaction_id))
    approvals = db.scalars(select(Approval).where(Approval.transaction_id == transaction_id).order_by(Approval.created_at)).all()
    ledger_entries = tx.ledger_entries if hasattr(tx, "ledger_entries") and tx.ledger_entries else []

    nodes = [
        {"id": "tx", "label": tx.id, "type": "transaction", "amount": float(tx.actual_amount)},
        {"id": "customer", "label": tx.customer, "type": "customer"},
        {"id": "account", "label": tx.account, "type": "account"},
    ]
    edges = [
        {"source": "customer", "target": "tx", "label": "INITIATED"},
        {"source": "tx", "target": "account", "label": "POSTED_TO"},
    ]
    if tx.invoice_id:
        nodes.append({"id": "invoice", "label": tx.invoice_id, "type": "invoice", "amount": float(tx.expected_amount)})
        edges.append({"source": "tx", "target": "invoice", "label": "FOR_INVOICE"})
    if tx.payment_id:
        nodes.append({"id": "payment", "label": tx.payment_id, "type": "payment"})
        edges.append({"source": "tx", "target": "payment", "label": "MATCHED_PAYMENT"})
    if tx.discrepancy_type:
        nodes.append({"id": "policy", "label": "FIN-042", "type": "policy", "name": "Discount Policy"})
        edges.append({"source": "tx", "target": "policy", "label": "GOVERNED_BY"})

    return {
        **tx_payload(tx),
        "investigation": (
            {
                "id": inv.id,
                "status": inv.status,
                "evidence": json.loads(inv.evidence or "[]"),
                "timeline": json.loads(inv.timeline or "[]"),
                "root_cause": inv.root_cause,
                "recommendation": inv.recommendation,
                "confidence": float(inv.confidence) if inv.confidence is not None else None,
                "ai_model": inv.ai_model,
                "completed_at": inv.completed_at,
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
        "ledger_entries": [
            {
                "id": le.id,
                "account_code": le.account_code,
                "account_name": le.account_name,
                "debit": float(le.debit),
                "credit": float(le.credit),
                "description": le.description,
                "reference": le.reference,
                "posted_date": le.posted_date,
            }
            for le in ledger_entries
        ],
        "approvals": [
            {
                "id": a.id,
                "decision": a.decision,
                "reason": a.reason,
                "decided_by": a.decided_by,
                "created_at": a.created_at,
            }
            for a in approvals
        ],
        "evidence_graph": {
            "nodes": nodes,
            "edges": edges,
        },
    }


@router.post("/transactions/{transaction_id}/investigate", status_code=202)
async def investigate(transaction_id: str, user: DecisionUser, db: Session = Depends(get_db)):
    """Queue AI analysis; approvals and accounting actions remain separate."""
    tx = db.get(FinancialTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx.status = "INVESTIGATING"
    investigation = db.scalar(select(Investigation).where(Investigation.transaction_id == tx.id))
    if not investigation:
        investigation = Investigation(
            id=f"INVG-{tx.id}",
            transaction_id=tx.id,
            status="PENDING",
            evidence="[]",
            timeline="[]",
        )
        db.add(investigation)
    investigation.status = "PENDING"
    audit(db, user.id, "AI_INVESTIGATION_QUEUED", tx.id)
    db.commit()
    try:
        job_id = await enqueue_investigation(tx.id)
    except Exception as exc:
        investigation.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=503, detail="Investigation queue is unavailable") from exc
    return {"transaction_id": tx.id, "status": "INVESTIGATING", "job_id": job_id}


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
    if not inv or inv.status != "COMPLETED":
        raise HTTPException(status_code=409, detail="Complete the AI investigation before submitting a financial decision")
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
    inv = db.scalar(select(Investigation).where(Investigation.transaction_id == tx.id))
    if not inv or inv.status != "COMPLETED":
        raise HTTPException(status_code=409, detail="Complete the AI investigation before submitting a financial decision")
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
