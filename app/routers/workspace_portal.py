"""Regular user portal and account query routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..langgraph import default_model_runner
from ..schema.models import Account, Customer, Document, FinancialTransaction, LedgerEntry, User
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
        tx_query = select(FinancialTransaction).where(
            or_(
                FinancialTransaction.account_code == acct.code,
                FinancialTransaction.account.ilike(f"%{acct.name}%"),
            )
        )
        txs = list(db.scalars(tx_query))
        tx_count = len(txs)
        total_balance = sum(float(tx.actual_amount) for tx in txs)
        discrepancy_txs = [tx for tx in txs if tx.difference != 0 or tx.discrepancy_type]
        discrepancies_count = len(discrepancy_txs)
        total_variance = sum(abs(float(tx.difference)) for tx in discrepancy_txs)

        # Look up representative customer details if applicable
        sample_customer_name = txs[0].customer if txs else None
        cust = None
        if sample_customer_name:
            cust = db.scalar(
                select(Customer).where(
                    or_(
                        Customer.name.ilike(sample_customer_name),
                        Customer.legal_name.ilike(sample_customer_name),
                    )
                )
            )

        result.append({
            "id": acct.id,
            "code": acct.code,
            "name": acct.name,
            "account_type": acct.account_type,
            "normal_balance": acct.normal_balance,
            "is_active": acct.is_active,
            "transaction_count": tx_count,
            "total_balance": float(total_balance),
            "discrepancies_count": discrepancies_count,
            "total_variance": float(total_variance),
            "has_discrepancies": discrepancies_count > 0,
            "customer_tier": cust.customer_tier if cust else "Standard",
            "payment_terms": cust.payment_terms if cust else "NET30",
            "credit_limit": float(cust.credit_limit) if cust and cust.credit_limit is not None else 50000.0,
            "contact_email": cust.contact_email if cust else None,
        })
    return result


@router.get("/workspace/accounts/{account_id}/transactions")
def account_transactions(
    account_id: str,
    _: FinanceUser = None,
    db: Session = Depends(get_db),
):
    """Retrieve full transaction records, customer details, documents, and ledger for an account."""
    # 1. Resolve Account by ID (e.g. ACCT-1100, ACCT-1200) or Code (e.g. 1100, 1200)
    acct = db.get(Account, account_id)
    if not acct:
        clean_code = account_id.replace("ACCT-", "")
        acct = db.scalar(
            select(Account).where(
                or_(
                    Account.code == clean_code,
                    Account.code == account_id,
                    Account.name.ilike(f"%{account_id}%"),
                )
            )
        )

    # 2. Fetch all matching transactions
    if acct:
        tx_query = select(FinancialTransaction).where(
            or_(
                FinancialTransaction.account_code == acct.code,
                FinancialTransaction.account.ilike(f"%{acct.name}%"),
            )
        ).order_by(FinancialTransaction.transaction_date.desc())
    else:
        # Fallback to searching transactions directly by code or customer ID
        tx_query = select(FinancialTransaction).where(
            or_(
                FinancialTransaction.account_code == account_id,
                FinancialTransaction.customer_id == account_id,
                FinancialTransaction.customer.ilike(f"%{account_id}%"),
            )
        ).order_by(FinancialTransaction.transaction_date.desc())

    txs = list(db.scalars(tx_query))
    if not acct and not txs:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' was not found")

    # If account was synthesized from transactions
    if not acct:
        acct_code = txs[0].account_code or "1200" if txs else "1200"
        acct_name = txs[0].account if txs else f"Account {account_id}"
        acct = Account(
            id=f"ACCT-{acct_code}",
            code=acct_code,
            name=acct_name,
            account_type="Asset",
            normal_balance="debit",
            is_active=True,
        )

    # 3. Retrieve Customer Profile & Tier
    cust = None
    if txs:
        for t in txs:
            if t.customer_id:
                cust = db.get(Customer, t.customer_id)
                if cust:
                    break
            if t.customer:
                cust = db.scalar(
                    select(Customer).where(
                        or_(
                            Customer.name.ilike(t.customer),
                            Customer.legal_name.ilike(t.customer),
                        )
                    )
                )
                if cust:
                    break

    if not cust:
        cust = Customer(
            id=f"CUST-{acct.code}",
            name=acct.name,
            legal_name=f"{acct.name} Master Account",
            customer_tier="Enterprise",
            payment_terms="NET30",
            credit_limit=100000.0,
            contact_email=f"billing@{acct.name.lower().replace(' ', '')}.com",
            country="USA",
            currency="USD",
        )

    # 4. Fetch related Ledger Entries
    ledger_entries = list(
        db.scalars(
            select(LedgerEntry)
            .where(
                or_(
                    LedgerEntry.account_code == acct.code,
                    LedgerEntry.account_name.ilike(f"%{acct.name}%"),
                )
            )
            .order_by(LedgerEntry.posted_date.desc())
            .limit(100)
        )
    )

    # 5. Fetch related Documents (Invoices, Policies)
    invoice_ids = {t.invoice_id for t in txs if t.invoice_id}
    docs = list(db.scalars(select(Document).limit(50)))
    matching_docs = []
    for doc in docs:
        if any(inv in doc.filename for inv in invoice_ids) or "policy" in doc.document_type.lower():
            matching_docs.append({
                "id": doc.id,
                "filename": doc.filename,
                "document_type": doc.document_type,
                "file_path": doc.file_path,
                "status": doc.status,
                "records_created": doc.records_created,
                "created_at": doc.created_at,
            })
    if not matching_docs and docs:
        matching_docs = [{
            "id": d.id,
            "filename": d.filename,
            "document_type": d.document_type,
            "file_path": d.file_path,
            "status": d.status,
            "records_created": d.records_created,
            "created_at": d.created_at,
        } for d in docs[:10]]

    # 6. Calculations
    total_spent = sum(float(t.actual_amount) for t in txs)
    discrepancies = [t for t in txs if t.difference != 0 or t.discrepancy_type]
    total_variance = sum(abs(float(t.difference)) for t in discrepancies)

    return {
        "account": {
            "id": acct.id,
            "code": acct.code,
            "name": acct.name,
            "account_type": acct.account_type,
            "normal_balance": acct.normal_balance,
            "is_active": acct.is_active,
            "total_balance": float(total_spent),
            "transaction_count": len(txs),
            "discrepancies_count": len(discrepancies),
            "total_variance": float(total_variance),
        },
        "customer": {
            "id": cust.id,
            "name": cust.name,
            "legal_name": cust.legal_name,
            "customer_tier": cust.customer_tier,
            "country": cust.country,
            "currency": cust.currency,
            "credit_limit": float(cust.credit_limit) if cust.credit_limit is not None else 50000.0,
            "payment_terms": cust.payment_terms,
            "contact_email": cust.contact_email,
            "total_spent": float(total_spent),
            "open_balance": float(total_variance),
        },
        "transactions": [tx_payload(t) for t in txs],
        "documents": matching_docs,
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
        "summary": {
            "total_transactions": len(txs),
            "total_amount": float(total_spent),
            "discrepancies_count": len(discrepancies),
            "reconciled_count": len(txs) - len(discrepancies),
            "total_variance": float(total_variance),
        },
    }



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
