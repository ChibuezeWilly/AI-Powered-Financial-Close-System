"""Workspace multi-source concurrent search routes."""
from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database.database import SessionLocal, get_db
from ..schema.models import Customer, Document, FinancialTransaction, LedgerEntry, Policy
from .auth import FinanceUser

router = APIRouter(prefix="", tags=["workspace-search"])


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
    except Exception:
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
    except Exception:
        return []


@router.get("/workspace/search")
async def search(q: str = Query(min_length=2), exclude: list[str] = Query(default=[]), _: FinanceUser = None):
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
