"""Persisted, read-only AI investigations for a financial transaction."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..langgraph import InvestigationInput, run_investigation
from ..langgraph.model_router import is_model_runner_configured
from ..langgraph.schema import Evidence
from ..schema.models import FinancialTransaction, Investigation, Policy


def _evidence_for(investigation: Investigation | None) -> list[Evidence]:
    if not investigation:
        return []
    records = json.loads(investigation.evidence or "[]")
    allowed_types = {"transaction", "document", "policy", "system", "user"}
    return [
        Evidence(
            source_id=str(record.get("source_id", "unknown")),
            source_type=(str(record.get("source_type", "system")).lower() if str(record.get("source_type", "")).lower() in allowed_types else "system"),
            excerpt=str(record.get("excerpt", "")),
            relevance=float(record.get("relevance", 0)),
        )
        for record in records
    ]


def investigate_transaction(db: Session, transaction: FinancialTransaction) -> dict:
    """Analyze a case with LangGraph; it never posts or approves financial actions."""
    if not is_model_runner_configured():
        raise RuntimeError("AI investigation is not configured. Set LLM_BASE_URL and LLM_API_KEY for a Qwen-compatible endpoint.")

    investigation = db.scalar(select(Investigation).where(Investigation.transaction_id == transaction.id))
    if not investigation:
        investigation = Investigation(
            id=f"INVG-{transaction.id}",
            transaction_id=transaction.id,
            status="RUNNING",
            evidence="[]",
            timeline="[]",
        )
        db.add(investigation)
    else:
        investigation.status = "RUNNING"
    policies = db.scalars(select(Policy).where(Policy.status == "active")).all()
    result = run_investigation(
        InvestigationInput(
            transaction_id=transaction.id,
            expected_amount=transaction.expected_amount,
            actual_amount=transaction.actual_amount,
            currency=transaction.currency,
            transaction={
                "transaction_id": transaction.id,
                "invoice_id": transaction.invoice_id,
                "payment_id": transaction.payment_id,
                "customer_id": transaction.customer,
                "discrepancy_type": transaction.discrepancy_type,
            },
            retrieved_policies=[{"policy_id": policy.policy_id, "title": policy.title, "content": policy.content} for policy in policies],
            evidence=_evidence_for(investigation),
        )
    )
    report = result["report"]
    root_cause = result["root_cause"]
    transaction.root_cause = root_cause.cause
    transaction.recommendation = report.recommendation
    transaction.confidence = report.confidence
    investigation.root_cause = root_cause.cause
    investigation.recommendation = report.recommendation
    investigation.confidence = report.confidence
    investigation.ai_model = result["agent_models"]["root_cause"]
    investigation.status = "COMPLETED"
    investigation.completed_at = datetime.now(timezone.utc)
    timeline = json.loads(investigation.timeline or "[]")
    timeline.append("AI LangGraph investigation completed; financial action remains human-controlled.")
    investigation.timeline = json.dumps(timeline)
    if transaction.difference != 0 and transaction.status in {"DISCREPANCY_DETECTED", "INVESTIGATING"}:
        transaction.status = "AWAITING_HUMAN_APPROVAL"

    return {
        "transaction_id": transaction.id,
        "reconciliation": result["reconciliation"],
        "root_cause": root_cause.model_dump(),
        "report": report.model_dump(),
        "verification": result["verification"].model_dump(),
    }
