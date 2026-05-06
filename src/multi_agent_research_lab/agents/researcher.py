"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.services.search_protocol import SearchClientProtocol


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(
        self,
        search_client: SearchClientProtocol | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.search_client = search_client or SearchClient(settings=self.settings)

    def _deduplicate_sources(self, sources: list[SourceDocument]) -> list[SourceDocument]:
        unique_sources: list[SourceDocument] = []
        seen: set[str] = set()
        for source in sources:
            key = source.url or source.title
            if key in seen or not source.snippet.strip():
                continue
            seen.add(key)
            unique_sources.append(source)
        return unique_sources

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        sources = self.search_client.search(
            query=state.request.query,
            max_results=state.request.max_sources,
        )
        filtered_sources = self._deduplicate_sources(sources)
        if not filtered_sources:
            raise AgentExecutionError("Researcher could not find any usable sources.")

        state.sources = filtered_sources
        state.selected_document_ids = [
            str(source.metadata["document_id"])
            for source in filtered_sources
            if "document_id" in source.metadata
        ]
        state.research_notes = "\n".join(
            f"- [{source.title}] ({source.url or 'no-url'}): {source.snippet}"
            for source in filtered_sources
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=state.research_notes,
                metadata={
                    "source_count": len(filtered_sources),
                    "selected_document_ids": state.selected_document_ids,
                },
            )
        )
        if any(source.metadata.get("source_type") == "mock" for source in filtered_sources):
            state.validation_warnings.append(
                "Researcher used mock search results because live search was unavailable."
            )
        return state
