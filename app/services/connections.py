"""Centralized connection management for external services.

All connections are lazily initialized and read credentials from environment
variables via config.settings. Never hard-code credentials.
"""
from __future__ import annotations

import logging
from typing import Any

from ..database.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────── Pinecone ───────────────────────────────────────

_pinecone_index = None


def get_pinecone_index():
    """Return a ready-to-use Pinecone index handle (lazy init)."""
    global _pinecone_index
    if _pinecone_index is not None:
        return _pinecone_index

    api_key = settings.PINECONE_API_KEY
    index_name = settings.PINECONE_INDEX
    if not api_key:
        logger.warning("PINE_CONE_API_KEY is not set – Pinecone is unavailable.")
        return None

    try:
        from pinecone import Pinecone, ServerlessSpec

        pc = Pinecone(api_key=api_key)
        existing = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing:
            pc.create_index(
                name=index_name,
                dimension=384,  # MiniLM-L6-v2 dimension
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            logger.info("Created Pinecone index '%s'", index_name)

        _pinecone_index = pc.Index(index_name)
        logger.info("Connected to Pinecone index '%s'", index_name)
        return _pinecone_index
    except Exception as e:
        logger.error("Pinecone connection failed: %s", e)
        return None


# ─────────────────────── Neo4j ──────────────────────────────────────────

_neo4j_driver = None


def get_neo4j_driver():
    """Return a Neo4j driver (lazy init)."""
    global _neo4j_driver
    if _neo4j_driver is not None:
        return _neo4j_driver

    uri = settings.NEO4J_URI
    username = settings.NEO4J_USERNAME
    password = settings.NEO4J_PASSWORD
    if not uri or not username:
        logger.warning("Neo4j credentials not configured – graph DB unavailable.")
        return None

    try:
        from neo4j import GraphDatabase

        _neo4j_driver = GraphDatabase.driver(uri, auth=(username, password))
        _neo4j_driver.verify_connectivity()
        logger.info("Connected to Neo4j at %s", uri)
        return _neo4j_driver
    except Exception as e:
        logger.error("Neo4j connection failed: %s", e)
        return None


def close_neo4j():
    """Gracefully close the Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver is not None:
        _neo4j_driver.close()
        _neo4j_driver = None


def neo4j_session(database: str | None = None):
    """Get a Neo4j session for query execution."""
    driver = get_neo4j_driver()
    if driver is None:
        return None
    db = database or settings.NEO4J_DATABASE
    return driver.session(database=db)


# ─────────────────────── Slack ──────────────────────────────────────────

_slack_client = None


def get_slack_client():
    """Return a Slack WebClient (lazy init)."""
    global _slack_client
    if _slack_client is not None:
        return _slack_client

    token = settings.SLACK_BOT_TOKEN
    if not token:
        logger.warning("SLACK_ACCESS_TOKEN not set – Slack is unavailable.")
        return None

    try:
        from slack_sdk import WebClient

        _slack_client = WebClient(token=token)
        # Quick auth test
        auth = _slack_client.auth_test()
        logger.info("Slack connected as %s", auth.get("user", "unknown"))
        return _slack_client
    except Exception as e:
        logger.error("Slack connection failed: %s", e)
        return None


# ─────────────────────── Embedding Model ────────────────────────────────

_embedding_model = None


def get_embedding_model():
    """Return a SentenceTransformer model for dense embeddings (lazy init)."""
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model

    model_name = settings.EMBEDDING_MODEL
    try:
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer(model_name)
        logger.info("Loaded embedding model '%s' (dim=%d)", model_name, _embedding_model.get_sentence_embedding_dimension())
        return _embedding_model
    except Exception as e:
        logger.error("Failed to load embedding model '%s': %s", model_name, e)
        return None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate dense embeddings for a list of texts."""
    model = get_embedding_model()
    if model is None:
        return []
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


# ─────────────────────── AgentMail ──────────────────────────────────────

_agentmail_client = None
INBOX_ID: str | None = settings.AGENTMAIL_INBOX_ID or None


def get_agentmail_client():
    """Return an AgentMail client (lazy init)."""
    global _agentmail_client, INBOX_ID

    if _agentmail_client is not None:
        return _agentmail_client

    api_key = settings.AGENTMAIL_API_KEY
    if not api_key:
        logger.warning("AGENTMAIL_API_KEY not set – email is unavailable.")
        return None

    try:
        from agentmail import AgentMail

        _agentmail_client = AgentMail(api_key=api_key)
        if not INBOX_ID:
            inbox = _agentmail_client.inboxes.create()
            INBOX_ID = inbox.inbox_id
        return _agentmail_client
    except Exception as e:
        logger.error("AgentMail connection failed: %s", e)
        return None
