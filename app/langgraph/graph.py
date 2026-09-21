"""Composable LangGraph workflow for a complete financial-close investigation."""
from __future__ import annotations

from functools import partial
from langgraph.graph import END, START, StateGraph

from .model_router import StructuredModelRunner, configured_models, default_model_runner
from .nodes import (
    apply_policy,
    determine_root_cause,
    document_intelligence,
    investigate,
    reconcile,
    report,
    resolve_entities,
    verify,
)
from .schema import InvestigationInput
from .state import InvestigationState


def build_investigation_graph(runner: StructuredModelRunner | None = None):
    """Build the graph; inject a provider-specific runner at application startup."""
    graph = StateGraph(InvestigationState)
    graph.add_node("reconciliation", reconcile)
    graph.add_node("entity_resolution", resolve_entities)
    graph.add_node("document_intelligence", partial(document_intelligence, runner=runner))
    graph.add_node("policy", partial(apply_policy, runner=runner))
    graph.add_node("investigation", partial(investigate, runner=runner))
    graph.add_node("root_cause", partial(determine_root_cause, runner=runner))
    graph.add_node("reporting", partial(report, runner=runner))
    graph.add_node("verification", partial(verify, runner=runner))
    graph.add_edge(START, "reconciliation")
    graph.add_edge("reconciliation", "entity_resolution")
    graph.add_edge("entity_resolution", "document_intelligence")
    graph.add_edge("document_intelligence", "policy")
    graph.add_edge("policy", "investigation")
    graph.add_edge("investigation", "root_cause")
    graph.add_edge("root_cause", "reporting")
    graph.add_edge("reporting", "verification")
    graph.add_edge("verification", END)
    return graph.compile()


investigation_graph = build_investigation_graph(default_model_runner())


def run_investigation(request: InvestigationInput, runner: StructuredModelRunner | None = None) -> InvestigationState:
    """Run analysis only; this graph never changes accounting or workflow state."""
    effective_runner = runner if runner is not None else default_model_runner()
    graph = investigation_graph if effective_runner is None else build_investigation_graph(effective_runner)
    models = configured_models()
    return graph.invoke({
        "request": request,
        "evidence": request.evidence,
        "errors": [],
        "agent_models": models.model_dump(),
    })
