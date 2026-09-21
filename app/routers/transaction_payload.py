"""Transaction serialization helper."""
from __future__ import annotations

from ..schema.models import FinancialTransaction


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
