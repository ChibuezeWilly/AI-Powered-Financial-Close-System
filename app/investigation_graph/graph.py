"""Compatibility re-export from app.langgraph.graph."""
from __future__ import annotations

from ..langgraph.graph import (
    build_investigation_graph,
    investigation_graph,
    run_investigation,
)

__all__ = [
    "build_investigation_graph",
    "investigation_graph",
    "run_investigation",
]
