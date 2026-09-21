"""Financial transactions API router."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..schema.models import FinancialTransaction
from .auth import FinanceUser
from .transaction_decisions import router as decisions_router
from .transaction_detail import router as detail_router
from .transaction_payload import tx_payload

router = APIRouter(prefix="/api/v1", tags=["financial-close"])
router.include_router(decisions_router)
router.include_router(detail_router)


@router.get("/transactions")
def transactions(
    period: str | None = None,
    q: str | None = None,
    _: FinanceUser = None,
    db: Session = Depends(get_db),
):
    query = select(FinancialTransaction)
    if period and period.upper() != "ALL":
        query = query.where(FinancialTransaction.period == period)
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



__all__ = ["router", "transactions", "tx_payload"]
