"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(
        self, llm_client: LLMClient | None = None, settings: Settings | None = None
    ) -> None:
        self.settings = settings or get_settings()
        self.llm_client = llm_client or LLMClient(settings=self.settings)

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        if not state.research_notes:
            raise ValidationError("Analyst requires research_notes before running.")

        source_list = "\n".join(f"- {source.title}: {source.snippet}" for source in state.sources)
        response = self.llm_client.complete(
            system_prompt=(
                "You are an analyst agent in a multi-agent research workflow. "
                "Produce concise structured analysis grounded in the provided research. "
                "Use exact source titles in square brackets when citing evidence."
            ),
            user_prompt=(
                f"User query: {state.request.query}\n\n"
                f"Research notes:\n{state.research_notes}\n\n"
                f"Sources:\n{source_list}\n\n"
                "Write sections titled: "
                "Key Claims, Agreements and Disagreements, Weak Evidence, Open Questions. "
                "Each key claim should cite one or more exact source titles in square brackets."
            ),
        )
        state.analysis_notes = response.content
        state.estimated_cost_usd += response.cost_usd or 0.0
        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        return state
