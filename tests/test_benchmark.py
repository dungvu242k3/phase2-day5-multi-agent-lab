from pathlib import Path

from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import evaluate_case
from multi_agent_research_lab.services.local_corpus import LocalCorpus, LocalCorpusSearchClient


def test_local_corpus_loads_and_returns_ranked_sources() -> None:
    corpus = LocalCorpus.from_path(Path("data/benchmark_corpus.yaml"))
    case = corpus.get_case("graphrag_state_of_the_art")
    search_client = LocalCorpusSearchClient(corpus=corpus, case=case)

    results = search_client.search(case.query, max_results=3)

    assert len(results) == 3
    assert results[0].metadata["source_type"] == "local_corpus"
    assert results[0].metadata["document_id"] in case.candidate_document_ids
    assert all(not item.metadata["is_distractor"] for item in results)


def test_evaluate_case_scores_grounded_answer() -> None:
    corpus = LocalCorpus.from_path(Path("data/benchmark_corpus.yaml"))
    case = corpus.get_case("llm_guardrails_summary")
    search_client = LocalCorpusSearchClient(corpus=corpus, case=case)
    sources = search_client.search(case.query, max_results=3)
    answer = """
### Summary

LLM agent systems need explicit max iterations, timeout, retry, validation, and fallback
behavior to prevent runaway loops and to keep failures understandable [Guardrails Checklist].

### Guardrails

Teams should benchmark latency, cost, quality, citation coverage, and failure rate instead of
judging by a pretty demo alone [Trace and Benchmarking Notes]. Trace data should explain who did
what, what it cost, and where the failure points appeared [Trace and Benchmarking Notes].

### Sources
- [Guardrails Checklist]
- [Trace and Benchmarking Notes]
- [Rollout Guardrails]
""".strip()
    state = ResearchState(
        request=ResearchQuery(query=case.query, audience=case.audience),
        benchmark_case_id=case.case_id,
        candidate_document_ids=case.candidate_document_ids,
        selected_document_ids=[
            str(source.metadata["document_id"])
            for source in sources
            if "document_id" in source.metadata
        ],
        sources=sources,
        final_answer=answer,
        completed=True,
    )

    metrics = evaluate_case(
        run_name="multi-agent",
        case=case,
        state=state,
        trace_path="reports/traces/test.json",
        success=True,
    )

    assert metrics.fact_coverage is not None and metrics.fact_coverage > 0.6
    assert metrics.citation_coverage is not None and metrics.citation_coverage > 0.6
    assert metrics.quality_score is not None and metrics.quality_score > 6.0
    assert metrics.improvement
