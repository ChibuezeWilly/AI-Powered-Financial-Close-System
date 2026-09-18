"""Queue integration for background LangGraph investigations."""
from __future__ import annotations

from arq import create_pool

from ..arq_worker import redis_settings


async def enqueue_investigation(transaction_id: str) -> str:
    pool = await create_pool(redis_settings())
    try:
        job = await pool.enqueue_job(
            "run_investigation_job",
            transaction_id=transaction_id,
            _job_id=f"investigation-{transaction_id}",
        )
        if job is None:
            return f"investigation-{transaction_id}"
        return job.job_id
    finally:
        await pool.aclose()
