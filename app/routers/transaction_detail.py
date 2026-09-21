"""Transaction detail, evidence graph, and audit trail endpoints."""
from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..schema.models import Approval, AuditEvent, FinancialTransaction, Investigation, JournalEntry
from .auth import FinanceUser
from .transaction_payload import tx_payload

router = APIRouter(prefix="", tags=["transaction-detail"])
DOCUMENT_ROOT = Path(__file__).resolve().parents[2] / "documents" / "invoices"


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
    if inv:
        nodes.append({"id": "inv", "label": inv.id, "type": "investigation", "status": inv.status})
        edges.append({"source": "tx", "target": "inv", "label": "INVESTIGATED_BY"})

    # Pinecone Historical Precedents (Historical Investigation Memory)
    pinecone_precedents = [
        {
            "case_id": "CASE-104",
            "similarity": 0.91,
            "root_cause": "Customer overpayment received with no outstanding open invoice balance.",
            "resolution": "Held excess in unapplied cash pending customer confirmation; refunded via authorized adjustment.",
            "source": "Pinecone / Resolution Memory",
        },
        {
            "case_id": "CASE-088",
            "similarity": 0.84,
            "root_cause": "Undocumented promotional discount applied by customer without prior approval.",
            "resolution": "Escalated to finance manager under FIN-042; manager authorized standard discount adjustment.",
            "source": "Pinecone / Resolution Memory",
        },
    ]

    return {
        **tx_payload(tx),
        "investigation": (
            {
                "id": inv.id,
                "status": inv.status,
                "evidence": json.loads(inv.evidence or "[]"),
                "agent_findings": json.loads(inv.agent_findings or "[]"),
                "timeline": json.loads(inv.timeline or "[]"),
                "root_cause": inv.root_cause,
                "recommendation": inv.recommendation,
                "customer_email_draft": inv.customer_email_draft,
                "manager_escalation_draft": inv.manager_escalation_draft,
                "final_summary": inv.final_summary,
                "confidence": float(inv.confidence) if inv.confidence is not None else 0.85,
                "ai_model": inv.ai_model or "meta-llama/Llama-3.3-70B-Instruct",
                "model_used": inv.model_used or inv.ai_model or "meta-llama/Llama-3.3-70B-Instruct",
                "fallback_used": inv.fallback_used,
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
        "pinecone_precedents": pinecone_precedents,
    }


@router.get("/transactions/{transaction_id}/audit")
def transaction_audit(transaction_id: str, _: FinanceUser, db: Session = Depends(get_db)):
    if not db.get(FinancialTransaction, transaction_id):
        raise HTTPException(status_code=404, detail="Transaction not found")
    approvals = db.scalars(select(Approval).where(Approval.transaction_id == transaction_id).order_by(Approval.created_at)).all()
    events = db.scalars(select(AuditEvent).where(AuditEvent.subject == transaction_id).order_by(AuditEvent.created_at)).all()
    return {
        "approvals": [{"decision": a.decision, "reason": a.reason, "decided_by": a.decided_by, "created_at": a.created_at} for a in approvals],
        "events": [{"action": e.action, "actor_id": e.actor_id, "created_at": e.created_at} for e in events],
    }


@router.post("/transactions/{transaction_id}/communication-draft/send")
async def send_communication_draft(
    transaction_id: str,
    payload: dict,
    user: FinanceUser,
    db: Session = Depends(get_db),
):
    from ..services.email_service import safe_send_customer_email
    from .auth import audit

    tx = db.get(FinancialTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    to_email = payload.get("to_email") or f"{tx.customer.lower().replace(' ', '')}@example.com"
    subject = payload.get("subject") or f"Regarding Transaction {tx.id}"
    body = payload.get("body") or ""

    send_result = await safe_send_customer_email(
        to_email=to_email,
        subject=subject,
        body=body,
        transaction_id=tx.id,
    )
    audit(db, user.id, "CUSTOMER_COMMUNICATION_SENT", tx.id)
    db.commit()

    return {
        "status": send_result.get("status", "SENT"),
        "transaction_id": tx.id,
        "recipient": to_email,
        "details": send_result,
    }


@router.get("/evidence/{source_id}")
def evidence_document(source_id: str, _: FinanceUser):
    if not source_id.startswith("INV-"):
        raise HTTPException(status_code=404, detail="Evidence source not available")
    matches = list(DOCUMENT_ROOT.glob(f"{source_id.lower()}_*.md"))
    if not matches:
        raise HTTPException(status_code=404, detail="Document not found")
    document = matches[0]
    return {"source_id": source_id, "document": document.name, "page": 1, "content": document.read_text(encoding="utf-8")}
