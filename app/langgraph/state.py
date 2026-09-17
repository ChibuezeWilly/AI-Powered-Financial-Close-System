"""Shared state for the investigation graph; node outputs are typed schemas."""
from __future__ import annotations

from typing import Any, TypedDict

from .schema import (
    AgentFinding,
    EntityMatch,
    Evidence,
    FinancialCloseReport,
    InvestigationInput,
    ReconciliationResult,
    RootCauseHypothesis,
    VerificationResult,
)


class InvestigationState(TypedDict, total=False):
    request: InvestigationInput
    reconciliation: ReconciliationResult
    entity_matches: list[EntityMatch]
    document_finding: AgentFinding
    policy_finding: AgentFinding
    investigation_finding: AgentFinding
    root_cause: RootCauseHypothesis
    report: FinancialCloseReport
    verification: VerificationResult
    evidence: list[Evidence]
    errors: list[str]
    agent_models: dict[str, str]
    raw_outputs: dict[str, Any]
