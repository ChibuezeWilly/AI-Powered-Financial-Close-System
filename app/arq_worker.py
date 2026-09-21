"""ARQ worker for asynchronous financial investigations."""
from __future__ import annotations

import asyncio
import json
import logging

try:
    from arq.connections import RedisSettings
except ImportError:
    class RedisSettings:  # type: ignore
        @classmethod
        def from_dsn(cls, dsn: str):
            return None

from dotenv import load_dotenv

from .database.config import resolve_redis_url, settings
from .database.database import SessionLocal
from .schema.models import FinancialTransaction, Investigation
from .langgraph.ai_investigation import investigate_transaction
from .services.langfuse_service import observe_arq_job

load_dotenv()
logger = logging.getLogger(__name__)


def redis_settings() -> RedisSettings | None:
    if hasattr(RedisSettings, "from_dsn"):
        return RedisSettings.from_dsn(resolve_redis_url(settings.REDIS_URL))
    return None


@observe_arq_job(job_name="financial_investigation_job")
async def run_investigation_job(ctx: dict, transaction_id: str) -> dict:
    """Run one investigation in the worker and persist its result."""
    def execute() -> dict:
        with SessionLocal() as db:
            transaction = db.get(FinancialTransaction, transaction_id)
            if transaction is None:
                raise ValueError(f"Transaction {transaction_id} was not found")

            investigation = db.get(Investigation, f"INVG-{transaction_id}")
            if not investigation:
                investigation = Investigation(
                    id=f"INVG-{transaction_id}",
                    transaction_id=transaction_id,
                    status="RUNNING",
                    evidence="[]",
                    timeline=json.dumps(["Background ARQ worker started LangGraph investigation pipeline."]),
                )
                db.add(investigation)
            else:
                investigation.status = "RUNNING"
                timeline = json.loads(investigation.timeline or "[]")
                timeline.append("Background ARQ worker picked up job; investigation running.")
                investigation.timeline = json.dumps(timeline)
            db.commit()

            try:
                result = investigate_transaction(db, transaction)
                db.commit()
                return result
            except Exception as exc:
                logger.error("Investigation failed for transaction %s: %s", transaction_id, exc)
                investigation = db.get(Investigation, f"INVG-{transaction_id}")
                if investigation:
                    investigation.status = "FAILED"
                    timeline = json.loads(investigation.timeline or "[]")
                    timeline.append(f"LangGraph investigation failed: {exc}; human review required.")
                    investigation.timeline = json.dumps(timeline)
                    db.commit()
                raise

    return await asyncio.to_thread(execute)


async def startup(ctx: dict) -> None:
    logger.info("TallyFlow investigation worker started")


async def shutdown(ctx: dict) -> None:
    logger.info("TallyFlow investigation worker stopped")


class WorkerSettings:
    functions = [run_investigation_job]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = redis_settings()
    max_jobs = 10
    job_timeout = 900
