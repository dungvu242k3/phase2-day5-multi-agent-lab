"""Benchmark helpers for controlled single-agent vs multi-agent comparisons."""

import json
from collections.abc import Callable
from math import ceil
from time import perf_counter

import yaml

from multi_agent_research_lab.core.schemas import (
    BenchmarkCase,
    BenchmarkMetrics,
    ResearchQuery,
)
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.services.local_corpus import LocalCorpus, LocalCorpusSearchClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

BenchmarkRunner = Callable[[BenchmarkCase, LocalCorpusSearchClient], ResearchState]


def _contains_fact(answer: str, keywords: list[str]) -> bool:
    if not keywords:
        return False
    normalized_answer = answer.lower()
    hits = sum(1 for keyword in keywords if keyword.lower() in normalized_answer)
    minimum_hits = max(1, min(2, ceil(len(keywords) / 2)))
    return hits >= minimum_hits


def _cited_titles(state: ResearchState) -> set[str]:
    if not state.final_answer:
        return set()
    normalized_answer = state.final_answer.lower()
    return {
        source.title
        for source in state.sources
        if source.title.lower() in normalized_answer
    }


def _fact_coverage(case: BenchmarkCase, state: ResearchState) -> float:
    if not state.final_answer or not case.expectation.required_facts:
        return 0.0
    hits = sum(
        1
        for fact in case.expectation.required_facts
        if _contains_fact(state.final_answer, fact.keywords)
    )
    return hits / len(case.expectation.required_facts)


def _citation_coverage(case: BenchmarkCase, state: ResearchState) -> float:
    expected_ids = set(case.expectation.expected_source_ids)
    if not expected_ids:
        return 0.0
    cited_ids = {
        str(source.metadata.get("document_id"))
        for source in state.sources
        if source.title in _cited_titles(state)
    }
    return len(expected_ids & cited_ids) / len(expected_ids)


def _citation_precision(case: BenchmarkCase, state: ResearchState) -> float:
    cited_titles = _cited_titles(state)
    if not cited_titles:
        return 0.0
    relevant_ids = set(case.expectation.expected_source_ids)
    cited_ids = {
        str(source.metadata.get("document_id"))
        for source in state.sources
        if source.title in cited_titles
    }
    return len(relevant_ids & cited_ids) / len(cited_ids)


def _unsupported_claim_rate(case: BenchmarkCase, state: ResearchState) -> float:
    if not state.final_answer:
        return 1.0
    normalized_answer = state.final_answer.lower()
    cited_titles = _cited_titles(state)
    bad_phrase_hits = sum(
        1 for phrase in case.expectation.forbidden_phrases if phrase.lower() in normalized_answer
    )
    distractor_citations = sum(
        1
        for source in state.sources
        if source.title in cited_titles and source.metadata.get("is_distractor", False)
    )
    denominator = max(
        1,
        len(case.expectation.forbidden_phrases) + len(cited_titles),
    )
    return min(1.0, (bad_phrase_hits + distractor_citations) / denominator)


def _completeness_score(case: BenchmarkCase, state: ResearchState) -> float:
    if not state.final_answer or not case.expectation.required_sections:
        return 0.0
    normalized_answer = state.final_answer.lower()
    hits = sum(
        1
        for section in case.expectation.required_sections
        if section.lower() in normalized_answer
    )
    return hits / len(case.expectation.required_sections)


def _structure_score(state: ResearchState) -> float:
    if not state.final_answer:
        return 0.0
    answer = state.final_answer
    checks = [
        "##" in answer or "###" in answer,
        "- " in answer or "1." in answer,
        "sources" in answer.lower(),
        len([paragraph for paragraph in answer.split("\n\n") if paragraph.strip()]) >= 3,
    ]
    return sum(1 for item in checks if item) / len(checks)


def _quality_score(
    fact_coverage: float,
    citation_coverage: float,
    citation_precision: float,
    unsupported_claim_rate: float,
    completeness_score: float,
    structure_score: float,
) -> float:
    weighted = (
        fact_coverage * 0.30
        + citation_coverage * 0.20
        + citation_precision * 0.15
        + completeness_score * 0.15
        + structure_score * 0.10
        + (1 - unsupported_claim_rate) * 0.10
    )
    return round(weighted * 10, 2)


