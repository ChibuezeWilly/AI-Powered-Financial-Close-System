"""RAG ingestion pipeline — index documents into Pinecone and BM25."""
from __future__ import annotations

import logging
import json
from hashlib import sha256
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..embedding_service import (
    chunk_document,
    generate_embeddings,
    build_bm25_index,
)
from ..pinecone_service import upsert_document_chunks
from ..graph_rag import initialize_graph
from ..neo4j_service import create_generic_node, create_policy_node
from ...schema.models import Document, DocumentChunk, KnowledgeDocument, Policy

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


def _sync_postgres(db: Session, chunks: list[dict]) -> dict:
    """Upsert source documents and chunks without duplicating a re-run."""
    document_ids: set[str] = set()
    documents: dict[str, Document] = {}
    storage_ids: dict[str, str] = {}
    for chunk in chunks:
        source_document_id = str(chunk["document_id"])
        document_id = storage_ids.setdefault(source_document_id, f"DOC-{sha256(source_document_id.encode()).hexdigest()[:28]}")
        document_ids.add(document_id)
        document = documents.get(document_id) or db.get(Document, document_id)
        if not document:
            document = Document(id=document_id, filename=chunk.get("filename", document_id), document_type=chunk["document_type"])
            db.add(document)
        documents[document_id] = document
        document.filename = chunk.get("filename", document.filename)
        document.document_type = chunk["document_type"]
        document.file_path = str(DOCUMENTS_ROOT if chunk["document_type"] in {"invoice", "policy", "procedure"} else KNOWLEDGE_ROOT)
        document.status = "INDEXED"

        existing = db.scalar(select(DocumentChunk).where(DocumentChunk.document_id == document_id, DocumentChunk.chunk_index == chunk["chunk_index"]))
        if not existing:
            existing = DocumentChunk(document_id=document_id, chunk_index=chunk["chunk_index"], content=chunk["content"])
            db.add(existing)
        existing.content = chunk["content"]
        existing.embedding_id = chunk["embedding_id"]
        existing.metadata_json = json.dumps({"source_document_id": source_document_id, **{key: value for key, value in chunk.items() if key != "content"}})

    for document_id in document_ids:
        document = documents.get(document_id) or db.get(Document, document_id)
        if document:
            document.records_created = sum(1 for chunk in chunks if storage_ids[str(chunk["document_id"])] == document_id)

    for chunk in chunks:
        if chunk["document_type"] == "policy" and chunk.get("policy_id") and chunk["chunk_index"] == 0:
            policy = db.scalar(select(Policy).where(Policy.policy_id == chunk["policy_id"]))
            if not policy:
                policy = Policy(id=f"POL-{chunk['policy_id']}", policy_id=chunk["policy_id"], title=chunk.get("filename", chunk["policy_id"]), effective_date="2026-01-01", content="")
                db.add(policy)
            policy.document_id = storage_ids[str(chunk["document_id"])]
            policy.content = "\n".join(item["content"] for item in chunks if item["document_id"] == chunk["document_id"])
            policy.status = "active"

        if chunk["document_type"] in {"concept", "procedure", "investigation", "graph_schema"} and chunk["chunk_index"] == 0:
            knowledge_id = f"KD-{sha256(str(chunk['document_id']).encode()).hexdigest()[:28]}"
            knowledge = db.get(KnowledgeDocument, knowledge_id)
            if not knowledge:
                knowledge = KnowledgeDocument(id=knowledge_id, title=chunk.get("filename", chunk["document_id"]), doc_type=chunk["document_type"], content="")
                db.add(knowledge)
            knowledge.content = "\n".join(item["content"] for item in chunks if item["document_id"] == chunk["document_id"])
            knowledge.embedding_status = "indexed"
    return {"postgres_documents": len(document_ids), "postgres_chunks": len(chunks)}


def _sync_neo4j(chunks: list[dict]) -> bool:
    graph_ready = initialize_graph()
    if not graph_ready:
        return False
    for chunk in chunks:
        if chunk["chunk_index"] != 0:
            continue
        if chunk["document_type"] == "policy" and chunk.get("policy_id"):
            create_policy_node(chunk["policy_id"], chunk.get("filename", chunk["policy_id"]), {"document_id": chunk["document_id"]})
        else:
            create_generic_node("KnowledgeDocument", str(chunk["document_id"]), {"title": chunk.get("filename", chunk["document_id"]), "document_type": chunk["document_type"]})
    return True


def ingest_all_documents(db: Session | None = None, *, include_vectors: bool = True) -> dict:
    """Synchronize bundled knowledge into PostgreSQL, Pinecone, BM25, and Neo4j."""
    stats = {"policies": 0, "procedures": 0, "concepts": 0, "invoices": 0, "total_chunks": 0, "embedding_dimension": 1024, "pinecone_indexed": False, "neo4j_indexed": False}
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

    # Build BM25 index
    build_bm25_index(all_chunks)
    logger.info("BM25 index built with %d documents", len(all_chunks))

    if db is not None:
        stats.update(_sync_postgres(db, all_chunks))
    stats["neo4j_indexed"] = _sync_neo4j(all_chunks)

    # Generate dense embeddings only after durable stores have been synchronized.
    if include_vectors:
        texts = [chunk["content"] for chunk in all_chunks]
        logger.info("Generating embeddings for %d chunks...", len(texts))
        embeddings = generate_embeddings(texts)
        if embeddings:
            stats["pinecone_indexed"] = upsert_document_chunks(all_chunks, embeddings)
            if stats["pinecone_indexed"]:
                logger.info("Upserted %d chunks to Pinecone", len(all_chunks))
            else:
                logger.warning("Pinecone upsert failed — continuing with BM25 only")

    return stats
