"""LangGraph workflow skeleton."""

from collections.abc import Callable

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import (
    AgentExecutionError,
    ValidationError,
)
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.services.search_protocol import SearchClientProtocol

WorkerFactory = Callable[[], BaseAgent]


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        llm_client: LLMClient | None = None,
        search_client: SearchClientProtocol | None = None,
        supervisor: SupervisorAgent | None = None,
        researcher: ResearcherAgent | None = None,
        analyst: AnalystAgent | None = None,
        writer: WriterAgent | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm_client = llm_client or LLMClient(settings=self.settings)
        self.search_client = search_client or SearchClient(settings=self.settings)
        self.supervisor = supervisor or SupervisorAgent(settings=self.settings)
        self.researcher = researcher or ResearcherAgent(
            search_client=self.search_client,
            settings=self.settings,
        )
        self.analyst = analyst or AnalystAgent(llm_client=self.llm_client, settings=self.settings)
        self.writer = writer or WriterAgent(llm_client=self.llm_client, settings=self.settings)
        self._worker_factories: dict[str, WorkerFactory] = {
            "researcher": lambda: self.researcher,
            "analyst": lambda: self.analyst,
            "writer": lambda: self.writer,
        }

    def _state_summary(self, state: ResearchState) -> dict[str, object]:
        return {
            "iteration": state.iteration,
            "sources": len(state.sources),
            "has_research_notes": bool(state.research_notes),
            "has_analysis_notes": bool(state.analysis_notes),
            "has_final_answer": bool(state.final_answer),
            "errors": len(state.errors),
        }

    def _append_trace(
        self,
        state: ResearchState,
        span: dict[str, object],
        input_summary: dict[str, object],
        output_summary: dict[str, object],
        error: str | None = None,
    ) -> None:
        state.add_trace_event(
            str(span["name"]),
            {
                "agent": span["name"],
                "started_at": span["started_at"],
                "duration_seconds": span["duration_seconds"],
                "input_summary": input_summary,
                "output_summary": output_summary,
                "error": error,
            },
        )

    def _validate_state(self, state: ResearchState) -> None:
        if not state.final_answer:
            raise AgentExecutionError("Workflow completed without producing a final answer.")
        if not state.sources:
            state.validation_warnings.append("Workflow completed without live search sources.")
        if "sources" not in state.final_answer.lower() and not any(
            source.title.lower() in state.final_answer.lower() for source in state.sources
        ):
            raise AgentExecutionError(
                "Workflow completed without citations or a source reference section."
            )

    def build(self) -> object:
        """Create a LangGraph graph."""
        return {
            "nodes": ["supervisor", "researcher", "analyst", "writer"],
            "edges": {
                "supervisor": ["researcher", "analyst", "writer", "done"],
                "researcher": ["supervisor"],
                "analyst": ["supervisor"],
                "writer": ["supervisor"],
            },
        }

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        _ = self.build()
        while not state.completed:
            supervisor_input = self._state_summary(state)
            with trace_span("supervisor", {"iteration": state.iteration}) as span:
                self.supervisor.run(state)
            self._append_trace(
                state=state,
                span=span,
                input_summary=supervisor_input,
                output_summary={"next_route": state.next_route, "completed": state.completed},
            )

            route = state.next_route or "done"
            if route == "done":
                break

            worker = self._worker_factories[route]()
            worker_input = self._state_summary(state)
            worker_error: str | None = None
            with trace_span(worker.name, {"iteration": state.iteration}) as span:
                try:
                    worker.run(state)
                    state.last_failed_agent = None
                except (AgentExecutionError, ValidationError) as exc:
                    worker_error = str(exc)
                    state.errors.append(f"{worker.name}: {exc}")
                    state.last_failed_agent = worker.name
            self._append_trace(
                state=state,
                span=span,
                input_summary=worker_input,
                output_summary=self._state_summary(state),
                error=worker_error,
            )

        self._validate_state(state)
        return state
