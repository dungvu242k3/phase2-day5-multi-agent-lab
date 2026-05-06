from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
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
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if "Key Claims" in user_prompt:
            return LLMResponse(content="Key Claims\n- Claim [Source A]", cost_usd=0.001)
        return LLMResponse(
            content="Final answer [Source A]\n\nSources:\n- Source A",
            cost_usd=0.001,
        )


class FakeSearchClient:
    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        return [
            SourceDocument(
                title="Source A",
                url="https://example.com/a",
                snippet=f"Evidence about {query}",
                metadata={"source_type": "mock"},
            )
        ]


def test_workflow_runs_end_to_end() -> None:
    settings = make_settings(max_iterations=6)
    llm_client = FakeLLMClient()
    search_client = FakeSearchClient()
    workflow = MultiAgentWorkflow(
        settings=settings,
        supervisor=SupervisorAgent(settings=settings),
        researcher=ResearcherAgent(search_client=search_client, settings=settings),
        analyst=AnalystAgent(llm_client=llm_client, settings=settings),
        writer=WriterAgent(llm_client=llm_client, settings=settings),
    )

    state = workflow.run(ResearchState(request=ResearchQuery(query="Explain multi-agent systems")))

    assert state.final_answer is not None
    assert state.analysis_notes is not None
    assert len(state.trace) >= 4
    assert state.route_history[-1] == "done"
