"""ARQ worker for asynchronous financial investigations."""
from __future__ import annotations

import asyncio
import json
import logging

from arq.connections import RedisSettings
from dotenv import load_dotenv

from .database.config import resolve_redis_url, settings
from .database.database import SessionLocal
from .schema.models import FinancialTransaction, Investigation
from .services.ai_investigation import investigate_transaction

load_dotenv()
logger = logging.getLogger(__name__)


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(resolve_redis_url(settings.REDIS_URL))


async def run_investigation_job(ctx: dict, transaction_id: str) -> dict:
    """Run one investigation in the worker and persist its result."""
    def execute() -> dict:
        with SessionLocal() as db:
            transaction = db.get(FinancialTransaction, transaction_id)
            if transaction is None:
                raise ValueError(f"Transaction {transaction_id} was not found")
            try:
                result = investigate_transaction(db, transaction)
                db.commit()
                return result
            except Exception:
                investigation = db.get(Investigation, f"INVG-{transaction_id}")
                if investigation:
                    investigation.status = "FAILED"
                    timeline = json.loads(investigation.timeline or "[]")
                    timeline.append("LangGraph investigation failed; human review required.")
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
