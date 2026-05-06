import pytest

from multi_agent_research_lab.core.config import Settings
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


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


def test_llm_client_requires_api_key() -> None:
    client = LLMClient(settings=make_settings(openai_api_key=None))
    with pytest.raises(ValidationError):
        client.complete(system_prompt="system", user_prompt="user")


def test_search_client_falls_back_to_mock_sources() -> None:
    client = SearchClient(settings=make_settings(tavily_api_key=None))
    results = client.search("Compare multi-agent systems", max_results=2)
    assert len(results) == 2
    assert all(item.metadata["source_type"] == "mock" for item in results)
