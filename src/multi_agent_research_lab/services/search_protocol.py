"""Shared search protocol for workflow-compatible retrieval backends."""

from typing import Protocol

from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClientProtocol(Protocol):
    """Minimal retrieval interface required by workflow and researcher."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Return relevant source documents for a query."""
