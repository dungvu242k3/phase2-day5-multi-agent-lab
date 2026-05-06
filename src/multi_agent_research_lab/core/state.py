"""Shared state for the multi-agent workflow.

Students should extend this file when adding new agents, outputs, or evaluation metrics.
"""

from typing import Any

from pydantic import BaseModel, Field

from multi_agent_research_lab.core.schemas import AgentResult, ResearchQuery, SourceDocument


class ResearchState(BaseModel):
    """Single source of truth passed through the workflow."""

    request: ResearchQuery
    benchmark_case_id: str | None = None
    iteration: int = 0
    route_history: list[str] = Field(default_factory=list)
    next_route: str | None = None
    completed: bool = False

    candidate_document_ids: list[str] = Field(default_factory=list)
    selected_document_ids: list[str] = Field(default_factory=list)
    sources: list[SourceDocument] = Field(default_factory=list)
    research_notes: str | None = None
    analysis_notes: str | None = None
    final_answer: str | None = None
    estimated_cost_usd: float = 0.0

    agent_results: list[AgentResult] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    last_failed_agent: str | None = None

    def record_route(self, route: str) -> None:
        self.route_history.append(route)
        self.iteration += 1

    def add_trace_event(self, name: str, payload: dict[str, Any]) -> None:
        self.trace.append({"name": name, "payload": payload})
