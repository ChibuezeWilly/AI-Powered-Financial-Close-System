"""Full ingestion and data sync script for TallyFlow.

1. Ingests all markdown documents (documents/policies, documents/invoices, documents/procedures, knowledge/*)
   into PostgreSQL (documents, policies, knowledge_documents, document_chunks).
2. Generates 1024-d BAAI/bge-m3 embeddings via Hugging Face and upserts to Pinecone.
3. Synchronizes entities and relationships to Neo4j.
4. Distributes transactions across users and ensures regular users have transactions.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from sqlalchemy import select, text
from app.database.config import settings
from app.database.database import SessionLocal
from app.schema.models import (
    Customer,
    Document,
    DocumentChunk,
    FinancialTransaction,
    Invoice,
    KnowledgeDocument,
    LedgerEntry,
    Policy,
    Role,
    User,
)
from app.services.connections import embed_texts, get_neo4j_driver, get_pinecone_index
from app.services.embedding_service import chunk_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestion")

ROOT_DIR = Path(__file__).resolve().parents[2]


def ingest_markdown_documents_to_postgres():
    """Ingest markdown files from documents/ and knowledge/ into PostgreSQL."""
    logger.info("Ingesting markdown documents into PostgreSQL...")
    with SessionLocal() as db:
        # Ingest policies
        policies_dir = ROOT_DIR / "documents" / "policies"
        if policies_dir.exists():
            for pfile in policies_dir.glob("*.md"):
                content = pfile.read_text(encoding="utf-8")
                policy_id = pfile.stem.split("_")[0]
                title = pfile.stem.replace("_", " ").title()
                for line in content.splitlines():
                    if line.startswith("# "):
                        title = line.removeprefix("# ").strip()
                        break
                
                existing = db.scalar(select(Policy).where(Policy.policy_id == policy_id))
                if not existing:
                    existing = Policy(
                        id=f"POL-{policy_id}",
                        policy_id=policy_id,
                        title=title,
                        content=content,
                        effective_date="2026-01-01",
                        status="active",
                    )
                    db.add(existing)
                    db.flush()
                else:
                    existing.content = content
                    existing.title = title

                doc_existing = db.scalar(select(Document).where(Document.filename == pfile.name))
                if not doc_existing:
                    doc = Document(
                        id=f"DOC-{policy_id}",
                        filename=pfile.name,
                        document_type="policy",
                        file_path=str(pfile),
                        file_size=len(content.encode()),
                        status="INDEXED",
                    )
                    db.add(doc)
                    db.flush()
                    chunks = chunk_document(content, doc_id=doc.id, doc_type="policy", metadata={"policy_id": policy_id, "title": title})
                    for chunk_data in chunks:
                        db.add(DocumentChunk(
                            document_id=doc.id,
                            chunk_index=chunk_data["chunk_index"],
                            content=chunk_data["content"],
                            embedding_id=chunk_data["embedding_id"],
                            metadata_json=json.dumps({"policy_id": policy_id, "title": title, "document_type": "policy"}),
                        ))

        # Ingest procedures
        proc_dir = ROOT_DIR / "documents" / "procedures"
        if proc_dir.exists():
            for pfile in proc_dir.glob("*.md"):
                content = pfile.read_text(encoding="utf-8")
                title = pfile.stem.replace("_", " ").title()
                for line in content.splitlines():
                    if line.startswith("# "):
                        title = line.removeprefix("# ").strip()
                        break
                doc_existing = db.scalar(select(Document).where(Document.filename == pfile.name))
                if not doc_existing:
                    doc = Document(
                        id=f"DOC-{pfile.stem[:12]}",
                        filename=pfile.name,
                        document_type="procedure",
                        file_path=str(pfile),
                        file_size=len(content.encode()),
                        status="INDEXED",
                    )
                    db.add(doc)
                    db.flush()
                    chunks = chunk_document(content, doc_id=doc.id, doc_type="procedure", metadata={"title": title})
                    for chunk_data in chunks:
                        db.add(DocumentChunk(
                            document_id=doc.id,
                            chunk_index=chunk_data["chunk_index"],
                            content=chunk_data["content"],
                            embedding_id=chunk_data["embedding_id"],
                            metadata_json=json.dumps({"title": title, "document_type": "procedure"}),
                        ))

        # Ingest knowledge documents
        knowledge_dir = ROOT_DIR / "knowledge"
        if knowledge_dir.exists():
            for kfile in knowledge_dir.rglob("*.md"):
                content = kfile.read_text(encoding="utf-8")
                title = kfile.stem.replace("_", " ").title()
                for line in content.splitlines():
                    if line.startswith("# "):
                        title = line.removeprefix("# ").strip()
                        break
                doc_type = kfile.parent.name
                kdoc = db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.title == title))
                if not kdoc:
                    kdoc = KnowledgeDocument(
                        id=f"KD-{kfile.stem[:16]}",
                        title=title,
                        doc_type=doc_type,
                        content=content,
                        status="active",
                        embedding_status="indexed",
                    )
                    db.add(kdoc)
                
                doc_existing = db.scalar(select(Document).where(Document.filename == kfile.name))
                if not doc_existing:
                    doc = Document(
                        id=f"DOC-{kfile.stem[:16]}",
                        filename=kfile.name,
                        document_type=f"knowledge_{doc_type}",
                        file_path=str(kfile),
                        file_size=len(content.encode()),
                        status="INDEXED",
                    )
                    db.add(doc)
                    db.flush()
                    chunks = chunk_document(content, doc_id=doc.id, doc_type=f"knowledge_{doc_type}", metadata={"title": title})
                    for chunk_data in chunks:
                        db.add(DocumentChunk(
                            document_id=doc.id,
                            chunk_index=chunk_data["chunk_index"],
                            content=chunk_data["content"],
                            embedding_id=chunk_data["embedding_id"],
                            metadata_json=json.dumps({"title": title, "doc_type": doc_type}),
                        ))

        db.commit()
    logger.info("Markdown documents successfully ingested into PostgreSQL.")


def ingest_to_pinecone():
    """Embed chunks with 1024-d BAAI/bge-m3 and upsert to Pinecone."""
    logger.info("Ingesting document chunks into Pinecone (1024-d)...")
    index = get_pinecone_index()
    if index is None:
        logger.warning("Pinecone index unavailable, skipping.")
        return

    with SessionLocal() as db:
        chunks = db.query(DocumentChunk).all()
        logger.info("Found %d chunks to index in Pinecone", len(chunks))
        batch_size = 10
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c.content for c in batch]
            embeddings = embed_texts(texts)
            if not embeddings:
                logger.warning("Embeddings failed for batch %d, skipping batch", i)
                continue

            vectors = []
            for chunk, emb in zip(batch, embeddings):
                meta = json.loads(chunk.metadata_json or "{}")
                meta["content"] = chunk.content[:1000]
                meta["document_id"] = chunk.document_id
                vectors.append({
                    "id": chunk.embedding_id or f"chunk_{chunk.id}",
                    "values": emb,
                    "metadata": meta,
                })
            
            try:
                index.upsert(vectors=vectors, namespace=settings.PINECONE_NAMESPACE)
                logger.info("Upserted batch %d/%d to Pinecone", min(i + len(batch), len(chunks)), len(chunks))
            except Exception as e:
                logger.error("Error upserting to Pinecone: %s", e)


def sync_neo4j_graph():
    """Create graph nodes and relationships in Neo4j for reconciliation investigations."""
    logger.info("Syncing graph nodes to Neo4j...")
    from app.services.connections import neo4j_session
    session = neo4j_session()
    if session is None:
        logger.warning("Neo4j session unavailable, skipping.")
        return

    with SessionLocal() as db:
        txs = db.query(FinancialTransaction).limit(100).all()
        with session:
            for tx in txs:
                query = """
                MERGE (c:Customer {name: $customer})
                MERGE (t:Transaction {id: $tx_id})
                SET t.amount = $amount, t.status = $status, t.period = $period, t.difference = $diff
                MERGE (c)-[:HAS_TRANSACTION]->(t)
                WITH t
                FOREACH (_ IN CASE WHEN $invoice_id IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (i:Invoice {id: $invoice_id})
                    MERGE (t)-[:FOR_INVOICE]->(i)
                )
                """
                session.run(query, {
                    "customer": tx.customer,
                    "tx_id": tx.id,
                    "amount": float(tx.actual_amount),
                    "status": tx.status,
                    "period": tx.period,
                    "diff": float(tx.difference),
                    "invoice_id": tx.invoice_id,
                })
    logger.info("Neo4j graph synchronization complete.")


def assign_users_to_transactions():
    """Ensure regular users exist and have transactions assigned."""
    logger.info("Assigning transactions to users...")
    from app.routers.auth import hash_password

    with SessionLocal() as db:
        # Create a default regular user if not exists
        reg_user = db.scalar(select(User).where(User.email == "user@example.com"))
        if not reg_user:
            reg_user = User(
                email="user@example.com",
                full_name="Alex Morgan",
                password_hash=hash_password("password123"),
                role="REGULAR_USER",
                is_active=True,
            )
            db.add(reg_user)
            db.flush()

        # Assign 40 transactions across periods to this user
        txs = db.query(FinancialTransaction).limit(50).all()
        for tx in txs:
            tx.user_id = reg_user.id

        # Also assign other transactions across users
        users = db.query(User).all()
        all_txs = db.query(FinancialTransaction).all()
        for idx, tx in enumerate(all_txs):
            assigned_user = users[idx % len(users)]
            if not tx.user_id:
                tx.user_id = assigned_user.id

        db.commit()
    logger.info("Transactions assigned to users successfully.")


if __name__ == "__main__":
    ingest_markdown_documents_to_postgres()
    assign_users_to_transactions()
    sync_neo4j_graph()
    ingest_to_pinecone()
    logger.info("All ingestion and synchronization steps completed!")
