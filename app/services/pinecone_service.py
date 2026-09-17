"""Pinecone vector store operations for investigation memory and document retrieval."""
from __future__ import annotations

import logging
from typing import Any

from .connections import get_pinecone_index, embed_texts

logger = logging.getLogger(__name__)


def upsert_investigation(
    transaction_id: str,
    investigation_summary: str,
    metadata: dict[str, Any],
) -> bool:
    """Store a resolved investigation in Pinecone for precedent retrieval."""
    index = get_pinecone_index()
    if index is None:
        logger.warning("Pinecone unavailable – investigation %s not stored.", transaction_id)
        return False

    embeddings = embed_texts([investigation_summary])
    if not embeddings:
        logger.error("Embedding generation failed for %s", transaction_id)
        return False

    vector_id = f"inv-{transaction_id}"
    safe_metadata = {
        "transaction_id": str(metadata.get("transaction_id", transaction_id)),
        "invoice_id": str(metadata.get("invoice_id", "")),
        "customer": str(metadata.get("customer", "")),
        "discrepancy_type": str(metadata.get("discrepancy_type", "")),
        "difference": float(metadata.get("difference", 0)),
        "root_cause": str(metadata.get("root_cause", ""))[:500],
        "recommendation": str(metadata.get("recommendation", ""))[:500],
        "human_decision": str(metadata.get("human_decision", "")),
        "resolution_status": str(metadata.get("resolution_status", "")),
        "period": str(metadata.get("period", "")),
        "confidence": float(metadata.get("confidence", 0)),
        "summary": investigation_summary[:1000],
    }

    try:
        index.upsert(vectors=[(vector_id, embeddings[0], safe_metadata)])
        logger.info("Upserted investigation %s to Pinecone", transaction_id)
        return True
    except Exception as e:
        logger.error("Pinecone upsert failed for %s: %s", transaction_id, e)
        return False


def upsert_document_chunks(
    chunks: list[dict],
    embeddings: list[list[float]],
) -> bool:
    """Upsert document chunks with their embeddings into Pinecone."""
    index = get_pinecone_index()
    if index is None:
        return False

    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        vec_id = chunk.get("embedding_id", f"doc-{chunk.get('document_id', 'unknown')}-{chunk.get('chunk_index', 0)}")
        meta = {
            "document_id": str(chunk.get("document_id", "")),
            "document_type": str(chunk.get("document_type", "")),
            "chunk_index": int(chunk.get("chunk_index", 0)),
            "content": chunk.get("content", "")[:1000],
            "policy_id": str(chunk.get("policy_id", "")),
            "customer_id": str(chunk.get("customer_id", "")),
            "accounting_period": str(chunk.get("accounting_period", "")),
        }
        vectors.append((vec_id, embedding, meta))

    try:
        # Upsert in batches of 100
        for i in range(0, len(vectors), 100):
            batch = vectors[i:i + 100]
            index.upsert(vectors=batch)
        logger.info("Upserted %d chunks to Pinecone", len(vectors))
        return True
    except Exception as e:
        logger.error("Pinecone chunk upsert failed: %s", e)
        return False


def search_similar(
    query: str,
    top_k: int = 10,
    filter_metadata: dict | None = None,
) -> list[dict]:
    """Search Pinecone for similar documents/investigations."""
    index = get_pinecone_index()
    if index is None:
        return []

    embeddings = embed_texts([query])
    if not embeddings:
        return []

    try:
        kwargs: dict[str, Any] = {
            "vector": embeddings[0],
            "top_k": top_k,
            "include_metadata": True,
        }
        if filter_metadata:
            kwargs["filter"] = filter_metadata

        results = index.query(**kwargs)
        matches = []
        for match in results.get("matches", []):
            matches.append({
                "id": match["id"],
                "score": float(match["score"]),
                "metadata": match.get("metadata", {}),
            })
        return matches
    except Exception as e:
        logger.error("Pinecone search failed: %s", e)
        return []


def search_past_investigations(
    query: str,
    top_k: int = 5,
    discrepancy_type: str | None = None,
) -> list[dict]:
    """Search for similar past resolved investigations."""
    filters = {}
    if discrepancy_type:
        filters["discrepancy_type"] = discrepancy_type

    return search_similar(
        query=query,
        top_k=top_k,
        filter_metadata=filters if filters else None,
    )
