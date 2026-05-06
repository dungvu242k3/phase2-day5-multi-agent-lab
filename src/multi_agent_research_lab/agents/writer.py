"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import ValidationError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(
        self, llm_client: LLMClient | None = None, settings: Settings | None = None
    ) -> None:
        self.settings = settings or get_settings()
        self.llm_client = llm_client or LLMClient(settings=self.settings)

    def _has_source_references(self, answer: str, state: ResearchState) -> bool:
        normalized_answer = answer.lower()
        if "sources" in normalized_answer:
            return True
        return any(source.title.lower() in normalized_answer for source in state.sources)

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        if not state.analysis_notes:
            raise ValidationError("Writer requires analysis_notes before running.")

        source_list = "\n".join(
            f"- {source.title} ({source.url or 'no-url'})" for source in state.sources
        )
        response = self.llm_client.complete(
            system_prompt=(
                "You are the writer agent in a multi-agent research workflow. "
                "Write a helpful answer for the requested audience and cite the provided sources. "
                "Use exact source titles in square brackets and end with a Sources section."
            ),
            user_prompt=(
                f"Audience: {state.request.audience}\n"
                f"User query: {state.request.query}\n\n"
                f"Research notes:\n{state.research_notes or ''}\n\n"
                f"Analysis notes:\n{state.analysis_notes}\n\n"
                f"Available sources:\n{source_list}\n\n"
                "Write a concise final answer with a short summary, analysis, "
                "and a Sources section. Cite claims with exact source titles in square brackets."
            ),
        )
        final_response = response
        if not self._has_source_references(response.content, state):
            final_response = self.llm_client.complete(
                system_prompt=(
                    "Revise the answer so it is fully grounded in the provided sources. "
                    "Use exact source titles in square brackets and include a Sources section."
                ),
                user_prompt=(
                    f"Draft answer:\n{response.content}\n\n"
                    f"Available sources:\n{source_list}\n\n"
                    "Revise only as needed to add precise source references and preserve substance."
                ),
            )

        state.final_answer = final_response.content
        state.estimated_cost_usd += (response.cost_usd or 0.0) + (
            0.0 if final_response is response else final_response.cost_usd or 0.0
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=state.final_answer,
                metadata={
                    "input_tokens": final_response.input_tokens,
                    "output_tokens": final_response.output_tokens,
                    "cost_usd": final_response.cost_usd,
                    "used_revision": final_response is not response,
                },
            )
        )
        return state
