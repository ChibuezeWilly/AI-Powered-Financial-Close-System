"""Neo4j knowledge graph operations for financial entity relationships."""
from __future__ import annotations

import logging
from typing import Any

from .connections import neo4j_session

logger = logging.getLogger(__name__)


# ─────────────────────── Schema Setup ───────────────────────────────────

GRAPH_SCHEMA_CYPHER = """
// Constraints
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT invoice_id IF NOT EXISTS FOR (i:Invoice) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT payment_id IF NOT EXISTS FOR (p:Payment) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT bank_tx_id IF NOT EXISTS FOR (b:BankTransaction) REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT account_id IF NOT EXISTS FOR (a:Account) REQUIRE a.code IS UNIQUE;
CREATE CONSTRAINT ledger_entry_id IF NOT EXISTS FOR (l:LedgerEntry) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT journal_entry_id IF NOT EXISTS FOR (j:JournalEntry) REQUIRE j.id IS UNIQUE;
CREATE CONSTRAINT policy_id IF NOT EXISTS FOR (p:Policy) REQUIRE p.policy_id IS UNIQUE;
CREATE CONSTRAINT discrepancy_id IF NOT EXISTS FOR (d:Discrepancy) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT investigation_id IF NOT EXISTS FOR (inv:Investigation) REQUIRE inv.id IS UNIQUE;
"""


def setup_schema() -> bool:
    """Create constraints and indexes in Neo4j."""
    session = neo4j_session()
    if session is None:
        logger.warning("Neo4j unavailable – schema setup skipped.")
        return False

    try:
        with session:
            for statement in GRAPH_SCHEMA_CYPHER.strip().split(";"):
                stmt = statement.strip()
                if stmt and not stmt.startswith("//"):
                    try:
                        session.run(stmt)
                    except Exception as e:
                        # Constraint may already exist
                        logger.debug("Schema statement skipped: %s", e)
        logger.info("Neo4j schema setup complete")
        return True
    except Exception as e:
        logger.error("Neo4j schema setup failed: %s", e)
        return False


# ─────────────────────── Node Operations ────────────────────────────────

def create_customer_node(customer_id: str, name: str, properties: dict | None = None) -> bool:
    session = neo4j_session()
    if session is None:
        return False
    props = {"id": customer_id, "name": name}
    if properties:
        props.update(properties)
    try:
        with session:
            session.run(
                "MERGE (c:Customer {id: $id}) SET c += $props",
                id=customer_id, props=props,
            )
        return True
    except Exception as e:
        logger.error("Failed to create customer node %s: %s", customer_id, e)
        return False


def create_invoice_node(invoice_id: str, properties: dict | None = None) -> bool:
    session = neo4j_session()
    if session is None:
        return False
    props = {"id": invoice_id}
    if properties:
        props.update(properties)
    try:
        with session:
            session.run(
                "MERGE (i:Invoice {id: $id}) SET i += $props",
                id=invoice_id, props=props,
            )
        return True
    except Exception as e:
        logger.error("Failed to create invoice node %s: %s", invoice_id, e)
        return False


def create_payment_node(payment_id: str, properties: dict | None = None) -> bool:
    session = neo4j_session()
    if session is None:
        return False
    props = {"id": payment_id}
    if properties:
        props.update(properties)
    try:
        with session:
            session.run(
                "MERGE (p:Payment {id: $id}) SET p += $props",
                id=payment_id, props=props,
            )
        return True
    except Exception as e:
        logger.error("Failed to create payment node: %s", e)
        return False


def create_policy_node(policy_id: str, title: str, properties: dict | None = None) -> bool:
    session = neo4j_session()
    if session is None:
        return False
    props = {"policy_id": policy_id, "title": title}
    if properties:
        props.update(properties)
    try:
        with session:
            session.run(
                "MERGE (p:Policy {policy_id: $policy_id}) SET p += $props",
                policy_id=policy_id, props=props,
            )
        return True
    except Exception as e:
        logger.error("Failed to create policy node: %s", e)
        return False


def create_generic_node(label: str, node_id: str, properties: dict | None = None) -> bool:
    session = neo4j_session()
    if session is None:
        return False
    props = {"id": node_id}
    if properties:
        props.update(properties)
    try:
        with session:
            session.run(
                f"MERGE (n:{label} {{id: $id}}) SET n += $props",
                id=node_id, props=props,
            )
        return True
    except Exception as e:
        logger.error("Failed to create %s node %s: %s", label, node_id, e)
        return False


