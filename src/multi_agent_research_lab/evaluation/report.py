"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def _format_optional_float(value: float | None, precision: int = 2) -> str:
    if value is None:
        return ""
    return f"{value:.{precision}f}"


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown."""

    lines = [
        "# Benchmark Report",
        "",
        "## Run Details",
        "",
        (
            "| Run | Case | Success | Latency (s) | Cost (USD) | Fact Coverage | "
            "Citation Coverage | Citation Precision | Unsupported Claim Rate | "
            "Completeness | Structure | Quality | Notes |"
        ),
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = _format_optional_float(item.estimated_cost_usd, 4)
        fact_coverage = _format_optional_float(item.fact_coverage, 2)
        coverage = _format_optional_float(item.citation_coverage, 2)
        precision = _format_optional_float(item.citation_precision, 2)
        unsupported = _format_optional_float(item.unsupported_claim_rate, 2)
        completeness = _format_optional_float(item.completeness_score, 2)
        structure = _format_optional_float(item.structure_score, 2)
        quality = _format_optional_float(item.quality_score, 1)
        lines.append(
            "| "
            f"{item.run_name} | {item.case_id or item.query or ''} | "
            f"{'yes' if item.success else 'no'} | "
            f"{item.latency_seconds:.2f} | {cost} | {fact_coverage} | {coverage} | "
            f"{precision} | {unsupported} | {completeness} | {structure} | "
            f"{quality} | {item.notes} |"
        )

    summary_by_run: dict[str, list[BenchmarkMetrics]] = {}
    for item in metrics:
        summary_by_run.setdefault(item.run_name, []).append(item)

    lines.extend(
        [
            "",
            "## Summary",
            "",
            (
                "| Run | Avg Latency (s) | Avg Cost (USD) | Success Rate | "
                "Avg Fact Coverage | Avg Citation Coverage | Avg Quality | Failure Rate |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for run_name, items in summary_by_run.items():
        avg_latency = sum(item.latency_seconds for item in items) / len(items)
        cost_values = [
            item.estimated_cost_usd for item in items if item.estimated_cost_usd is not None
        ]
        avg_cost = sum(cost_values) / len(cost_values) if cost_values else None
        fact_values = [item.fact_coverage for item in items if item.fact_coverage is not None]
        coverage_values = [
            item.citation_coverage for item in items if item.citation_coverage is not None
        ]
        quality_values = [item.quality_score for item in items if item.quality_score is not None]
        avg_fact = sum(fact_values) / len(fact_values) if fact_values else None
        avg_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else None
        avg_quality = sum(quality_values) / len(quality_values) if quality_values else None
        success_rate = sum(1 for item in items if item.success) / len(items)
        failure_rate = 1 - success_rate
        lines.append(
            f"| {run_name} | {avg_latency:.2f} | {_format_optional_float(avg_cost, 4)} | "
            f"{success_rate:.2f} | {_format_optional_float(avg_fact, 2)} | "
            f"{_format_optional_float(avg_coverage, 2)} | "
            f"{_format_optional_float(avg_quality, 1)} | "
            f"{failure_rate:.2f} |"
        )

    lines.extend(["", "## Peer Review Notes", ""])
    for item in metrics:
        lines.extend(
            [
                f"### {item.run_name} / {item.case_id or item.query or 'case'}",
                f"Strength: {item.strength}",
                f"Risk / failure mode: {item.risk}",
                f"One concrete improvement: {item.improvement}",
                f"Score: {_format_optional_float(item.quality_score, 1)}/10",
                f"Trace artifact: {item.trace_path or ''}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"
