"""Transaction investigation queue and decision execution endpoints."""
from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..langgraph.reconciliation_graph import run_human_decision, run_manager_decision
from ..schema.models import AccountingPeriod, Approval, FinancialTransaction, IdempotentAction, Investigation
from ..schemas import DecisionRequest, ManagerDecisionRequest
from ..services.investigation_queue import enqueue_investigation
from .auth import DecisionUser, ManagerUser, audit

router = APIRouter(prefix="", tags=["transaction-decisions"])


@router.post("/transactions/{transaction_id}/investigate", status_code=202)
async def investigate(transaction_id: str, user: DecisionUser, db: Session = Depends(get_db)):
    tx = db.get(FinancialTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx.status = "INVESTIGATING"
    investigation = db.scalar(select(Investigation).where(Investigation.transaction_id == tx.id))
    if not investigation:
        investigation = Investigation(
            id=f"INVG-{tx.id}",
            transaction_id=tx.id,
            status="PENDING",
            evidence="[]",
            timeline="[]",
        )
        db.add(investigation)
    investigation.status = "PENDING"
    audit(db, user.id, "AI_INVESTIGATION_QUEUED", tx.id)
    db.commit()
    try:
        job_id = await enqueue_investigation(tx.id)
    except Exception as exc:
        investigation.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=503, detail="Investigation queue is unavailable") from exc
    return {"transaction_id": tx.id, "status": "INVESTIGATING", "job_id": job_id}


@router.post("/transactions/{transaction_id}/decision")
async def decide(
    transaction_id: str,
    payload: DecisionRequest,
    user: DecisionUser,
    request: Request,
    db: Session = Depends(get_db),
):
    tx = db.get(FinancialTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    accounting_period = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == tx.period))
    if not accounting_period or accounting_period.status != "OPEN":
        raise HTTPException(status_code=409, detail="Financial decisions are blocked for a closed accounting period")
    if tx.status != "AWAITING_HUMAN_APPROVAL":
        raise HTTPException(status_code=409, detail=f"Cannot decide a transaction in {tx.status}")
    key = request.headers.get("Idempotency-Key", f"{transaction_id}:{payload.decision}")
    prior = db.scalar(select(IdempotentAction).where(IdempotentAction.key == key))
    if prior:
        return json.loads(prior.result)
    db.add(
        Approval(
            transaction_id=tx.id,
            decision=payload.decision,
            reason=payload.reason,
            decided_by=user.id,
        )
    )
    inv = db.scalar(select(Investigation).where(Investigation.transaction_id == tx.id))
    if not inv or inv.status not in {"COMPLETED", "PENDING"}:
        raise HTTPException(status_code=409, detail="Complete the AI investigation before submitting a financial decision")
    result = await run_human_decision(
        db=db,
        transaction=tx,
        actor_id=user.id,
        decision=payload.decision,
        reason=payload.reason,
        idempotency_key=key,
    )
    audit(db, user.id, f"TRANSACTION_{payload.decision.upper()}", tx.id)
    db.add(IdempotentAction(key=key, result=json.dumps(result)))
    db.commit()
    return result


@router.post("/transactions/{transaction_id}/manager-decision")
async def manager_decide(
    transaction_id: str,
    payload: ManagerDecisionRequest,
    user: ManagerUser,
    request: Request,
    db: Session = Depends(get_db),
):
    tx = db.get(FinancialTransaction, transaction_id)
    if not tx or tx.status != "AWAITING_MANAGER_APPROVAL":
        raise HTTPException(status_code=409, detail="No manager decision is pending")
    accounting_period = db.scalar(select(AccountingPeriod).where(AccountingPeriod.code == tx.period))
    if not accounting_period or accounting_period.status != "OPEN":
        raise HTTPException(status_code=409, detail="Financial decisions are blocked for a closed accounting period")

    key = request.headers.get("Idempotency-Key", f"manager:{transaction_id}:{payload.decision}")
    prior = db.scalar(select(IdempotentAction).where(IdempotentAction.key == key))
    if prior:
        return json.loads(prior.result)

    db.add(
        Approval(
            transaction_id=tx.id,
            decision=f"manager_{payload.decision}",
            reason=payload.reason,
            decided_by=user.id,
        )
    )
    result = await run_manager_decision(
        db=db,
        transaction=tx,
        actor_id=user.id,
        decision=payload.decision,
        reason=payload.reason,
        idempotency_key=key,
    )
    audit(db, user.id, f"MANAGER_{payload.decision.upper()}", tx.id)
    db.add(IdempotentAction(key=key, result=json.dumps(result)))
    db.commit()
    return result
