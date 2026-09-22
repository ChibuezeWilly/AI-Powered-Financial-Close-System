"""Application startup and shutdown lifecycle management."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from contextlib import asynccontextmanager
from datetime import date
from urllib.parse import urlparse

from fastapi import FastAPI
from sqlalchemy import select

from .database.config import settings
from .database.database import Base, SessionLocal, engine
from .schema.models import (
    AccountingPeriod,
    DocumentChunk,
    FinancialTransaction,
    Investigation,
    User,
)
from .services.embedding_service import build_bm25_index
from .services.oauth import hash_password

logger = logging.getLogger(__name__)


def _ensure_local_redis() -> subprocess.Popen | None:
    if not settings.REDIS_URL:
        return None

    parsed = urlparse(settings.REDIS_URL)
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        return None

    try:
        from redis import Redis

        port = parsed.port or 6379
        client = Redis.from_url(
            settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1
        )
        try:
            client.ping()
            return None
        except Exception:
            pass
        finally:
            client.close()

        redis_process: subprocess.Popen | None = None
        redis_server = shutil.which("redis-server")
        if redis_server:
            redis_process = subprocess.Popen(
                [redis_server, "--port", str(port), "--save", "", "--appendonly", "no"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif shutil.which("docker"):
            container_name = "tallyflow-redis"
            subprocess.run(
                ["docker", "start", container_name], capture_output=True, check=False
            )

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            client = Redis.from_url(
                settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1
            )
            try:
                if client.ping():
                    return redis_process
            except Exception:
                time.sleep(0.25)
            finally:
                client.close()
        return redis_process
    except Exception as exc:
        logger.warning("Local Redis check skipped: %s", exc)
        return None


def _migrate_schema() -> None:
    from sqlalchemy import text

    migrations = [
        "ALTER TABLE investigations ADD COLUMN IF NOT EXISTS agent_findings TEXT DEFAULT '[]'",
        "ALTER TABLE investigations ADD COLUMN IF NOT EXISTS customer_email_draft TEXT",
        "ALTER TABLE investigations ADD COLUMN IF NOT EXISTS manager_escalation_draft TEXT",
        "ALTER TABLE investigations ADD COLUMN IF NOT EXISTS final_summary TEXT",
        "ALTER TABLE investigations ADD COLUMN IF NOT EXISTS model_used VARCHAR(120)",
        "ALTER TABLE investigations ADD COLUMN IF NOT EXISTS fallback_used BOOLEAN DEFAULT FALSE",
        "ALTER TABLE investigation_evidence ADD COLUMN IF NOT EXISTS agent_name VARCHAR(80)",
    ]
    with engine.connect() as conn:
        for stmt in migrations:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as exc:
                logger.debug("Migration notice for '%s': %s", stmt, exc)


def _seed_database() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_schema()
    from .services.seed_data import seed_all as seed_financial_data

    with SessionLocal() as db:
        if not db.scalar(
            select(User).where(User.email == settings.DEFAULT_ADMIN_EMAIL.lower())
        ):
            db.add(
                User(
                    email=settings.DEFAULT_ADMIN_EMAIL.lower(),
                    full_name="Platform Administrator",
                    password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                    role="ADMIN",
                )
            )

        current_year = date.today().year
        for year in range(current_year - 1, current_year + 2):
            for month in range(1, 13):
                code = f"{year}-{month:02d}"
                if not db.scalar(
                    select(AccountingPeriod).where(AccountingPeriod.code == code)
                ):
                    db.add(
                        AccountingPeriod(
                            code=code,
                            year=year,
                            month=month,
                            period_start=f"{year}-{month:02d}-01",
                            period_end=f"{year}-{month:02d}-28",
                        )
                    )
        db.commit()
        seed_financial_data(db)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    redis_process = None
    try:
        redis_process = _ensure_local_redis()
    except Exception as exc:
        logger.warning("Redis startup skipped: %s", exc)

    _seed_database()

    with SessionLocal() as db:
        chunks = db.query(DocumentChunk).all()

        if chunks:
            build_bm25_index(
                [
                    {
                        "content": chunk.content,
                        "document_id": chunk.document_id,
                        "embedding_id": chunk.embedding_id,
                    }
                    for chunk in chunks
                ]
            )
        else:
            logger.info(
                "Database contains no documents yet. Skipping BM25 search index initialization."
            )

    ngrok_authtoken = settings.NGROK_AUTHTOKEN
    if ngrok_authtoken:
        try:
            import ngrok

            listener = await ngrok.forward("localhost:8000", authtoken=ngrok_authtoken)
            app.state.ngrok_listener = listener
        except Exception:
            app.state.ngrok_listener = None

    arq_worker = None
    worker_task = None
    if settings.REDIS_URL:
        try:
            import asyncio
            from arq.worker import create_worker
            from .arq_worker import WorkerSettings

            arq_worker = create_worker(WorkerSettings)
            worker_task = asyncio.create_task(arq_worker.async_run())
            app.state.arq_worker = arq_worker
            app.state.arq_worker_task = worker_task
        except Exception:
            pass

    try:
        yield
    finally:
        if arq_worker is not None:
            try:
                await arq_worker.close()
            except Exception:
                pass
        if worker_task is not None:
            worker_task.cancel()
        if redis_process is not None:
            try:
                redis_process.terminate()
            except Exception:
                pass
        listener = getattr(app.state, "ngrok_listener", None)
        if listener is not None:
            try:
                await listener.close()
            except Exception:
                pass
