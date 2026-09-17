"""Validated contracts exchanged by the financial-close LangGraph nodes."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class ModelAssignments(BaseModel):
    """Open-source models deliberately assigned to each specialized role."""

    reconciliation: str = "Qwen3-8B"
    investigation: str = "Qwen3-14B"
    document_intelligence: str = "Qwen2.5-VL-72B-Instruct"
    policy: str = "Qwen3-8B"
    root_cause: str = "Qwen3-14B"
    reporting: str = "Qwen3-8B"
    verification: str = "Qwen3-8B"
    embeddings: str = "BAAI/bge-m3"
    reranker: str = "BAAI/bge-reranker-v2-m3"


class Evidence(BaseModel):
    source_id: str
    source_type: Literal["transaction", "document", "policy", "system", "user"]
    excerpt: str = Field(max_length=2_000)
    relevance: float = Field(ge=0, le=1)


class ReconciliationResult(BaseModel):
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    status: Literal["MATCHED", "DISCREPANCY"]
    calculation: str


class EntityMatch(BaseModel):
    candidate_id: str
    score: float = Field(ge=0, le=1)
    match_method: Literal["exact_identifier", "normalized_identifier", "fuzzy"]
    accepted: bool


class AgentFinding(BaseModel):
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    needs_human_review: bool = False


class RootCauseHypothesis(BaseModel):
    cause: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class VerificationResult(BaseModel):
    outcome: Literal["VERIFIED", "NOT_VERIFIED", "NEEDS_HUMAN_REVIEW"]
    checks: list[str] = Field(default_factory=list)
    reason: str


class FinancialCloseReport(BaseModel):
    summary: str
    root_cause: str | None = None
    recommendation: str | None = None
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True


class InvestigationInput(BaseModel):
    """Only normalized facts and extracted document text enter the graph."""

    transaction_id: str
    expected_amount: Decimal
    actual_amount: Decimal
    currency: str = "USD"
    transaction: dict[str, Any] = Field(default_factory=dict)
    entity_candidates: list[dict[str, Any]] = Field(default_factory=list)
    document_facts: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_policies: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
