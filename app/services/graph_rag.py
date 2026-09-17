"""Graph RAG service — knowledge graph queries for investigation support."""
from __future__ import annotations

import logging
from typing import Any

from .neo4j_service import (
    build_graph_from_transaction,
    create_policy_node,
    create_relationship,
    get_customer_relationships,
    get_policy_for_discrepancy,
    get_transaction_evidence_graph,
    setup_schema,
)

logger = logging.getLogger(__name__)


def initialize_graph() -> bool:
    """Set up the Neo4j schema and seed base nodes."""
    success = setup_schema()
    if not success:
        logger.warning("Graph initialization failed — Neo4j may be unavailable.")
        return False

    # Seed core policy nodes
    policies = [
        ("FIN-001", "Payment Policy"),
        ("FIN-003", "Refund Policy"),
        ("FIN-004", "Credit Note Policy"),
        ("FIN-005", "Journal Entry Policy"),
        ("FIN-006", "Adjustment Policy"),
        ("FIN-007", "Write-Off Policy"),
        ("FIN-008", "Reconciliation Policy"),
        ("FIN-009", "Month-End Close Policy"),
        ("FIN-010", "Approval Matrix"),
        ("FIN-011", "Access Control Policy"),
        ("FIN-012", "Accounting Period Policy"),
        ("FIN-013", "Exception Management Policy"),
        ("FIN-042", "Discount Authorization Policy"),
    ]

    for pid, title in policies:
        create_policy_node(pid, title, {"status": "active", "version": "1.0"})

    # Create discrepancy-type → policy relationships
    discrepancy_policy_map = {
        "UNDOCUMENTED_DISCOUNT": "FIN-042",
        "PARTIAL_PAYMENT": "FIN-001",
        "OVERPAYMENT": "FIN-001",
        "DUPLICATE_PAYMENT": "FIN-001",
        "MISSING_PAYMENT": "FIN-001",
        "UNAUTHORIZED_DISCOUNT": "FIN-042",
        "BANK_FEE": "FIN-008",
        "CURRENCY_MISMATCH": "FIN-001",
        "LEDGER_ERROR": "FIN-005",
    }

    for disc_type, policy_id in discrepancy_policy_map.items():
        from .neo4j_service import create_generic_node
        create_generic_node("DiscrepancyType", disc_type, {"name": disc_type})
        create_relationship("DiscrepancyType", disc_type, "Policy", policy_id, "GOVERNED_BY")

    logger.info("Graph initialized with %d policies and %d discrepancy mappings",
                len(policies), len(discrepancy_policy_map))
    return True


def build_transaction_graph(transactions: list[dict]) -> int:
    """Populate the knowledge graph from a list of transaction dicts."""
    count = 0
    for tx in transactions:
        try:
            build_graph_from_transaction(tx)
            count += 1
        except Exception as e:
            logger.error("Failed to add transaction %s to graph: %s", tx.get("id"), e)
    logger.info("Added %d/%d transactions to knowledge graph", count, len(transactions))
    return count


def investigate_via_graph(
    transaction_id: str,
    customer_id: str | None = None,
    discrepancy_type: str | None = None,
) -> dict:
    """Run a graph-based investigation for a transaction."""
    result: dict[str, Any] = {
        "evidence_graph": [],
        "related_policies": [],
        "customer_history": [],
    }

    # Get evidence graph
    evidence = get_transaction_evidence_graph(transaction_id)
    result["evidence_graph"] = evidence

    # Get applicable policies
    if discrepancy_type:
        policies = get_policy_for_discrepancy(discrepancy_type)
        result["related_policies"] = policies

    # Get customer history
    if customer_id:
        history = get_customer_relationships(customer_id)
        result["customer_history"] = history

    return result
