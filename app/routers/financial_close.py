from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..schema.models import AccountingPeriod, FinancialTransaction, MonthlyReport, Notification
from .auth import DecisionUser, FinanceUser, audit
from ..services.ingestion import import_invoices, reconcile_period

router = APIRouter(prefix="/api/v1", tags=["financial-close"])

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


@router.get("/periods")
def periods(_: FinanceUser, db: Session = Depends(get_db)):
    return [
        {"code": period.code, "status": period.status}
        for period in db.scalars(select(AccountingPeriod).order_by(AccountingPeriod.code))
    ]


@router.get("/dashboard")
def dashboard(period: str, _: FinanceUser, db: Session = Depends(get_db)):
    txs = list(db.scalars(select(FinancialTransaction).where(FinancialTransaction.period == period)))
    total = len(txs)
    unresolved = [tx for tx in txs if tx.difference != 0]
    record = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == period))
    return {
        "period": period,
        "period_status": record.status if record else "OPEN",
        "total_transactions": total,
        "reconciled": len([tx for tx in txs if tx.status in {"RECONCILED", "RESOLVED"}]),
        "discrepancies": len(unresolved),
        "awaiting_approval": len([tx for tx in txs if tx.status == "AWAITING_HUMAN_APPROVAL"]),
        "close_progress": round(
            (
                len([tx for tx in txs if tx.status in {"RECONCILED", "RESOLVED"}]) / total * 100
            )
            if total
            else 0
        ),
        "unresolved_amount": sum(abs(float(tx.difference)) for tx in unresolved),
    }


@router.get("/notifications")
def notifications(_: FinanceUser, db: Session = Depends(get_db)):
    return [
        {
            "id": notification.id,
            "event": notification.event,
            "message": notification.message,
            "status": notification.status,
            "created_at": notification.created_at,
        }
        for notification in db.scalars(
            select(Notification).order_by(Notification.created_at.desc()).limit(20)
        )
    ]


@router.post("/ingestion/invoices")
def ingest_invoices(period: str | None, user: DecisionUser, db: Session = Depends(get_db)):
    """Administrative ingestion of the bundled source records into application state."""
    result = import_invoices(db, period)
    audit(db, user.id, "INVOICES_INGESTED", period or "all-periods")
    db.commit()
    return result


@router.post("/periods/{period}/reconcile")
def reconcile(period: str, user: DecisionUser, db: Session = Depends(get_db)):
    record = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == period))
    if not record:
        raise HTTPException(status_code=404, detail="Period not found")
    if record.status == "CLOSED":
        raise HTTPException(status_code=409, detail="Reopen the accounting period before reconciliation")
    result = reconcile_period(db, period)
    audit(db, user.id, "RECONCILIATION_COMPLETED", period)
    db.commit()
    return result


@router.post("/periods/{period}/report")
def generate_report(period: str, user: DecisionUser, db: Session = Depends(get_db)):
    record = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == period))
    if not record:
        raise HTTPException(status_code=404, detail="Period not found")
    txs = list(db.scalars(select(FinancialTransaction).where(FinancialTransaction.period == period)))
    payload = {
        "period": period, "close_status": record.status, "transaction_count": len(txs),
        "reconciled": sum(tx.status in {"RECONCILED", "RESOLVED"} for tx in txs),
        "outstanding_amount": sum(abs(float(tx.difference)) for tx in txs if tx.difference != 0),
        "discrepancy_by_severity": {severity: sum(tx.severity == severity for tx in txs) for severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
        "generated_by": user.full_name, "agent_model": None,
    }
    report = db.scalar(select(MonthlyReport).where(MonthlyReport.period == period))
    if report and report.status == "FINAL" and record.status == "CLOSED":
        return json.loads(report.payload)
    if not report:
        report = MonthlyReport(period=period, payload="{}", generated_by=user.id)
        db.add(report)
    report.payload, report.status, report.generated_by = json.dumps(payload), "FINAL" if record.status == "CLOSED" else "DRAFT", user.id
    audit(db, user.id, "MONTHLY_REPORT_GENERATED", period)
    db.commit()
    return payload


@router.get("/periods/{period}/report")
def get_report(period: str, _: FinanceUser, db: Session = Depends(get_db)):
    report = db.scalar(select(MonthlyReport).where(MonthlyReport.period == period))
    if not report:
        raise HTTPException(status_code=404, detail="No report has been generated for this period")
    return json.loads(report.payload)


@router.post("/periods/{period}/close")
def close_period(period: str, user: DecisionUser, db: Session = Depends(get_db)):
    record = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == period))
    unresolved = db.scalar(
        select(FinancialTransaction).where(
            FinancialTransaction.period == period,
            FinancialTransaction.status.not_in(["RECONCILED", "RESOLVED"]),
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail="Period not found")
    if unresolved:
        raise HTTPException(
            status_code=409,
            detail="Resolve or explicitly escalate all transactions before close",
        )
    record.status = "CLOSED"
    audit(db, user.id, "PERIOD_CLOSED", period)
    db.commit()
    return {"period": period, "status": "CLOSED"}


@router.post("/periods/{period}/reopen")
def reopen_period(period: str, reason: str, user: DecisionUser, db: Session = Depends(get_db)):
    record = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == period))
    if not record:
        raise HTTPException(status_code=404, detail="Period not found")
    record.status = "OPEN"
    record.closed_reason = reason
    audit(db, user.id, "PERIOD_REOPENED", f"{period}:{reason}")
    db.commit()
    return {"period": period, "status": "OPEN"}
