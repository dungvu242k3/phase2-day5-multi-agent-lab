from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMResponse


def make_settings(**overrides: object) -> Settings:
    data = {
        "app_env": "test",
        "log_level": "INFO",
        "openai_api_key": None,
        "openai_model": "gpt-4o-mini",
        "langsmith_api_key": None,
        "langsmith_project": "multi-agent-research-lab",
        "tavily_api_key": None,
        "max_iterations": 6,
        "timeout_seconds": 60,
    }
    data.update(overrides)
    return Settings.model_construct(**data)


class FakeLLMClient:
    def __init__(self, content: str) -> None:
        self.content = content

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return LLMResponse(content=self.content, input_tokens=10, output_tokens=20, cost_usd=0.001)


class FakeSearchClient:
    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        return [
            SourceDocument(
                title="Source A",
                url="https://example.com/a",
                snippet=f"Source A about {query}",
                metadata={"source_type": "mock"},
            ),
            SourceDocument(
                title="Source B",
                url="https://example.com/b",
                snippet=f"Source B about {query}",
                metadata={"source_type": "mock"},
            ),
        ][:max_results]


def test_supervisor_routes_researcher_first() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    updated = SupervisorAgent(settings=make_settings(max_iterations=6)).run(state)
    assert updated.next_route == "researcher"
    assert updated.route_history == ["researcher"]


def test_researcher_populates_sources_and_notes() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    updated = ResearcherAgent(
        search_client=FakeSearchClient(),
        settings=make_settings(),
    ).run(state)
    assert len(updated.sources) == 2
    assert updated.research_notes is not None
    assert "Source A" in updated.research_notes


def test_analyst_populates_analysis_notes() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        research_notes="- Source A: notes",
        sources=[SourceDocument(title="Source A", url="https://example.com/a", snippet="notes")],
    )
    updated = AnalystAgent(
        llm_client=FakeLLMClient("Key Claims\n- Claim"),
        settings=make_settings(),
    ).run(state)
    assert updated.analysis_notes == "Key Claims\n- Claim"
    assert updated.estimated_cost_usd > 0


def test_writer_populates_final_answer() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        research_notes="- Source A: notes",
        analysis_notes="Key Claims\n- Claim",
        sources=[SourceDocument(title="Source A", url="https://example.com/a", snippet="notes")],
    )
    updated = WriterAgent(
        llm_client=FakeLLMClient("Final answer\n\nSources:\n- Source A"),
        settings=make_settings(),
    ).run(state)
    assert updated.final_answer is not None
    assert "Sources" in updated.final_answer
