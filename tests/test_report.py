from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.evaluation.report import render_markdown_report


def test_report_renders_markdown() -> None:
    report = render_markdown_report(
        [
            BenchmarkMetrics(
                case_id="sample_case",
                run_name="baseline",
                query="Explain multi-agent systems",
                latency_seconds=1.23,
                fact_coverage=0.5,
                citation_coverage=0.5,
                citation_precision=0.5,
                unsupported_claim_rate=0.0,
                completeness_score=1.0,
                structure_score=0.75,
                quality_score=6.5,
                success=True,
                strength="Clear structure.",
                risk="Needs better evidence.",
                improvement="Add more grounded facts.",
                trace_path="reports/traces/sample.json",
            )
        ]
    )
    assert "Benchmark Report" in report
    assert "baseline" in report
    assert "Citation Coverage" in report
    assert "Fact Coverage" in report
    assert "Peer Review Notes" in report
