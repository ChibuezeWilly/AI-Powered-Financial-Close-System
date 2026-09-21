"""Langfuse observability service for ARQ background jobs and LangGraph investigation pipelines."""
from __future__ import annotations

import logging
from typing import Any
from functools import wraps

from ..database.config import settings

logger = logging.getLogger(__name__)

_langfuse_client = None


def get_langfuse_client():
    """Return a singleton Langfuse client if configured, otherwise None."""
    global _langfuse_client
    if _langfuse_client is not None:
        return _langfuse_client

    pub_key = settings.LANGFUSE_PUBLIC_KEY
    sec_key = settings.LANGFUSE_SECRET_KEY
    host = settings.LANGFUSE_HOST or settings.LANGFUSE_BASE_URL or "https://cloud.langfuse.com"

    if pub_key and sec_key:
        try:
            from langfuse import Langfuse
            _langfuse_client = Langfuse(
                public_key=pub_key,
                secret_key=sec_key,
                host=host,
            )
            logger.info("Langfuse observability initialized successfully (host: %s)", host)
        except Exception as exc:
            logger.warning("Failed to initialize Langfuse client: %s", exc)
            _langfuse_client = None
    return _langfuse_client


def observe_arq_job(job_name: str = "investigation_job"):
    """Decorator to trace an ARQ background job in Langfuse."""
    def decorator(fn):
        @wraps(fn)
        async def wrapper(ctx: dict, transaction_id: str, *args, **kwargs):
            client = get_langfuse_client()
            if not client:
                return await fn(ctx, transaction_id, *args, **kwargs)

            trace_id = f"tx-{transaction_id}"
            try:
                from langfuse import observe
                # Set trace context for the execution
                client.update_current_trace(
                    name=f"investigation:{transaction_id}",
                    session_id=f"tx-{transaction_id}",
                    tags=["arq-worker", "investigation", "financial-close"],
                    metadata={"transaction_id": transaction_id, "job_name": job_name},
                )
            except Exception as e:
                logger.debug("Langfuse trace setup note: %s", e)

            try:
                result = await fn(ctx, transaction_id, *args, **kwargs)
                try:
                    client.update_current_trace(
                        output={"status": "COMPLETED", "result_summary": str(result)[:500]},
                    )
                    client.flush()
                except Exception:
                    pass
                return result
            except Exception as exc:
                try:
                    client.update_current_trace(
                        output={"status": "FAILED", "error": str(exc)},
                    )
                    client.flush()
                except Exception:
                    pass
                raise exc
        return wrapper
    return decorator


def trace_langgraph_step(
    step_name: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any] | None = None,
    model: str | None = None,
    error: str | None = None,
) -> None:
    """Record a span or generation for a LangGraph pipeline node in Langfuse."""
    client = get_langfuse_client()
    if not client:
        return

    try:
        if model:
            client.start_generation(
                name=step_name,
                model=model,
                input=inputs,
                output=outputs,
            )
        else:
            client.start_span(
                name=step_name,
                input=inputs,
                output=outputs,
            )
    except Exception as exc:
        logger.debug("Langfuse step recording note: %s", exc)
