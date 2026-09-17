"""RAG ingestion pipeline — index documents into Pinecone and BM25."""
from __future__ import annotations

import logging
from pathlib import Path

from ..embedding_service import (
    chunk_document,
    generate_embeddings,
    build_bm25_index,
)
from ..pinecone_service import upsert_document_chunks

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTS_ROOT = PROJECT_ROOT / "documents"
KNOWLEDGE_ROOT = PROJECT_ROOT / "knowledge"


def ingest_markdown_files(directory: Path, doc_type: str) -> list[dict]:
    """Read all markdown files from a directory and chunk them."""
    all_chunks: list[dict] = []
    if not directory.exists():
        logger.warning("Directory %s does not exist", directory)
        return all_chunks

    for md_file in sorted(directory.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        doc_id = md_file.stem
        metadata = {"document_type": doc_type, "filename": md_file.name}

        # Extract policy ID if present
        for line in content.split("\n")[:10]:
            if "Policy ID" in line or "policy_id" in line.lower():
                parts = line.split(":")
                if len(parts) > 1:
                    metadata["policy_id"] = parts[-1].strip()
                    break

        chunks = chunk_document(content, doc_id, doc_type, metadata)
        all_chunks.extend(chunks)
        logger.info("Chunked %s into %d pieces", md_file.name, len(chunks))

    return all_chunks


def ingest_all_documents() -> dict:
    """Ingest all policies, procedures, concepts, and invoices into vector + BM25."""
    stats = {"policies": 0, "procedures": 0, "concepts": 0, "invoices": 0, "total_chunks": 0}
    all_chunks: list[dict] = []

    # Policies
    policy_chunks = ingest_markdown_files(DOCUMENTS_ROOT / "policies", "policy")
    stats["policies"] = len(policy_chunks)
    all_chunks.extend(policy_chunks)

    # Procedures
    proc_chunks = ingest_markdown_files(DOCUMENTS_ROOT / "procedures", "procedure")
    stats["procedures"] = len(proc_chunks)
    all_chunks.extend(proc_chunks)

    # Knowledge concepts
    concept_chunks = ingest_markdown_files(KNOWLEDGE_ROOT / "concepts", "concept")
    stats["concepts"] = len(concept_chunks)
    all_chunks.extend(concept_chunks)

    # Knowledge procedures
    kp_chunks = ingest_markdown_files(KNOWLEDGE_ROOT / "procedures", "procedure")
    stats["procedures"] += len(kp_chunks)
    all_chunks.extend(kp_chunks)

    # Invoice documents
    inv_chunks = ingest_markdown_files(DOCUMENTS_ROOT / "invoices", "invoice")
    stats["invoices"] = len(inv_chunks)
    all_chunks.extend(inv_chunks)

    # Knowledge investigations
    inv_know = ingest_markdown_files(KNOWLEDGE_ROOT / "investigations", "investigation")
    all_chunks.extend(inv_know)

    # Knowledge graph docs
    graph_chunks = ingest_markdown_files(KNOWLEDGE_ROOT / "graph", "graph_schema")
    all_chunks.extend(graph_chunks)

    stats["total_chunks"] = len(all_chunks)

    if not all_chunks:
        logger.warning("No documents found to ingest.")
        return stats

    # Generate dense embeddings
    texts = [c["content"] for c in all_chunks]
    logger.info("Generating embeddings for %d chunks...", len(texts))
    embeddings = generate_embeddings(texts)

    if embeddings:
        # Upsert to Pinecone
        success = upsert_document_chunks(all_chunks, embeddings)
        if success:
            logger.info("Upserted %d chunks to Pinecone", len(all_chunks))
        else:
            logger.warning("Pinecone upsert failed — continuing with BM25 only")

    # Build BM25 index
    build_bm25_index(all_chunks)
    logger.info("BM25 index built with %d documents", len(all_chunks))

    return stats
