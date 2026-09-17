"""CSV ingestion with deterministic reconciliation; no LLM arithmetic or mutation."""
from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schema.models import AccountingPeriod, FinancialTransaction

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


def import_invoices(db: Session, period: str | None = None) -> dict:
    """Import invoice/payment outcomes as normalized transaction facts once per invoice."""
    imported = skipped = 0
    with (DATA_ROOT / "invoices.csv").open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            if period and row["accounting_period"] != period:
                continue
            tx_id = f"TX-{row['invoice_id'].removeprefix('INV-')}"
            if db.get(FinancialTransaction, tx_id):
                skipped += 1
                continue
            expected, actual = Decimal(row["total"]), Decimal(row["amount_paid"])
            difference = expected - actual
            status = "RECONCILED" if difference == 0 else "DISCREPANCY_DETECTED"
            severity = "NONE" if difference == 0 else ("HIGH" if abs(difference) >= Decimal("1000") else "MEDIUM")
            transaction = FinancialTransaction(
                id=tx_id, period=row["accounting_period"], transaction_date=row["invoice_date"],
                customer=row["customer_id"], invoice_id=row["invoice_id"], payment_id=None,
                account="Accounts Receivable", currency=row["currency"], expected_amount=expected,
                actual_amount=actual, difference=difference, discrepancy_type=("PARTIAL_PAYMENT" if difference > 0 else "OVERPAYMENT") if difference else None,
                severity=severity, status=status, root_cause=None, recommendation=None, confidence=None,
            )
            db.add(transaction)
            if not db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == row["accounting_period"])):
                db.add(AccountingPeriod(code=row["accounting_period"]))
            imported += 1
    return {"imported": imported, "skipped": skipped}


def reconcile_period(db: Session, period: str) -> dict:
    """Recalculate persisted differences exclusively from stored numerical facts."""
    matched = discrepancies = 0
    transactions = db.scalars(select(FinancialTransaction).where(FinancialTransaction.period == period)).all()
    for tx in transactions:
        tx.difference = Decimal(str(tx.expected_amount)) - Decimal(str(tx.actual_amount))
        if tx.difference == 0 and tx.status not in {"RESOLVED", "PAYMENT_PENDING"}:
            tx.status, tx.severity, tx.discrepancy_type = "RECONCILED", "NONE", None
            matched += 1
        elif tx.difference != 0 and tx.status in {"RECONCILED", "DISCREPANCY_DETECTED"}:
            tx.status = "DISCREPANCY_DETECTED"
            tx.severity = "HIGH" if abs(tx.difference) >= Decimal("1000") else "MEDIUM"
            discrepancies += 1
    return {"period": period, "transactions": len(transactions), "matched": matched, "discrepancies": discrepancies}
