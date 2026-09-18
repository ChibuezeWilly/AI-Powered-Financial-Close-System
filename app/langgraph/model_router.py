"""Hugging Face Inference Providers model boundary for LangGraph."""
from __future__ import annotations

import json
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from ..database.config import settings
from .schema import ModelAssignments

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class StructuredModelRunner(Protocol):
    def invoke(self, *, model: str, prompt: str, payload: dict[str, Any], schema: type[SchemaT]) -> SchemaT: ...


import re

class HuggingFaceStructuredRunner:
    """Call Hugging Face Inference Providers and validate structured JSON."""

    def __init__(self, api_key: str) -> None:
        from huggingface_hub import InferenceClient

        self.client = InferenceClient(token=api_key)

    def invoke(self, *, model: str, prompt: str, payload: dict[str, Any], schema: type[SchemaT]) -> SchemaT:
        serialised_payload = json.dumps(
            payload,
            default=lambda value: value.model_dump(mode="json") if isinstance(value, BaseModel) else str(value),
        )
        try:
            response = self.client.chat_completion(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": serialised_payload},
                ],
                max_tokens=2000,
                temperature=0.1,
            )
            content = response.choices[0].message.content or "{}"
        except Exception:
            # Fallback retry with default agent model if specialized model fails
            response = self.client.chat_completion(
                model="meta-llama/Llama-3.3-70B-Instruct",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": serialised_payload},
                ],
                max_tokens=2000,
                temperature=0.1,
            )
            content = response.choices[0].message.content or "{}"

        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        if "```" in content:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
            if match:
                content = match.group(1).strip()
        if not content.startswith("{"):
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start : end + 1]

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
    return bool(settings.HF_TOKEN)


def default_model_runner() -> StructuredModelRunner | None:
    if not is_model_runner_configured():
        return None
    return HuggingFaceStructuredRunner(settings.HF_TOKEN)