# ─────────────────────── Relationships ──────────────────────────────────

def create_relationship(
    from_label: str, from_id: str,
    to_label: str, to_id: str,
    rel_type: str,
    properties: dict | None = None,
) -> bool:
    """Create a relationship between two nodes."""
    session = neo4j_session()
    if session is None:
        return False
    try:
        with session:
            props_clause = " SET r += $props" if properties else ""
            query = (
                f"MATCH (a:{from_label} {{id: $from_id}}), (b:{to_label} {{id: $to_id}}) "
                f"MERGE (a)-[r:{rel_type}]->(b){props_clause}"
            )
            params: dict[str, Any] = {"from_id": from_id, "to_id": to_id}
            if properties:
                params["props"] = properties
            session.run(query, **params)
        return True
    except Exception as e:
        logger.error("Failed to create relationship %s->%s: %s", from_id, to_id, e)
        return False


# ─────────────────────── Graph Queries ──────────────────────────────────

def get_customer_relationships(customer_id: str) -> list[dict]:
    """Traverse all relationships for a customer."""
    session = neo4j_session()
    if session is None:
        return []
    try:
        with session:
            result = session.run(
                """
                MATCH (c:Customer {id: $id})-[r]->(n)
                RETURN type(r) AS relationship, labels(n) AS node_labels, n AS node
                """,
                id=customer_id,
            )
            return [
                {
                    "relationship": record["relationship"],
                    "node_type": record["node_labels"][0] if record["node_labels"] else "Unknown",
                    "node": dict(record["node"]),
                }
                for record in result
            ]
    except Exception as e:
        logger.error("Customer relationship query failed: %s", e)
        return []


def get_transaction_evidence_graph(transaction_id: str) -> list[dict]:
    """Get the evidence graph for a specific transaction investigation."""
    session = neo4j_session()
    if session is None:
        return []
    try:
        with session:
            result = session.run(
                """
                MATCH path = (inv:Invoice {id: $tx_id})-[*1..3]-(n)
                UNWIND relationships(path) AS r
                WITH startNode(r) AS from_node, endNode(r) AS to_node, type(r) AS rel_type
                RETURN labels(from_node) AS from_labels, from_node.id AS from_id,
                       rel_type, labels(to_node) AS to_labels, to_node.id AS to_id
                """,
                tx_id=transaction_id,
            )
            return [
                {
                    "from_type": record["from_labels"][0] if record["from_labels"] else "Unknown",
                    "from_id": record["from_id"],
                    "relationship": record["rel_type"],
                    "to_type": record["to_labels"][0] if record["to_labels"] else "Unknown",
                    "to_id": record["to_id"],
                }
                for record in result
            ]
    except Exception as e:
        logger.error("Evidence graph query failed for %s: %s", transaction_id, e)
        return []


def get_policy_for_discrepancy(discrepancy_type: str) -> list[dict]:
    """Find policies relevant to a discrepancy type via graph traversal."""
    session = neo4j_session()
    if session is None:
        return []
    try:
        with session:
            result = session.run(
                """
                MATCH (p:Policy)
                WHERE p.covers_discrepancy = $disc_type
                   OR p.title CONTAINS $disc_type
                RETURN p
                """,
                disc_type=discrepancy_type,
            )
            return [dict(record["p"]) for record in result]
    except Exception as e:
        logger.error("Policy query failed: %s", e)
        return []


def build_graph_from_transaction(tx_data: dict) -> bool:
    """Build knowledge graph nodes and relationships from a transaction."""
    customer = tx_data.get("customer", "")
    customer_id = tx_data.get("customer_id", customer)
    invoice_id = tx_data.get("invoice_id", "")
    payment_id = tx_data.get("payment_id")
    tx_id = tx_data.get("id", "")

    create_customer_node(customer_id, customer, {"country": "USA"})
    create_invoice_node(invoice_id, {
        "total": tx_data.get("expected_amount", 0),
        "currency": tx_data.get("currency", "USD"),
        "period": tx_data.get("period", ""),
    })

    create_relationship("Customer", customer_id, "Invoice", invoice_id, "CUSTOMER_HAS_INVOICE")

    if payment_id:
        create_payment_node(payment_id, {
            "amount": tx_data.get("actual_amount", 0),
            "currency": tx_data.get("currency", "USD"),
        })
        create_relationship("Invoice", invoice_id, "Payment", payment_id, "INVOICE_PAID_BY")

    return True
