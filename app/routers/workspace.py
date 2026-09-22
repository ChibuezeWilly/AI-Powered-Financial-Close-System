"""Operational workspace endpoints used by the admin and regular portals."""
from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..schema.models import Document, FinancialTransaction, Investigation, User
from .auth import AdminUser, FinanceUser
from .transactions import tx_payload
from .workspace_portal import router as portal_router
from .workspace_search import router as search_router

router = APIRouter(prefix="/api/v1", tags=["workspace"])
router.include_router(portal_router)
router.include_router(search_router)


def _transactions(db: Session, period: str | None = None, statuses: set[str] | None = None) -> list[dict]:
    query = select(FinancialTransaction).order_by(FinancialTransaction.transaction_date.desc())
    if period:
        query = query.where(FinancialTransaction.period == period)
    if statuses:
        query = query.where(FinancialTransaction.status.in_(statuses))
    return [tx_payload(tx) for tx in db.scalars(query)]


@router.get("/workspace/kpis")
def kpis(period: str = "2026-09", _: FinanceUser = None, db: Session = Depends(get_db)):
    discrepancy_statuses = {"DISCREPANCY_DETECTED", "INVESTIGATING", "AWAITING_HUMAN_APPROVAL", "AWAITING_MANAGER_APPROVAL", "ESCALATED"}
    period_filter = FinancialTransaction.period == period
    discrepancies_count = db.scalar(select(func.count(FinancialTransaction.id)).where(period_filter, FinancialTransaction.status.in_(discrepancy_statuses))) or 0
    awaiting_count = db.scalar(select(func.count(FinancialTransaction.id)).where(period_filter, FinancialTransaction.status.in_({"AWAITING_HUMAN_APPROVAL", "AWAITING_MANAGER_APPROVAL"}))) or 0
    reconciled_count = db.scalar(select(func.count(FinancialTransaction.id)).where(period_filter, FinancialTransaction.status.in_({"RECONCILED", "RESOLVED"}))) or 0
    investigations_count = db.scalar(
        select(func.count(Investigation.id))
        .join(FinancialTransaction, Investigation.transaction_id == FinancialTransaction.id)
        .where(period_filter, Investigation.status.in_({"PENDING", "RUNNING", "AWAITING_APPROVAL"}))
    ) or 0

    resolution_watch_amount = float(
        db.scalar(
            select(func.coalesce(func.sum(func.abs(FinancialTransaction.difference)), 0))
            .where(period_filter, ~FinancialTransaction.status.in_({"RECONCILED", "RESOLVED"}))
        ) or 0
    )
    total_tx_count = db.scalar(select(func.count(FinancialTransaction.id)).where(period_filter)) or 0

    return {
        "discrepancies": discrepancies_count,
        "awaiting_approval": awaiting_count,
        "reconciled": reconciled_count,
        "investigations": investigations_count,
        "resolution_watch_amount": resolution_watch_amount,
        "total_transactions": total_tx_count,
        "current_period": period,
    }


@router.get("/workspace/reconciliation-current")
def reconciliation_current(period: str = "2026-09", _: FinanceUser = None, db: Session = Depends(get_db)):
    current_period = period
    txs = _transactions(db, period=current_period)
    matched = [t for t in txs if t["status"] in {"RECONCILED", "RESOLVED"}]
    unmatched = [t for t in txs if t["status"] not in {"RECONCILED", "RESOLVED"}]
    return {
        "current_period": current_period,
        "status": "READY_FOR_RECONCILIATION",
        "total_transactions": len(txs),
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "transactions": txs,
    }


@router.get("/workspace/discrepancies")
def discrepancies(period: str | None = None, _: FinanceUser = None, db: Session = Depends(get_db)):
    """Deterministic discrepancy query returning all transactions with active variances or discrepancy types."""
    query = select(FinancialTransaction).where(
        or_(
            FinancialTransaction.difference != 0,
            FinancialTransaction.discrepancy_type.isnot(None),
            FinancialTransaction.status.in_({
                "DISCREPANCY_DETECTED",
                "INVESTIGATING",
                "AWAITING_HUMAN_APPROVAL",
                "AWAITING_MANAGER_APPROVAL",
                "ESCALATED",
            }),
        )
    ).order_by(FinancialTransaction.transaction_date.desc())
    if period and period.upper() != "ALL":
        query = query.where(FinancialTransaction.period == period)
    return [tx_payload(tx) for tx in db.scalars(query)]



@router.get("/workspace/investigations")
def investigations(_: FinanceUser = None, db: Session = Depends(get_db)):
    rows = db.scalars(select(Investigation).where(Investigation.status.in_({"PENDING", "RUNNING", "AWAITING_APPROVAL"})).order_by(Investigation.created_at.desc()))
    return [{"id": row.id, "transaction_id": row.transaction_id, "status": row.status, "root_cause": row.root_cause, "recommendation": row.recommendation, "confidence": row.confidence, "timeline": json.loads(row.timeline or "[]")} for row in rows]


@router.get("/workspace/approvals")
def approvals(period: str | None = None, _: FinanceUser = None, db: Session = Depends(get_db)):
    return _transactions(db, period=period, statuses={"AWAITING_HUMAN_APPROVAL", "AWAITING_MANAGER_APPROVAL"})


@router.get("/workspace/reconciled")
def reconciled(period: str | None = None, _: FinanceUser = None, db: Session = Depends(get_db)):
    return _transactions(db, period=period, statuses={"RECONCILED", "RESOLVED"})


@router.get("/workspace/users")
def users(q: str | None = None, _: AdminUser = None, db: Session = Depends(get_db)):
    query = select(User).order_by(User.created_at.desc())
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern), User.role.ilike(pattern)))
    result = []
    for user in db.scalars(query):
        tx_count = len(user.transactions) if user.transactions else 0
        balance = sum(float(tx.actual_amount) for tx in user.transactions) if user.transactions else 0.0
        result.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "transaction_count": tx_count,
            "total_balance": balance,
        })
    return result


@router.get("/workspace/users/{user_id}/transactions")
def user_transactions(user_id: int, _: FinanceUser = None, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_txs = user.transactions if user.transactions else []
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "total_balance": sum(float(tx.actual_amount) for tx in user_txs),
        },
        "transactions": [tx_payload(tx) for tx in user_txs],
    }


@router.get("/workspace/documents")
def documents(q: str | None = None, _: AdminUser = None, db: Session = Depends(get_db)):
    query = select(Document).order_by(Document.created_at.desc())
    if q:
        query = query.where(Document.filename.ilike(f"%{q}%"))
    docs = []
    for doc in db.scalars(query):
        docs.append({
            "id": doc.id,
            "filename": doc.filename,
            "document_type": doc.document_type,
            "file_path": doc.file_path,
            "status": doc.status,
            "accounting_period": doc.accounting_period,
            "records_created": doc.records_created,
            "created_at": doc.created_at,
        })
    return docs
