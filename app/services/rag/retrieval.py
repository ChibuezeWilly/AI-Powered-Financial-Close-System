"""Hybrid retrieval with dense (Pinecone) + sparse (BM25) + RRF + reranking."""
from __future__ import annotations

import logging
from typing import Any

from ..embedding_service import bm25_search, reciprocal_rank_fusion
from ..pinecone_service import search_similar

logger = logging.getLogger(__name__)


# ── Retrieval Router ────────────────────────────────────────────────────

def route_query(query: str) -> str:
    """Determine the best retrieval method based on query pattern."""
    query_lower = query.lower().strip()

    # Exact ID lookups → SQL
    id_prefixes = ["inv-", "pay-", "tx-", "je-", "cust-", "bank-"]
    if any(query_lower.startswith(p) for p in id_prefixes):
        return "sql"

    # Policy lookups → hybrid
    policy_keywords = ["policy", "fin-", "procedure", "approval", "threshold", "rule"]
    if any(kw in query_lower for kw in policy_keywords):
        return "hybrid"

    # Relationship queries → graph
    relationship_keywords = ["related to", "connected", "relationship", "linked", "between"]
    if any(kw in query_lower for kw in relationship_keywords):
        return "graph"

    # Default → hybrid
    return "hybrid"


# ── Dense Retrieval ─────────────────────────────────────────────────────

def dense_search(
    query: str,
    top_k: int = 10,
    filter_metadata: dict | None = None,
) -> list[dict]:
    """Search Pinecone for semantically similar chunks."""
    results = search_similar(query, top_k=top_k, filter_metadata=filter_metadata)
    # Normalize to standard format
    return [
        {
            "embedding_id": r["id"],
            "content": r.get("metadata", {}).get("content", ""),
            "document_id": r.get("metadata", {}).get("document_id", ""),
            "document_type": r.get("metadata", {}).get("document_type", ""),
            "policy_id": r.get("metadata", {}).get("policy_id", ""),
            "score": r.get("score", 0),
            "retrieval_method": "Vector",
        }
        for r in results
    ]


# ── Sparse Retrieval ───────────────────────────────────────────────────

def sparse_search(query: str, top_k: int = 10) -> list[dict]:
    """Search BM25 index for exact keyword matches."""
    results = bm25_search(query, top_k=top_k)
    return [
        {
            **r,
            "retrieval_method": "BM25",
            "score": r.get("bm25_score", 0),
        }
        for r in results
    ]


# ── Hybrid Retrieval ───────────────────────────────────────────────────

def hybrid_search(
    query: str,
    top_k: int = 10,
    filter_metadata: dict | None = None,
) -> list[dict]:
    """Combine dense and sparse results using Reciprocal Rank Fusion."""
    dense_results = dense_search(query, top_k=top_k, filter_metadata=filter_metadata)
    sparse_results = sparse_search(query, top_k=top_k)

    fused = reciprocal_rank_fusion(dense_results, sparse_results)

    # Mark retrieval method
    for item in fused:
        item["retrieval_method"] = "Hybrid"

    return fused[:top_k]


# ── Reranking ──────────────────────────────────────────────────────────

def rerank_results(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank results using cross-encoder for improved precision."""
    if not results:
        return []

    try:
        from sentence_transformers import CrossEncoder

        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        pairs = [(query, r.get("content", "")) for r in results]
        scores = model.predict(pairs)

        for i, score in enumerate(scores):
            results[i]["rerank_score"] = float(score)

        reranked = sorted(results, key=lambda x: x.get("rerank_score", 0), reverse=True)
        return reranked[:top_k]
    except Exception as e:
        logger.warning("Reranking failed, returning unranked results: %s", e)
        return results[:top_k]


# ── Main Retrieval Function ────────────────────────────────────────────

def retrieve(
    query: str,
    top_k: int = 10,
    method: str | None = None,
    filter_metadata: dict | None = None,
    rerank: bool = True,
) -> list[dict]:
    """Main retrieval entry point with automatic routing.

    Args:
        query: The search query
        top_k: Number of results to return
        method: Force a specific method ('dense', 'sparse', 'hybrid', 'graph')
        filter_metadata: Pinecone metadata filters
        rerank: Whether to apply cross-encoder reranking
    """
    route = method or route_query(query)

    if route == "sql":
        # SQL queries should be handled by the caller
        return []
    elif route == "dense":
        results = dense_search(query, top_k=top_k * 2, filter_metadata=filter_metadata)
    elif route == "sparse":
        results = sparse_search(query, top_k=top_k * 2)
    elif route == "graph":
        # Graph queries should be handled by neo4j_service
        return []
    else:
        results = hybrid_search(query, top_k=top_k * 2, filter_metadata=filter_metadata)

    if rerank and results:
        results = rerank_results(query, results, top_k=top_k)
    else:
        results = results[:top_k]

    return results


def retrieve_policies(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve relevant policies for a discrepancy investigation."""
    return retrieve(
        query=query,
        top_k=top_k,
        method="hybrid",
        filter_metadata={"document_type": "policy"},
        rerank=True,
    )


def retrieve_procedures(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve relevant procedures."""
    return retrieve(
        query=query,
        top_k=top_k,
        method="hybrid",
        filter_metadata={"document_type": "procedure"},
        rerank=True,
    )
