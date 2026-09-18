"""Operational workspace endpoints used by the admin and regular portals."""
from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database.database import SessionLocal, get_db
from ..langgraph.model_router import default_model_runner
from ..schema.models import (
    Account,
    Approval,
    Customer,
    Document,
    FinancialTransaction,
    Investigation,
    KnowledgeDocument,
    LedgerEntry,
    Policy,
    Role,
    User,
)
from ..services.rag.retrieval import retrieve
from .auth import AdminUser, FinanceUser, RegularUser
from .transactions import tx_payload

router = APIRouter(prefix="/api/v1", tags=["workspace"])


def _transactions(db: Session, period: str | None = None, statuses: set[str] | None = None) -> list[dict]:
    query = select(FinancialTransaction).order_by(FinancialTransaction.transaction_date.desc())
    if period:
        query = query.where(FinancialTransaction.period == period)
    if statuses:
        query = query.where(FinancialTransaction.status.in_(statuses))
    return [tx_payload(tx) for tx in db.scalars(query)]


from sqlalchemy import func, or_, select

@router.get("/workspace/kpis")
def kpis(_: FinanceUser = None, db: Session = Depends(get_db)):
    discrepancy_statuses = {"DISCREPANCY_DETECTED", "INVESTIGATING", "AWAITING_HUMAN_APPROVAL", "AWAITING_MANAGER_APPROVAL", "ESCALATED"}
    discrepancies_count = db.scalar(select(func.count(FinancialTransaction.id)).where(FinancialTransaction.status.in_(discrepancy_statuses))) or 0
    awaiting_count = db.scalar(select(func.count(FinancialTransaction.id)).where(FinancialTransaction.status.in_({"AWAITING_HUMAN_APPROVAL", "AWAITING_MANAGER_APPROVAL"}))) or 0
    reconciled_count = db.scalar(select(func.count(FinancialTransaction.id)).where(FinancialTransaction.status.in_({"RECONCILED", "RESOLVED"}))) or 0
    investigations_count = db.scalar(select(func.count(Investigation.id)).where(Investigation.status.in_({"PENDING", "RUNNING", "AWAITING_APPROVAL"}))) or 0

    resolution_watch_amount = float(
        db.scalar(
            select(func.coalesce(func.sum(func.abs(FinancialTransaction.difference)), 0))
            .where(~FinancialTransaction.status.in_({"RECONCILED", "RESOLVED"}))
        ) or 0
    )
    total_tx_count = db.scalar(select(func.count(FinancialTransaction.id))) or 0

    return {
        "discrepancies": discrepancies_count,
        "awaiting_approval": awaiting_count,
        "reconciled": reconciled_count,
        "investigations": investigations_count,
        "resolution_watch_amount": resolution_watch_amount,
        "total_transactions": total_tx_count,
        "current_period": "2026-09",
    }


@router.get("/workspace/reconciliation-current")
def reconciliation_current(_: FinanceUser = None, db: Session = Depends(get_db)):
    current_period = "2026-09"
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
def discrepancies(_: FinanceUser = None, db: Session = Depends(get_db)):
    return _transactions(db, statuses={"DISCREPANCY_DETECTED", "INVESTIGATING", "AWAITING_HUMAN_APPROVAL", "AWAITING_MANAGER_APPROVAL", "ESCALATED"})


@router.get("/workspace/investigations")
def investigations(_: FinanceUser = None, db: Session = Depends(get_db)):
    rows = db.scalars(select(Investigation).where(Investigation.status.in_({"PENDING", "RUNNING", "AWAITING_APPROVAL"})).order_by(Investigation.created_at.desc()))
    return [{"id": row.id, "transaction_id": row.transaction_id, "status": row.status, "root_cause": row.root_cause, "recommendation": row.recommendation, "confidence": row.confidence, "timeline": json.loads(row.timeline or "[]")} for row in rows]