def _feedback(metrics: BenchmarkMetrics) -> tuple[str, str, str]:
    if metrics.fact_coverage and metrics.fact_coverage >= 0.8:
        strength = "Covers most required facts from the benchmark case."
    elif metrics.citation_coverage and metrics.citation_coverage >= 0.8:
        strength = "Grounds the answer in the expected benchmark sources."
    else:
        strength = "Provides a usable first pass with at least partial structure."

    if metrics.unsupported_claim_rate and metrics.unsupported_claim_rate > 0.2:
        risk = "Mentions unsupported or distractor information, reducing trust."
    elif metrics.citation_precision is not None and metrics.citation_precision < 0.6:
        risk = "Citations are weak or incomplete, so grounding is hard to verify."
    else:
        risk = "Main remaining risk is shallow synthesis rather than obvious hallucination."

    improvement = "Improve the weakest metric next: "
    score_candidates = {
        "fact coverage": metrics.fact_coverage or 0.0,
        "citation coverage": metrics.citation_coverage or 0.0,
        "citation precision": metrics.citation_precision or 0.0,
        "completeness": metrics.completeness_score or 0.0,
        "structure": metrics.structure_score or 0.0,
        "supportedness": 1 - (metrics.unsupported_claim_rate or 0.0),
    }
    weakest = min(score_candidates.items(), key=lambda item: item[1])[0]
    return strength, risk, improvement + weakest + "."


def evaluate_case(
    run_name: str,
    case: BenchmarkCase,
    state: ResearchState,
    trace_path: str,
    success: bool,
) -> BenchmarkMetrics:
    """Score one benchmark case using deterministic quality checks."""

    fact_coverage = _fact_coverage(case, state)
    citation_coverage = _citation_coverage(case, state)
    citation_precision = _citation_precision(case, state)
    unsupported_claim_rate = _unsupported_claim_rate(case, state)
    completeness_score = _completeness_score(case, state)
    structure_score = _structure_score(state)
    quality_score = _quality_score(
        fact_coverage=fact_coverage,
        citation_coverage=citation_coverage,
        citation_precision=citation_precision,
        unsupported_claim_rate=unsupported_claim_rate,
        completeness_score=completeness_score,
        structure_score=structure_score,
    )
    notes = "; ".join(state.errors + state.validation_warnings)
    metrics = BenchmarkMetrics(
        case_id=case.case_id,
        run_name=run_name,
        query=case.query,
        latency_seconds=0.0,
        estimated_cost_usd=state.estimated_cost_usd or None,
        fact_coverage=fact_coverage,
        citation_coverage=citation_coverage,
        citation_precision=citation_precision,
        unsupported_claim_rate=unsupported_claim_rate,
        completeness_score=completeness_score,
        structure_score=structure_score,
        quality_score=quality_score,
        success=success and bool(state.final_answer),
        trace_path=trace_path,
        notes=notes,
    )
    strength, risk, improvement = _feedback(metrics)
    metrics.strength = strength
    metrics.risk = risk
    metrics.improvement = improvement
    return metrics


def run_benchmark(
    run_name: str,
    case: BenchmarkCase,
    runner: BenchmarkRunner,
    search_client: LocalCorpusSearchClient,
    artifact_store: LocalArtifactStore,
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure one benchmark case and write its trace artifact."""

    started = perf_counter()
    success = True
    try:
        state = runner(case, search_client)
    except Exception as exc:
        state = ResearchState(
            request=ResearchQuery(query=case.query, audience=case.audience),
            benchmark_case_id=case.case_id,
            candidate_document_ids=case.candidate_document_ids,
        )
        state.errors.append(str(exc))
        success = False
    latency = perf_counter() - started
    trace_path = f"traces/{run_name}_{case.case_id}.json"
    artifact_store.write_text(trace_path, json.dumps(state.model_dump(), indent=2))
    metrics = evaluate_case(
        run_name=run_name,
        case=case,
        state=state,
        trace_path=f"reports/{trace_path}",
        success=success,
    )
    metrics.latency_seconds = latency
    return state, metrics


def run_benchmark_suite(
    config_path: str,
    runners: dict[str, BenchmarkRunner],
    artifact_store: LocalArtifactStore | None = None,
) -> tuple[list[BenchmarkMetrics], str]:
    """Run the controlled benchmark suite and write markdown artifacts."""

    with open(config_path, encoding="utf-8") as file:
        config = yaml.safe_load(file)

    benchmark_config = config.get("benchmark", {})
    corpus = LocalCorpus.from_path(benchmark_config["corpus_path"])
    cases = corpus.list_cases(benchmark_config.get("case_ids"))
    store = artifact_store or LocalArtifactStore()
    metrics: list[BenchmarkMetrics] = []

    for run_name, runner in runners.items():
        for case in cases:
            search_client = LocalCorpusSearchClient(corpus=corpus, case=case)
            _, item = run_benchmark(
                run_name=run_name,
                case=case,
                runner=runner,
                search_client=search_client,
                artifact_store=store,
            )
            metrics.append(item)

    report = render_markdown_report(metrics)
    store.write_text("benchmark_report.md", report)
    return metrics, report
