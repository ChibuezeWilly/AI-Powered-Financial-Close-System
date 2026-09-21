"""LangGraph orchestration for human-authorized reconciliation decisions.

PostgreSQL remains the durable source of truth. This graph deliberately has
no browser-facing tools and invokes ledger/slack adapters only after the API
has authenticated a human and persisted that person's approval record.
"""
from __future__ import annotations

import asyncio
from typing import Any, Literal, TypedDict

from fastapi import HTTPException
from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..schema.models import AccountingPeriod, FinancialTransaction
from .workflow import escalate_rejection, resolve_approved_adjustment, resolve_manager_rejection


class DecisionState(TypedDict):
    db: Session
    transaction: FinancialTransaction
    actor_id: int
    decision: Literal["approved", "rejected"]
    reason: str
    idempotency_key: str
    result: dict[str, Any]


def _validate_human_decision(state: DecisionState) -> dict:
    tx = state["transaction"]
    period = state["db"].scalar(
        select(AccountingPeriod).where(AccountingPeriod.code == tx.period)
    )
    if not period or period.status != "OPEN":
        raise HTTPException(409, "Financial decisions are blocked for a closed accounting period")
    if tx.status != "AWAITING_HUMAN_APPROVAL":
        raise HTTPException(409, f"Cannot decide a transaction in {tx.status}")
    return {}


def _route_decision(state: DecisionState) -> str:
    return state["decision"]


async def _execute_approved_adjustment(state: DecisionState) -> dict:
    res = await resolve_approved_adjustment(
        state["db"],
        state["transaction"],
        state["idempotency_key"],
        state["actor_id"],
    )
    return {"result": res}


async def _escalate_to_manager(state: DecisionState) -> dict:
    res = escalate_rejection(
        state["db"],
        state["transaction"],
        state["actor_id"],
        state["reason"],
    )
    return {"result": res}


def _build_human_decision_graph():
    graph = StateGraph(DecisionState)
    graph.add_node("validate_human_decision", _validate_human_decision)
    graph.add_node("execute_approved_adjustment", _execute_approved_adjustment)
    graph.add_node("escalate_to_manager", _escalate_to_manager)
    graph.add_edge(START, "validate_human_decision")
    graph.add_conditional_edges(
        "validate_human_decision",
        _route_decision,
        {
            "approved": "execute_approved_adjustment",
            "rejected": "escalate_to_manager",
        },
    )
    graph.add_edge("execute_approved_adjustment", END)
    graph.add_edge("escalate_to_manager", END)
    return graph.compile()


human_decision_graph = _build_human_decision_graph()


class ManagerDecisionState(TypedDict):
    db: Session
    transaction: FinancialTransaction
    actor_id: int
    decision: Literal["approved", "rejected"]
    reason: str
    idempotency_key: str
    result: dict[str, Any]


def _validate_manager_decision(state: ManagerDecisionState) -> dict:
    tx = state["transaction"]
    period = state["db"].scalar(
        select(AccountingPeriod).where(AccountingPeriod.code == tx.period)
    )
    if not period or period.status != "OPEN":
        raise HTTPException(409, "Financial decisions are blocked for a closed accounting period")
    if tx.status != "AWAITING_MANAGER_APPROVAL":
        raise HTTPException(409, f"Cannot submit manager decision for transaction in {tx.status}")
    return {}


async def _manager_approved_node(state: ManagerDecisionState) -> dict:
    res = await resolve_approved_adjustment(
        state["db"],
        state["transaction"],
        state["idempotency_key"],
        state["actor_id"],
    )
    return {"result": res}


async def _manager_rejected_node(state: ManagerDecisionState) -> dict:
    res = await resolve_manager_rejection(
        state["db"],
        state["transaction"],
        state["actor_id"],
        state["reason"],
    )
    return {"result": res}


def _build_manager_decision_graph():
    graph = StateGraph(ManagerDecisionState)
    graph.add_node("validate_manager_decision", _validate_manager_decision)
    graph.add_node("manager_approved", _manager_approved_node)
    graph.add_node("manager_rejected", _manager_rejected_node)
    graph.add_edge(START, "validate_manager_decision")
    graph.add_conditional_edges(
        "validate_manager_decision",
        lambda s: s["decision"],
        {
            "approved": "manager_approved",
            "rejected": "manager_rejected",
        },
    )
    graph.add_edge("manager_approved", END)
    graph.add_edge("manager_rejected", END)
    return graph.compile()


manager_decision_graph = _build_manager_decision_graph()


async def run_human_decision(
    *,
    db: Session,
    transaction: FinancialTransaction,
    actor_id: int,
    decision: Literal["approved", "rejected"],
    reason: str,
    idempotency_key: str,
) -> dict:
    """Run a guarded LangGraph after API authorization and approval persistence."""
    final_state = await human_decision_graph.ainvoke(
        {
            "db": db,
            "transaction": transaction,
            "actor_id": actor_id,
            "decision": decision,
            "reason": reason,
            "idempotency_key": idempotency_key,
        }
    )
    return final_state["result"]


async def run_manager_decision(
    *,
    db: Session,
    transaction: FinancialTransaction,
    actor_id: int,
    decision: Literal["approved", "rejected"],
    reason: str,
    idempotency_key: str,
) -> dict:
    """Run a guarded LangGraph for manager escalation decisions."""
    final_state = await manager_decision_graph.ainvoke(
        {
            "db": db,
            "transaction": transaction,
            "actor_id": actor_id,
            "decision": decision,
            "reason": reason,
            "idempotency_key": idempotency_key,
        }
    )
    return final_state["result"]