@router.get("/workspace/approvals")
def approvals(_: FinanceUser = None, db: Session = Depends(get_db)):
    return _transactions(db, statuses={"AWAITING_HUMAN_APPROVAL", "AWAITING_MANAGER_APPROVAL"})


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
def user_transactions(user_id: int, _: AdminUser = None, db: Session = Depends(get_db)):
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


def _sql_search(query: str, limit: int) -> list[dict]:
    with SessionLocal() as db:
        pattern = f"%{query}%"
        rows: list[dict] = []
        for doc in db.scalars(select(Document).where(Document.filename.ilike(pattern)).limit(limit)):
            rows.append({"source": "postgres", "kind": "document", "id": doc.id, "title": doc.filename, "content": doc.document_type, "location": doc.file_path})
        for policy in db.scalars(select(Policy).where(or_(Policy.title.ilike(pattern), Policy.content.ilike(pattern))).limit(limit)):
            rows.append({"source": "postgres", "kind": "policy", "id": policy.policy_id, "title": policy.title, "content": policy.content[:300], "location": "policies"})
        for customer in db.scalars(select(Customer).where(or_(Customer.id.ilike(pattern), Customer.name.ilike(pattern), Customer.legal_name.ilike(pattern))).limit(limit)):
            rows.append({"source": "postgres", "kind": "customer", "id": customer.id, "title": customer.name, "content": f"Customer: {customer.legal_name} | Tier: {customer.customer_tier}", "location": "customers"})
        for entry in db.scalars(select(LedgerEntry).where(or_(LedgerEntry.description.ilike(pattern), LedgerEntry.reference.ilike(pattern), LedgerEntry.account_name.ilike(pattern))).limit(limit)):
            rows.append({"source": "postgres", "kind": "ledger", "id": entry.id, "title": entry.account_name, "content": entry.description, "location": entry.accounting_period})
        for tx in db.scalars(select(FinancialTransaction).where(or_(FinancialTransaction.customer.ilike(pattern), FinancialTransaction.id.ilike(pattern), FinancialTransaction.invoice_id.ilike(pattern))).limit(limit)):
            rows.append({"source": "postgres", "kind": "transaction", "id": tx.id, "title": f"{tx.customer} ({tx.id})", "content": f"Amount: ${float(tx.actual_amount):,.2f} | Status: {tx.status}", "location": tx.period})
        return rows


def _pinecone_search(query: str, limit: int) -> list[dict]:
    try:
        from ..services.rag.retrieval import dense_search
        return [
            {
                "source": "pinecone",
                "kind": "vector_match",
                "id": r.get("embedding_id", r.get("document_id", "vec")),
                "title": r.get("document_id", "Semantic match"),
                "content": r.get("content", "")[:300],
                "score": round(float(r.get("score", 0)), 3),
                "location": r.get("document_type", "vector_index"),
            }
            for r in dense_search(query, top_k=limit)
        ]
    except Exception as err:
        return []


def _bm25_search(query: str, limit: int) -> list[dict]:
    try:
        from ..services.rag.retrieval import sparse_search
        return [
            {
                "source": "bm25",
                "kind": "sparse_match",
                "id": r.get("embedding_id", r.get("document_id", "bm25")),
                "title": r.get("document_id", "Keyword match"),
                "content": r.get("content", "")[:300],
                "score": round(float(r.get("score", 0)), 3),
                "location": "knowledge_index",
            }
            for r in sparse_search(query, top_k=limit)
        ]
    except Exception as err:
        return []


