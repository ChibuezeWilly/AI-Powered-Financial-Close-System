"""Model configuration and an injectable structured-output boundary.

The graph is usable without a configured LLM endpoint: affected nodes return a
human-review finding instead of fabricating an analysis.
"""
from __future__ import annotations

import json
from typing import Any, Protocol, TypeVar

import httpx
from pydantic import BaseModel

from ..database.config import settings
from .schema import ModelAssignments

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class StructuredModelRunner(Protocol):
    def invoke(self, *, model: str, prompt: str, payload: dict[str, Any], schema: type[SchemaT]) -> SchemaT: ...


class OpenAICompatibleStructuredRunner:
    """Call any OpenAI-compatible Qwen endpoint and validate its JSON output."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.url = f"{base_url.rstrip('/')}/chat/completions"
        self.api_key = api_key

    def invoke(self, *, model: str, prompt: str, payload: dict[str, Any], schema: type[SchemaT]) -> SchemaT:
        serialised_payload = json.dumps(
            payload,
            default=lambda value: value.model_dump(mode="json") if isinstance(value, BaseModel) else str(value),
        )
        response = httpx.post(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": serialised_payload},
                ],
            },
            timeout=90,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return schema.model_validate_json(content)


def configured_models() -> ModelAssignments:
    return ModelAssignments(
        reconciliation=settings.GENERAL_AGENT_MODEL,
        investigation=settings.INVESTIGATION_MODEL,
        document_intelligence=settings.VISION_MODEL,
        policy=settings.GENERAL_AGENT_MODEL,
        root_cause=settings.INVESTIGATION_MODEL,
        reporting=settings.GENERAL_AGENT_MODEL,
        verification=settings.GENERAL_AGENT_MODEL,
        embeddings=settings.EMBEDDING_MODEL,
        reranker=settings.RERANKING_MODEL,
    )


def is_model_runner_configured() -> bool:
    return bool(settings.LLM_BASE_URL and settings.LLM_API_KEY)


def default_model_runner() -> StructuredModelRunner | None:
    if not is_model_runner_configured():
        return None
    return OpenAICompatibleStructuredRunner(settings.LLM_BASE_URL, settings.LLM_API_KEY)
