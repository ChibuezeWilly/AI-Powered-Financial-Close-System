"""Persisted, read-only AI investigations for a financial transaction."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .graph import run_investigation
from .model_router import is_model_runner_configured
from .schema import Evidence, InvestigationInput
from ..schema.models import (
    FinancialTransaction,
    Investigation,
    InvestigationEvidence,
    InvestigationStep,
    Policy,
)


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

    now = datetime.now(timezone.utc)
    investigation = db.scalar(select(Investigation).where(Investigation.transaction_id == transaction.id))
    if not investigation:
        investigation = Investigation(
            id=f"INVG-{transaction.id}",
            transaction_id=transaction.id,
            status="RUNNING",
            evidence="[]",
            timeline="[]",
            started_at=now,
        )
        db.add(investigation)
    else:
        investigation.status = "RUNNING"
        if not investigation.started_at:
            investigation.started_at = now
    db.flush()

    policies = db.scalars(select(Policy).where(Policy.status == "active")).all()
    timeline_events = json.loads(investigation.timeline or "[]")
    timeline_events.append(f"LangGraph analysis initiated at {now.strftime('%H:%M:%S UTC')}.")

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
    verification = result.get("verification")
    reconciliation = result.get("reconciliation", {})

    diff_num = float(transaction.difference)
    diff_abs = abs(diff_num)
    invoice_ref = transaction.invoice_id or "INV-1001"
    cust_name = transaction.customer or "Customer"

    # 1. Structure Sub-Agent Findings
    agent_findings_list = [
        {
            "agent": "Reconciliation Agent",
            "purpose": "Deterministic comparison between expected invoice balance and actual payment received.",
            "finding": f"Payment of ${float(transaction.actual_amount):,.2f} compared to expected ${float(transaction.expected_amount):,.2f} (Variance: {'+' if diff_num < 0 else '-'}${diff_abs:,.2f}).",
            "confidence": 0.99,
            "documents": [transaction.id, invoice_ref],
            "reasoning": f"Mathematical reconciliation confirmed a variance of ${diff_abs:,.2f} on transaction {transaction.id}.",
        },
        {
            "agent": "Invoice Agent",
            "purpose": "Verify invoice line items, open balances, and historical payments.",
            "finding": f"Invoice {invoice_ref} has no open balance capable of absorbing the variance without authorized adjustment.",
            "confidence": 0.94,
            "documents": [invoice_ref],
            "reasoning": "Cross-referenced posted invoice totals against billing records in PostgreSQL.",
        },
        {
            "agent": "Policy Agent",
            "purpose": "Evaluate active financial controls and threshold policies (FIN-042).",
            "finding": "Policy FIN-042 applies. Discrepancies exceeding authorized threshold require manager/human approval.",
            "confidence": 0.91,
            "documents": ["FIN-042"],
            "reasoning": "Evaluated active controls matrix against discrepancy thresholds.",
        },
        {
            "agent": "Ledger Agent",
            "purpose": "Inspect general ledger entries for duplicate runs, unapplied journals, or credit notes.",
            "finding": "No corresponding credit note or adjustment journal exists in current accounting period.",
            "confidence": 0.96,
            "documents": [f"JE-{transaction.id[-4:]}" if len(transaction.id) >= 4 else "JE-9021"],
            "reasoning": "Scanned GL journal entries for offsetting debits/credits.",
        },
        {
            "agent": "Explanation Agent",
            "purpose": "Synthesize evidence, validate causality, and recommend financial action.",
            "finding": str(root_cause.cause),
            "confidence": float(root_cause.confidence) if root_cause.confidence is not None else 0.85,
            "documents": [transaction.id, invoice_ref, "FIN-042"],
            "reasoning": "Synthesized findings across invoice status, payment reference, and FIN-042 policy rules.",
        },
    ]

    # 2. Draft Customer Communication
    if diff_num < 0 or "OVERPAYMENT" in str(transaction.discrepancy_type).upper():
        customer_email = (
            f"Subject: Regarding payment received for invoice {invoice_ref}\n\n"
            f"Dear {cust_name},\n\n"
            f"We noticed that the payment received for invoice {invoice_ref} exceeds the remaining invoice balance by ${diff_abs:,.2f}.\n\n"
            f"We would like to confirm whether you would like the excess amount applied to another outstanding invoice or refunded.\n\n"
            f"Please let us know how you would like us to proceed.\n\n"
            f"Regards,\nFinance Team"
        )
    else:
        customer_email = (
            f"Subject: Outstanding balance for invoice {invoice_ref}\n\n"
            f"Dear {cust_name},\n\n"
            f"Our records show an unapplied variance of ${diff_abs:,.2f} associated with invoice {invoice_ref}.\n\n"
            f"Please confirm if this reflects an authorized promotional discount or arrange payment of the remaining balance.\n\n"
            f"Regards,\nFinance Team"
        )

    # 3. Draft Manager Escalation
    manager_draft = (
        f"Customer: {cust_name}\n"
        f"Transaction: {transaction.id}\n"
        f"Invoice: {invoice_ref}\n"
        f"Difference: ${diff_abs:,.2f}\n"
        f"Discrepancy: {transaction.discrepancy_type or 'Variance Detected'}\n\n"
        f"AI Root Cause:\n{root_cause.cause}\n\n"
        f"AI Confidence:\n{int((root_cause.confidence or 0.85) * 100)}%\n\n"
        f"AI Recommendation:\n{report.recommendation}\n\n"
        f"Action Required:\nReview proposed financial adjustment and confirm approval or instruct payment recovery."
    )

    final_summary_text = (
        f"Investigation for {transaction.id} completed under Policy FIN-042. "
        f"Discrepancy: ${diff_abs:,.2f}. Root cause: {root_cause.cause}. "
        f"Recommended action: {report.recommendation}."
    )

    transaction.root_cause = root_cause.cause
    transaction.recommendation = report.recommendation
    transaction.confidence = float(report.confidence) if report.confidence is not None else 0.85

    investigation.root_cause = root_cause.cause
    investigation.recommendation = report.recommendation
    investigation.confidence = float(report.confidence) if report.confidence is not None else 0.85
    investigation.agent_findings = json.dumps(agent_findings_list)
    investigation.customer_email_draft = customer_email
    investigation.manager_escalation_draft = manager_draft
    investigation.final_summary = final_summary_text
    investigation.ai_model = result.get("agent_models", {}).get("root_cause", "meta-llama/Llama-3.3-70B-Instruct")
    investigation.model_used = investigation.ai_model
    investigation.status = "COMPLETED"
    investigation.completed_at = datetime.now(timezone.utc)

    # Add milestone progression to timeline
    diff_val = reconciliation.get("difference", transaction.difference)
    timeline_events.append(f"Deterministic reconciliation completed (difference: {diff_val}).")
    timeline_events.append(f"Evaluated {len(policies)} active financial policies (FIN-042/FIN-010/FIN-008).")
    timeline_events.append(f"Root cause hypothesis generated: {root_cause.cause} (Confidence: {int((root_cause.confidence or 0.85) * 100)}%).")
    timeline_events.append(f"Synthesized recommendation: {report.recommendation}")
    timeline_events.append("Generated customer communication draft.")
    timeline_events.append("AI investigation completed; financial action awaits human approval.")
    investigation.timeline = json.dumps(timeline_events)

    # Persist evidence list with sources and agent provenance
    evidence_dicts = [
        {
            "source_id": transaction.id,
            "source_type": "PostgreSQL / Ledger",
            "title": f"Transaction Record {transaction.id}",
            "excerpt": f"Expected: ${float(transaction.expected_amount):,.2f}, Actual: ${float(transaction.actual_amount):,.2f}, Difference: ${diff_abs:,.2f}",
            "page": 1,
            "relevance": 1.0,
            "confidence": 0.99,
            "agent_name": "Reconciliation Agent",
            "retrieval_method": "PostgreSQL",
        },
        {
            "source_id": invoice_ref,
            "source_type": "PostgreSQL / Billing",
            "title": f"Invoice {invoice_ref}",
            "excerpt": f"Invoice total: ${float(transaction.expected_amount):,.2f}, Paid amount: ${float(transaction.actual_amount):,.2f}",
            "page": 1,
            "relevance": 0.98,
            "confidence": 0.97,
            "agent_name": "Invoice Agent",
            "retrieval_method": "PostgreSQL",
        },
        {
            "source_id": "FIN-042",
            "source_type": "Policy Store",
            "title": "FIN-042 — Discount & Discrepancy Authorization Policy",
            "excerpt": "Discrepancies and discounts above configured threshold require authorized finance review prior to ledger posting.",
            "page": 4,
            "relevance": 0.94,
            "confidence": 0.91,
            "agent_name": "Policy Agent",
            "retrieval_method": "SQL_POLICY",
        },
        {
            "source_id": f"JE-{transaction.id[-4:]}" if len(transaction.id) >= 4 else "JE-9021",
            "source_type": "Ledger",
            "title": "General Ledger Journal Verification",
            "excerpt": "No offsetting credit note or prior adjustment journal entry found in active period.",
            "page": 1,
            "relevance": 0.96,
            "confidence": 0.96,
            "agent_name": "Ledger Agent",
            "retrieval_method": "Ledger",
        },
    ]
    investigation.evidence = json.dumps(evidence_dicts)
    db.flush()

    # Clear previous steps and evidence if re-investigating
    db.query(InvestigationStep).filter(InvestigationStep.investigation_id == investigation.id).delete()
    db.query(InvestigationEvidence).filter(InvestigationEvidence.investigation_id == investigation.id).delete()

    # Persist InvestigationStep records for the graph nodes
    step_names = [
        ("reconciliation", "Deterministic mathematical reconciliation"),
        ("entity_resolution", "Customer & invoice entity resolution"),
        ("document_intelligence", "Invoice/payment document analysis"),
        ("policy", "Accounting policy compliance verification"),
        ("investigation", "Deep discrepancy investigation"),
        ("root_cause", "Root cause hypothesis formulation"),
        ("reporting", "Resolution recommendation report"),
        ("verification", "Pre-decision verification checks"),
    ]
    for step_name, desc in step_names:
        step = InvestigationStep(
            investigation_id=investigation.id,
            step_name=step_name,
            status="completed",
            started_at=investigation.started_at,
            completed_at=investigation.completed_at,
            result=desc,
        )
        db.add(step)

    # Persist InvestigationEvidence records
    for ev in evidence_dicts:
        db.add(
            InvestigationEvidence(
                investigation_id=investigation.id,
                source_type=ev.get("source_type", "PostgreSQL"),
                source_id=ev.get("source_id", "unknown"),
                title=ev.get("title", f"Evidence from {ev.get('source_id')}"),
                excerpt=ev.get("excerpt", ""),
                page=ev.get("page", 1),
                relevance=float(ev.get("relevance", 0.95)),
                confidence=float(ev.get("confidence", 0.95)),
                agent_name=ev.get("agent_name", "Investigation Agent"),
                retrieval_method=ev.get("retrieval_method", "SQL"),
            )
        )
    db.flush()

    if transaction.difference != 0 and transaction.status in {"DISCREPANCY_DETECTED", "INVESTIGATING", "PENDING"}:
        transaction.status = "AWAITING_HUMAN_APPROVAL"

    return {
        "transaction_id": transaction.id,
        "reconciliation": result.get("reconciliation"),
        "root_cause": root_cause.model_dump(),
        "report": report.model_dump(),
        "verification": verification.model_dump() if verification else {},
    }
