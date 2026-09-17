"""Embedding service using sentence-transformers/all-MiniLM-L6-v2.

Handles document chunking, dense embedding generation, and BM25 sparse indexing.
"""
from __future__ import annotations

import logging
import re
from typing import Any

import tiktoken

from .connections import embed_texts, get_embedding_model

logger = logging.getLogger(__name__)

# ── Chunking ────────────────────────────────────────────────────────────

_tokenizer = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = tiktoken.encoding_for_model("gpt-4o")
    return _tokenizer


def chunk_text(
    text: str,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
) -> list[str]:
    """Split text into token-bounded chunks with overlap."""
    tokenizer = _get_tokenizer()
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_str = tokenizer.decode(chunk_tokens)
        if chunk_text_str.strip():
            chunks.append(chunk_text_str.strip())
        start += chunk_size - chunk_overlap
    return chunks


def chunk_document(
    content: str,
    doc_id: str,
    doc_type: str = "policy",
    metadata: dict | None = None,
) -> list[dict]:
    """Chunk a document and return chunk records with metadata."""
    chunks = chunk_text(content)
    result = []
    base_meta = metadata or {}
    for i, chunk in enumerate(chunks):
        result.append({
            "chunk_index": i,
            "content": chunk,
            "document_id": doc_id,
            "document_type": doc_type,
            "embedding_id": f"{doc_id}_chunk_{i}",
            **base_meta,
        })
    return result


# ── Dense Embeddings ────────────────────────────────────────────────────

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate dense embeddings using MiniLM-L6-v2."""
    if not texts:
        return []
    return embed_texts(texts)


def generate_single_embedding(text: str) -> list[float] | None:
    """Generate a single dense embedding vector."""
    results = generate_embeddings([text])
    return results[0] if results else None


# ── BM25 Sparse Index ──────────────────────────────────────────────────

_bm25_corpus: list[list[str]] = []
_bm25_docs: list[dict] = []
_bm25_index = None


def _tokenize_for_bm25(text: str) -> list[str]:
    """Simple whitespace + lowercased tokenization for BM25."""
    text = re.sub(r"[^a-zA-Z0-9\s\-_.]", "", text.lower())
    return text.split()


def build_bm25_index(documents: list[dict]) -> None:
    """Build a BM25 index from a list of document dicts with 'content' key."""
    global _bm25_corpus, _bm25_docs, _bm25_index

    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        logger.error("rank_bm25 not installed – BM25 unavailable.")
        return

    _bm25_docs = documents
    _bm25_corpus = [_tokenize_for_bm25(doc.get("content", "")) for doc in documents]
    _bm25_index = BM25Okapi(_bm25_corpus)
    logger.info("BM25 index built with %d documents", len(documents))


def bm25_search(query: str, top_k: int = 10) -> list[dict]:
    """Search the BM25 index. Returns scored document dicts."""
    if _bm25_index is None or not _bm25_docs:
        return []

    tokenized_query = _tokenize_for_bm25(query)
    scores = _bm25_index.get_scores(tokenized_query)

    scored_docs = sorted(
        zip(scores, _bm25_docs),
        key=lambda x: x[0],
        reverse=True,
    )
    results = []
    for score, doc in scored_docs[:top_k]:
        if score > 0:
            results.append({**doc, "bm25_score": float(score)})
    return results


# ── Hybrid (RRF) ───────────────────────────────────────────────────────

def reciprocal_rank_fusion(
    dense_results: list[dict],
    sparse_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """Merge dense and sparse results using Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for rank, doc in enumerate(dense_results):
        doc_id = doc.get("embedding_id", doc.get("document_id", str(rank)))
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        docs[doc_id] = doc

    for rank, doc in enumerate(sparse_results):
        doc_id = doc.get("embedding_id", doc.get("document_id", str(rank)))
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        if doc_id not in docs:
            docs[doc_id] = doc

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [{**docs[did], "rrf_score": scores[did]} for did in sorted_ids if did in docs]
