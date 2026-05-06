"""Command-line entrypoint for the lab starter."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import LabError
from multi_agent_research_lab.core.schemas import (
    AgentName,
    AgentResult,
    BenchmarkCase,
    ResearchQuery,
)
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark_suite
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.local_corpus import LocalCorpusSearchClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _run_baseline(query: str) -> ResearchState:
    settings = get_settings()
    llm_client = LLMClient(settings=settings)
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    response = llm_client.complete(
        system_prompt=(
            "You are a single-agent research assistant. "
            "Answer the user's request clearly for the specified audience "
            "and include a brief sources note if relevant."
        ),
        user_prompt=(
            f"Audience: {request.audience}\n"
            f"Research query: {request.query}\n\n"
            "Provide a concise but informative answer."
        ),
    )
    state.final_answer = response.content
    state.estimated_cost_usd = response.cost_usd or 0.0
    state.agent_results.append(
        AgentResult(
            agent=AgentName.WRITER,
            content=response.content,
            metadata={
                "mode": "baseline",
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            },
        )
    )
    state.add_trace_event(
        "baseline",
        {
            "agent": "baseline",
            "input_summary": {"query": request.query, "audience": request.audience},
            "output_summary": {"has_final_answer": True},
            "error": None,
        },
    )
    state.completed = True
    return state


def _run_multi_agent(query: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


def _run_baseline_case(
    case: BenchmarkCase, search_client: LocalCorpusSearchClient
) -> ResearchState:
    settings = get_settings()
    llm_client = LLMClient(settings=settings)
    candidate_documents = search_client.get_candidate_documents()
    state = ResearchState(
        request=ResearchQuery(query=case.query, audience=case.audience, max_sources=3),
        benchmark_case_id=case.case_id,
        candidate_document_ids=case.candidate_document_ids,
        selected_document_ids=case.candidate_document_ids,
    )
    context_bundle = search_client.build_context_bundle()
    response = llm_client.complete(
        system_prompt=(
            "You are a single-agent research assistant. "
            "Read the raw evidence bundle, answer the user's question in one pass, "
            "use exact source titles in square brackets, and end with a Sources section."
        ),
        user_prompt=(
            f"Audience: {case.audience}\n"
            f"User query: {case.query}\n"
            f"Rubric focus: {'; '.join(case.expectation.rubric_focus)}\n\n"
            "Candidate evidence bundle:\n"
            f"{context_bundle}\n\n"
            "Write the final answer directly. Do not show intermediate analysis."
        ),
    )
    state.sources = [
        source
        for source in search_client.search(case.query, max_results=len(candidate_documents))
    ]
    state.final_answer = response.content
    state.estimated_cost_usd = response.cost_usd or 0.0
    state.add_trace_event(
        "baseline",
        {
            "agent": "baseline",
            "input_summary": {
                "case_id": case.case_id,
                "candidate_document_ids": case.candidate_document_ids,
                "candidate_source_count": len(candidate_documents),
            },
            "output_summary": {"has_final_answer": True},
            "error": None,
        },
    )
    state.agent_results.append(
        AgentResult(
            agent=AgentName.WRITER,
            content=response.content,
            metadata={
                "mode": "baseline",
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
                "candidate_document_ids": case.candidate_document_ids,
            },
        )
    )
    state.completed = True
    return state


def _run_multi_agent_case(
    case: BenchmarkCase, search_client: LocalCorpusSearchClient
) -> ResearchState:
    state = ResearchState(
        request=ResearchQuery(query=case.query, audience=case.audience, max_sources=3),
        benchmark_case_id=case.case_id,
        candidate_document_ids=case.candidate_document_ids,
    )
    workflow = MultiAgentWorkflow(search_client=search_client)
    return workflow.run(state)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the single-agent baseline."""

    _init()
    try:
        state = _run_baseline(query)
    except LabError as exc:
        console.print(Panel.fit(str(exc), title="Baseline Error", style="red"))
        raise typer.Exit(code=2) from exc
    console.print(Panel.fit(state.final_answer or "", title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    try:
        result = _run_multi_agent(query)
    except LabError as exc:
        console.print(Panel.fit(str(exc), title="Workflow Error", style="red"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    config: Annotated[Path, typer.Option("--config", "-c", help="Path to benchmark config")] = Path(
        "configs/lab_default.yaml"
    ),
) -> None:
    """Run the configured benchmark suite and write markdown artifacts."""

    _init()
    try:
        _, report = run_benchmark_suite(
            config_path=str(config),
            runners={
                "baseline": _run_baseline_case,
                "multi-agent": _run_multi_agent_case,
            },
            artifact_store=LocalArtifactStore(),
        )
    except LabError as exc:
        console.print(Panel.fit(str(exc), title="Benchmark Error", style="red"))
        raise typer.Exit(code=2) from exc
    console.print(
        Panel.fit("Saved report to reports/benchmark_report.md", title="Benchmark Complete")
    )
    console.print(report)


if __name__ == "__main__":
    app()
