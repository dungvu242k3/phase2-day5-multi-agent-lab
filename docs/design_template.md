# Design Template

## Problem

Xây dựng một research assistant nhận câu hỏi mở, thu thập thông tin, phân tích bằng chứng và viết câu trả lời cuối cùng có nguồn tham khảo. Hệ thống phải hỗ trợ cả baseline một-agent và workflow nhiều agent để so sánh chất lượng, độ trễ và khả năng giải thích.

## Why multi-agent?

Single-agent đủ cho câu hỏi ngắn, nhưng với câu hỏi dài và cần nhiều bước thì dễ trộn lẫn nhiệm vụ tìm nguồn, phân tích và viết. Tách thành nhiều agent giúp mỗi bước có responsibility rõ hơn, shared state dễ debug hơn và benchmark minh bạch hơn. Trong benchmark controlled corpus, multi-agent cũng có cơ hội thắng rõ hơn về grounding, fact coverage và trace explanation.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Chọn worker tiếp theo hoặc dừng workflow | `ResearchState` hiện tại | `next_route`, cập nhật `route_history` | Vượt `max_iterations`, worker fail nhưng không có đường fallback |
| Researcher | Chọn tài liệu liên quan và tạo research notes ngắn gọn | `request.query`, `max_sources` | `sources`, `research_notes`, `selected_document_ids` | Chọn nhầm distractor, không tìm ra nguồn usable |
| Analyst | Rút ý chính, điểm đồng thuận và lỗ hổng bằng chứng | `research_notes`, `sources` | `analysis_notes` | Thiếu `research_notes`, LLM call lỗi |
| Writer | Viết câu trả lời cuối cùng cho audience mục tiêu | `research_notes`, `analysis_notes`, `sources`, `audience` | `final_answer` | Thiếu `analysis_notes`, LLM call lỗi |

## Shared state

- `request`: giữ query, audience và số nguồn tối đa.
- `iteration`, `route_history`, `next_route`, `completed`: điều phối workflow và enforce stop condition.
- `candidate_document_ids`, `selected_document_ids`, `sources`, `research_notes`, `analysis_notes`, `final_answer`: artifact chính giữa các bước handoff.
- `estimated_cost_usd`: cộng dồn chi phí từ các lần gọi LLM.
- `agent_results`: lưu output chuẩn hóa của từng agent.
- `trace`: lưu trace event cho giải thích và benchmark.
- `errors`, `validation_warnings`, `last_failed_agent`: phục vụ guardrail và fallback.

## Routing policy

Workflow mặc định là tuyến tính có supervisor gate:

`Supervisor -> Researcher -> Supervisor -> Analyst -> Supervisor -> Writer -> Supervisor -> done`

Rule chính:
- Nếu chưa có `sources` hoặc `research_notes` thì gọi `Researcher`.
- Nếu đã có `research_notes` nhưng chưa có `analysis_notes` thì gọi `Analyst`.
- Nếu đã có `analysis_notes` nhưng chưa có `final_answer` thì gọi `Writer`.
- Nếu đã có `final_answer` thì `done`.
- Nếu worker fail, supervisor chỉ fallback sang `Writer` khi đã có đủ notes; nếu không thì dừng với error.

## Guardrails

- Max iterations: lấy từ `Settings.max_iterations`, mặc định 6.
- Timeout: tất cả live LLM/search calls dùng `Settings.timeout_seconds`.
- Retry: LLM retries bằng `tenacity` với exponential backoff.
- Fallback: benchmark mặc định dùng local corpus cố định; ad-hoc search vẫn có thể fallback sang mock khi thiếu key.
- Validation: `Analyst` yêu cầu `research_notes`, `Writer` yêu cầu `analysis_notes`, final answer phải có source references, workflow fail nếu kết thúc mà không có `final_answer`.

## Benchmark plan

- Cases lấy từ `configs/lab_default.yaml` và corpus ở `data/benchmark_corpus.yaml`.
- Mỗi case chạy qua `baseline` và `multi-agent` trên cùng candidate documents.
- Metric:
  - `latency_seconds`
  - `estimated_cost_usd`
  - `fact_coverage`
  - `citation_coverage`
  - `citation_precision`
  - `unsupported_claim_rate`
  - `completeness_score`
  - `structure_score`
  - `quality_score`
  - `success`
- Artifact:
  - `reports/benchmark_report.md`
  - `reports/traces/*.json`
- Expected outcome:
  - baseline nhanh hơn nhưng dễ bị distractor hoặc thiếu coverage hơn
  - multi-agent có trace rõ hơn, grounding tốt hơn và dễ peer review hơn
