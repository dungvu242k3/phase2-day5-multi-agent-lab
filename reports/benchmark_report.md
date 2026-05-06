# Benchmark Report

## Run Details

| Run | Case | Success | Latency (s) | Cost (USD) | Fact Coverage | Citation Coverage | Citation Precision | Unsupported Claim Rate | Completeness | Structure | Quality | Notes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | graphrag_state_of_the_art | yes | 8.74 | 0.0004 | 0.67 | 1.00 | 1.00 | 0.00 | 1.00 | 0.75 | 8.8 |  |
| baseline | customer_support_workflows | yes | 4.04 | 0.0002 | 1.00 | 1.00 | 1.00 | 0.00 | 0.33 | 0.75 | 8.8 |  |
| baseline | llm_guardrails_summary | yes | 3.74 | 0.0002 | 1.00 | 1.00 | 1.00 | 0.00 | 0.67 | 0.75 | 9.2 |  |
| multi-agent | graphrag_state_of_the_art | yes | 22.36 | 0.0009 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 0.75 | 9.8 |  |
| multi-agent | customer_support_workflows | yes | 15.41 | 0.0006 | 1.00 | 1.00 | 1.00 | 0.00 | 0.33 | 1.00 | 9.0 |  |
| multi-agent | llm_guardrails_summary | yes | 14.09 | 0.0006 | 1.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 10.0 |  |

## Summary

| Run | Avg Latency (s) | Avg Cost (USD) | Success Rate | Avg Fact Coverage | Avg Citation Coverage | Avg Quality | Failure Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 5.51 | 0.0002 | 1.00 | 0.89 | 1.00 | 8.9 | 0.00 |
| multi-agent | 17.29 | 0.0007 | 1.00 | 1.00 | 1.00 | 9.6 | 0.00 |

## Peer Review Notes

### baseline / graphrag_state_of_the_art
Strength: Grounds the answer in the expected benchmark sources.
Risk / failure mode: Main remaining risk is shallow synthesis rather than obvious hallucination.
One concrete improvement: Improve the weakest metric next: fact coverage.
Score: 8.8/10
Trace artifact: reports/traces/baseline_graphrag_state_of_the_art.json

### baseline / customer_support_workflows
Strength: Covers most required facts from the benchmark case.
Risk / failure mode: Main remaining risk is shallow synthesis rather than obvious hallucination.
One concrete improvement: Improve the weakest metric next: completeness.
Score: 8.8/10
Trace artifact: reports/traces/baseline_customer_support_workflows.json

### baseline / llm_guardrails_summary
Strength: Covers most required facts from the benchmark case.
Risk / failure mode: Main remaining risk is shallow synthesis rather than obvious hallucination.
One concrete improvement: Improve the weakest metric next: completeness.
Score: 9.2/10
Trace artifact: reports/traces/baseline_llm_guardrails_summary.json

### multi-agent / graphrag_state_of_the_art
Strength: Covers most required facts from the benchmark case.
Risk / failure mode: Main remaining risk is shallow synthesis rather than obvious hallucination.
One concrete improvement: Improve the weakest metric next: structure.
Score: 9.8/10
Trace artifact: reports/traces/multi-agent_graphrag_state_of_the_art.json

### multi-agent / customer_support_workflows
Strength: Covers most required facts from the benchmark case.
Risk / failure mode: Main remaining risk is shallow synthesis rather than obvious hallucination.
One concrete improvement: Improve the weakest metric next: completeness.
Score: 9.0/10
Trace artifact: reports/traces/multi-agent_customer_support_workflows.json

### multi-agent / llm_guardrails_summary
Strength: Covers most required facts from the benchmark case.
Risk / failure mode: Main remaining risk is shallow synthesis rather than obvious hallucination.
One concrete improvement: Improve the weakest metric next: fact coverage.
Score: 10.0/10
Trace artifact: reports/traces/multi-agent_llm_guardrails_summary.json

