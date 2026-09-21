"""Regular user portal and account query routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..langgraph import default_model_runner
from ..schema.models import Account, Customer, FinancialTransaction
from .auth import FinanceUser, RegularUser
from .transactions import tx_payload

router = APIRouter(prefix="", tags=["workspace-portal"])


@router.get("/portal/customer-account")
def portal_customer_account(
    user: RegularUser = None,
    db: Session = Depends(get_db),
):
    customer = db.scalar(
        select(Customer).where(
            or_(
                Customer.contact_email == user.email,
                Customer.name.ilike(user.full_name),
                Customer.legal_name.ilike(user.full_name),
            )
        )
    )
    if not customer:
        cust_id = f"CUST-U{user.id:04d}"
        customer = db.get(Customer, cust_id)
        if not customer:
            customer = Customer(
                id=cust_id,
                name=user.full_name,
                legal_name=user.full_name,
                contact_email=user.email,
                contact_name=user.full_name,
                customer_tier="Standard",
                country="USA",
                currency="USD",
                payment_terms="NET30",
                credit_limit=50000.0,
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)

    user_tx_count = db.scalar(
        select(func.count(FinancialTransaction.id)).where(FinancialTransaction.user_id == user.id)
    ) or 0
    total_amount = db.scalar(
        select(func.coalesce(func.sum(FinancialTransaction.actual_amount), 0.0))
        .where(FinancialTransaction.user_id == user.id)
    ) or 0.0

    return {
        "id": customer.id,
        "name": customer.name,
        "legal_name": customer.legal_name,
        "customer_tier": customer.customer_tier,
        "country": customer.country,
        "currency": customer.currency,
        "credit_limit": float(customer.credit_limit) if customer.credit_limit is not None else 50000.0,
        "contact_email": customer.contact_email or user.email,
        "total_amount": float(total_amount),
        "transaction_count": user_tx_count,
    }


@router.get("/portal/transactions/search")
def portal_transactions_search(
    q: str = Query(min_length=1),
    user: RegularUser = None,
    db: Session = Depends(get_db),
):
    pat = f"%{q.strip()}%"
    query = (
        select(FinancialTransaction)
        .where(FinancialTransaction.user_id == user.id)
        .where(
            or_(
                FinancialTransaction.id.ilike(pat),
                FinancialTransaction.invoice_id.ilike(pat),
                FinancialTransaction.account.ilike(pat),
                FinancialTransaction.customer.ilike(pat),
                FinancialTransaction.root_cause.ilike(pat),
            )
        )
        .order_by(FinancialTransaction.transaction_date.desc())
        .limit(50)
    )
    txs = list(db.scalars(query))
    matching_amount = sum(float(tx.actual_amount) for tx in txs)
    account_total = db.scalar(
        select(func.coalesce(func.sum(FinancialTransaction.actual_amount), 0.0))
        .where(FinancialTransaction.user_id == user.id)
    ) or 0.0
    return {
        "query": q,
        "total_matches": len(txs),
        "matching_amount": matching_amount,
        "account_total": float(account_total),
        "results": [tx_payload(tx) for tx in txs],
    }


@router.get("/portal/transactions")
def portal_transactions(
    period: str | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
    user: RegularUser = None,
    db: Session = Depends(get_db),
):
    target_period = period or "2026-09"
    base_query = (
        select(FinancialTransaction)
        .where(FinancialTransaction.period == target_period)
        .where(FinancialTransaction.user_id == user.id)
    )
    if q and q.strip():
        pat = f"%{q.strip()}%"
        base_query = base_query.where(
            or_(
                FinancialTransaction.id.ilike(pat),
                FinancialTransaction.invoice_id.ilike(pat),
                FinancialTransaction.account.ilike(pat),
                FinancialTransaction.customer.ilike(pat),
                FinancialTransaction.root_cause.ilike(pat),
            )
        )
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    total_amount = db.scalar(
        select(func.coalesce(func.sum(FinancialTransaction.actual_amount), 0.0))
        .where(FinancialTransaction.period == target_period)
        .where(FinancialTransaction.user_id == user.id)
    ) or 0.0
    txs = list(
        db.scalars(
            base_query.order_by(FinancialTransaction.transaction_date.desc())
            .offset(offset)
            .limit(limit)
        )
    )

    return {
        "period": target_period,
        "total": total,
        "total_amount": float(total_amount),
        "offset": offset,
        "limit": limit,
        "has_more": (offset + limit) < total,
        "transactions": [tx_payload(tx) for tx in txs],
    }


@router.get("/workspace/accounts")
def workspace_accounts(
    q: str | None = None,
    _: FinanceUser = None,
    db: Session = Depends(get_db),
):
    query = select(Account).order_by(Account.code)
    if q and q.strip():
        pat = f"%{q.strip()}%"
        query = query.where(
            or_(
                Account.code.ilike(pat),
                Account.name.ilike(pat),
                Account.account_type.ilike(pat),
            )
        )
    accounts = list(db.scalars(query))

    result = []
    for acct in accounts:
        tx_count = db.scalar(
            select(func.count(FinancialTransaction.id)).where(
                or_(
                    FinancialTransaction.account_code == acct.code,
                    FinancialTransaction.account.ilike(f"%{acct.name}%"),
                )
            )
        ) or 0
        total_balance = db.scalar(
            select(func.coalesce(func.sum(FinancialTransaction.actual_amount), 0.0)).where(
                or_(
                    FinancialTransaction.account_code == acct.code,
                    FinancialTransaction.account.ilike(f"%{acct.name}%"),
                )
            )
        ) or 0.0

        result.append({
            "id": acct.id,
            "code": acct.code,
            "name": acct.name,
            "account_type": acct.account_type,
            "normal_balance": acct.normal_balance,
            "is_active": acct.is_active,
            "transaction_count": tx_count,
            "total_balance": float(total_balance),
        })
    return result


class Insight(BaseModel):
    period: str
    summary: str
    risks: list[str] = []
    recommendations: list[str] = []


@router.get("/workspace/insights", response_model=Insight)
def insights(period: str = "2026-09", _: FinanceUser = None, db: Session = Depends(get_db)):
    txs = list(db.scalars(select(FinancialTransaction).where(FinancialTransaction.period == period).limit(50)))
    if not txs:
        txs = list(db.scalars(select(FinancialTransaction).limit(50)))
    payload = {
        "period": period,
        "transaction_count": len(txs),
        "discrepancies": len([t for t in txs if t.difference != 0]),
        "transactions": [tx_payload(tx) for tx in txs[:15]],
    }
    runner = default_model_runner()
    if runner is None:
        return Insight(
            period=period,
            summary=f"Period {period} financial overview: {len(txs)} transactions logged with {payload['discrepancies']} discrepancies.",
            risks=["Unapproved customer discounts require manager escalation", "Duplicate payment batches pending clearance"],
            recommendations=["Prioritize review of transactions exceeding $250 variance", "Enforce FIN-042 documentation before reconciliation"],
        )
    try:
        return runner.invoke(
            model="meta-llama/Llama-3.3-70B-Instruct",
            prompt="You are a senior financial controller. Analyze this dataset and provide insights as JSON.",
            payload=payload,
            schema=Insight,
        )
    except Exception:
        return Insight(
            period=period,
            summary=f"Analysis for period {period}: Total volume of {len(txs)} transactions with {payload['discrepancies']} discrepancies.",
            risks=["Undocumented promotional discounts", "Bank timing differences on settlements"],
            recommendations=["Verify credit note authorization", "Trigger AI investigation on critical severity variances"],
        )
