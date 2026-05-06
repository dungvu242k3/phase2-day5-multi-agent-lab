"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        route = "done"
        if state.iteration >= self.settings.max_iterations:
            state.errors.append("Supervisor stopped execution after reaching max_iterations.")
            state.completed = True
        elif state.last_failed_agent:
            if (
                state.research_notes
                and state.analysis_notes
                and state.last_failed_agent != "writer"
            ):
                route = "writer"
                state.validation_warnings.append(
                    f"Supervisor is falling back to writer after {state.last_failed_agent} failed."
                )
            else:
                state.errors.append(f"Supervisor stopped after {state.last_failed_agent} failed.")
                state.completed = True
            state.last_failed_agent = None
        elif not state.sources or not state.research_notes:
            route = "researcher"
        elif not state.analysis_notes:
            route = "analyst"
        elif not state.final_answer:
            route = "writer"
        else:
            state.completed = True

        if state.completed:
            route = "done"

        state.next_route = route
        state.record_route(route)
        if route == "done":
            state.completed = True
        return state