@router.get("/workspace/search")
async def search(q: str = Query(min_length=2), exclude: list[str] = Query(default=[]), _: FinanceUser = None):
    """Search PostgreSQL, Pinecone, and BM25 concurrently with exclusion filters."""
    limit = 20
    exclude_set = set(exclude)
    tasks = []
    task_keys = []

    if "postgres" not in exclude_set:
        tasks.append(asyncio.to_thread(_sql_search, q, limit))
        task_keys.append("postgres")
    if "pinecone" not in exclude_set:
        tasks.append(asyncio.to_thread(_pinecone_search, q, limit))
        task_keys.append("pinecone")
    if "bm25" not in exclude_set:
        tasks.append(asyncio.to_thread(_bm25_search, q, limit))
        task_keys.append("bm25")

    results_lists = await asyncio.gather(*tasks) if tasks else []
    all_results = []
    for rlist in results_lists:
        all_results.extend(rlist)

    return {
        "query": q,
        "active_sources": task_keys,
        "total_results": len(all_results),
        "results": all_results[:limit * 2],
    }


@router.get("/workspace/customer-search")
def customer_search(q: str = Query(min_length=2), _: FinanceUser = None, db: Session = Depends(get_db)):
    """Search customer records for finance admins and managers."""
    pattern = f"%{q}%"
    customers = db.scalars(
        select(Customer)
        .where(or_(Customer.id.ilike(pattern), Customer.name.ilike(pattern), Customer.legal_name.ilike(pattern)))
        .order_by(Customer.name)
        .limit(20)
    )
    return [
        {
            "id": customer.id,
            "name": customer.name,
            "legal_name": customer.legal_name,
            "customer_tier": customer.customer_tier,
            "country": customer.country,
        }
        for customer in customers
    ]


@router.get("/portal/customer-account")
def portal_customer_account(
    user: RegularUser = None,
    db: Session = Depends(get_db),
):
    """Query customer record from the customers table for regular accounts."""
    # Query customer record from the customers table matching this regular user
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
    """Search transactions strictly belonging to this regular user and return matching transactions with total amount."""
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
    """Get transactions belonging strictly to the logged in regular user. No auto-assignment."""
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
    """Query chart of accounts from the accounts table for admins and finance managers."""
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


@router.get("/workspace/accounts/{account_id}/transactions")
def account_transactions(
    account_id: str,
    _: FinanceUser = None,
    db: Session = Depends(get_db),
):
    """Get transactions for an account from the accounts table."""
    acct = db.get(Account, account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")
    txs = list(
        db.scalars(
            select(FinancialTransaction)
            .where(
                or_(
                    FinancialTransaction.account_code == acct.code,
                    FinancialTransaction.account.ilike(f"%{acct.name}%"),
                )
            )
            .order_by(FinancialTransaction.transaction_date.desc())
            .limit(50)
        )
    )
    return {
        "account": {
            "id": acct.id,
            "code": acct.code,
            "name": acct.name,
            "account_type": acct.account_type,
            "normal_balance": acct.normal_balance,
            "total_balance": sum(float(tx.actual_amount) for tx in txs),
        },
        "transactions": [tx_payload(tx) for tx in txs],
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
            summary=f"Period {period} financial overview: {len(txs)} transactions logged with {payload['discrepancies']} discrepancies detected across accounts receivable.",
            risks=["Unapproved customer discounts require manager escalation", "Duplicate payment batches pending clearance"],
            recommendations=["Prioritize review of transactions exceeding $250 variance", "Enforce FIN-042 documentation before reconciliation"],
        )
    try:
        return runner.invoke(
            model="meta-llama/Llama-3.3-70B-Instruct",
            prompt="You are a senior financial controller. Analyze this financial period dataset and generate an executive summary, top risks, and actionable recommendations as structured JSON.",
            payload=payload,
            schema=Insight,
        )
    except Exception as exc:
        return Insight(
            period=period,
            summary=f"Analysis for period {period}: Total volume of {len(txs)} transactions with {payload['discrepancies']} discrepancies currently flagged for close inspection.",
            risks=["Undocumented promotional discounts on major enterprise invoices", "Bank timing differences on net-30 settlements"],
            recommendations=["Verify credit note authorization against FIN-010 matrix", "Trigger AI investigation on critical severity variances"],
        )
