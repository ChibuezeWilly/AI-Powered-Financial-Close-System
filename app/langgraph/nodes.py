"""Pure/deterministic and model-backed nodes used by the investigation graph."""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from .model_router import StructuredModelRunner
from .prompts import role_prompts
from .schema import (
    AgentFinding,
    EntityMatch,
    Evidence,
    FinancialCloseReport,
    ModelAssignments,
    RootCauseHypothesis,
    VerificationResult,
)
from .state import InvestigationState


def _normalise(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def reconcile(state: InvestigationState) -> dict:
    request = state["request"]
    difference = request.expected_amount - request.actual_amount
    result = {
        "expected_amount": request.expected_amount,
        "actual_amount": request.actual_amount,
        "difference": difference,
        "status": "MATCHED" if difference == Decimal("0") else "DISCREPANCY",
        "calculation": "expected_amount - actual_amount",
    }
    evidence = [
        *state.get("evidence", []),
        Evidence(
            source_id=request.transaction_id,
            source_type="transaction",
            excerpt="Deterministic reconciliation result",
            relevance=1,
        ),
    ]
    return {"reconciliation": result, "evidence": evidence}


def resolve_entities(state: InvestigationState) -> dict:
    request = state["request"]
    transaction_ids = {
        _normalise(value)
        for key, value in request.transaction.items()
        if key.endswith("id") and value
    }
    matches: list[EntityMatch] = []
    for candidate in request.entity_candidates:
        candidate_id = str(candidate.get("id", ""))
        identifiers = {
            _normalise(value)
            for key, value in candidate.items()
            if key.endswith("id") and value
        }
        exact = bool(transaction_ids & identifiers)
        matches.append(
            EntityMatch(
                candidate_id=candidate_id,
                score=1.0 if exact else 0.0,
                match_method="exact_identifier" if exact else "normalized_identifier",
                accepted=exact,
            )
        )
    return {"entity_matches": matches}


def _model_finding(role: str, state: InvestigationState, runner: StructuredModelRunner | None) -> AgentFinding:
    if runner is None:
        return AgentFinding(
            summary=f"{role} requires a configured structured model runner.",
            confidence=0,
            needs_human_review=True,
        )
    prompts = role_prompts(ModelAssignments.model_validate(state["agent_models"]))
    return runner.invoke(model=state["agent_models"][role], prompt=prompts[role], payload=state, schema=AgentFinding)


def document_intelligence(state: InvestigationState, runner: StructuredModelRunner | None = None) -> dict:
    return {"document_finding": _model_finding("document_intelligence", state, runner)}


def apply_policy(state: InvestigationState, runner: StructuredModelRunner | None = None) -> dict:
    return {"policy_finding": _model_finding("policy", state, runner)}


def investigate(state: InvestigationState, runner: StructuredModelRunner | None = None) -> dict:
    return {"investigation_finding": _model_finding("investigation", state, runner)}


def determine_root_cause(state: InvestigationState, runner: StructuredModelRunner | None = None) -> dict:
    if runner is None:
        hypothesis = RootCauseHypothesis(
            cause="Insufficient model-backed evidence for a root-cause conclusion.",
            confidence=0,
            contradictions=[],
            supporting_evidence_ids=[],
        )
    else:
        prompts = role_prompts(ModelAssignments.model_validate(state["agent_models"]))
        hypothesis = runner.invoke(
            model=state["agent_models"]["root_cause"],
            prompt=prompts["root_cause"],
            payload=state,
            schema=RootCauseHypothesis,
        )
    return {"root_cause": hypothesis}


def report(state: InvestigationState, runner: StructuredModelRunner | None = None) -> dict:
    if runner is None:
        report_output = FinancialCloseReport(
            summary="Investigation requires human review because a structured model runner is not configured.",
            confidence=0,
            requires_human_approval=True,
        )
    else:
        prompts = role_prompts(ModelAssignments.model_validate(state["agent_models"]))
        report_output = runner.invoke(
            model=state["agent_models"]["reporting"],
            prompt=prompts["reporting"],
            payload=state,
            schema=FinancialCloseReport,
        )
    return {"report": report_output}


def verify(state: InvestigationState, runner: StructuredModelRunner | None = None) -> dict:
    if runner is None:
        verification = VerificationResult(
            outcome="NEEDS_HUMAN_REVIEW",
            checks=[],
            reason="No structured post-action verification was provided.",
        )
    else:
        prompts = role_prompts(ModelAssignments.model_validate(state["agent_models"]))
        verification = runner.invoke(
            model=state["agent_models"]["verification"],
            prompt=prompts["verification"],
            payload=state,
            schema=VerificationResult,
        )
    return {"verification": verification}
