"""Public schemas exchanged between CLI, agents, and evaluators."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AgentName(StrEnum):
    SUPERVISOR = "supervisor"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    CRITIC = "critic"


class ResearchQuery(BaseModel):
    query: str = Field(..., min_length=5)
    max_sources: int = Field(default=5, ge=1, le=20)
    audience: str = "technical learners"


class AgentResult(BaseModel):
    agent: AgentName
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceDocument(BaseModel):
    title: str
    url: str | None = None
    snippet: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkDocument(BaseModel):
    document_id: str
    title: str
    content: str
    url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkFact(BaseModel):
    fact_id: str
    description: str
    keywords: list[str] = Field(default_factory=list)


class BenchmarkExpectation(BaseModel):
    required_facts: list[BenchmarkFact] = Field(default_factory=list)
    expected_source_ids: list[str] = Field(default_factory=list)
    forbidden_phrases: list[str] = Field(default_factory=list)
    required_sections: list[str] = Field(default_factory=list)
    rubric_focus: list[str] = Field(default_factory=list)


class BenchmarkCase(BaseModel):
    case_id: str
    query: str = Field(..., min_length=5)
    audience: str = "technical learners"
    candidate_document_ids: list[str] = Field(default_factory=list)
    expectation: BenchmarkExpectation


class BenchmarkMetrics(BaseModel):
    case_id: str | None = None
    run_name: str
    latency_seconds: float
    query: str | None = None
    estimated_cost_usd: float | None = None
    fact_coverage: float | None = Field(default=None, ge=0, le=1)
    citation_coverage: float | None = Field(default=None, ge=0, le=1)
    citation_precision: float | None = Field(default=None, ge=0, le=1)
    unsupported_claim_rate: float | None = Field(default=None, ge=0, le=1)
    completeness_score: float | None = Field(default=None, ge=0, le=1)
    structure_score: float | None = Field(default=None, ge=0, le=1)
    quality_score: float | None = Field(default=None, ge=0, le=10)
    success: bool = True
    trace_path: str | None = None
    strength: str = ""
    risk: str = ""
    improvement: str = ""
    notes: str = ""
