# Multi-Agent Research Lab

Chào mừng bạn đến với repo **Multi-Agent Research Lab**! Đây là một hệ thống nghiên cứu đa tác tử (multi-agent) được xây dựng để so sánh hiệu quả giữa cách tiếp cận đơn tác tử (single-agent baseline) và hệ thống phối hợp đa tác tử (Supervisor + Researcher + Analyst + Writer).

Dự án này sử dụng **LangGraph** để điều phối quy trình làm việc và cung cấp các công cụ để đánh giá (benchmark) chất lượng, độ trễ và chi phí.

---

## 🚀 Hướng dẫn nhanh (Quick Start)

### 1. Chuẩn bị môi trường

Dự án yêu cầu **Python 3.11+**.

#### Trên Windows (PowerShell):
```powershell
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# Cài đặt các thư viện cần thiết (bao gồm cả dev và llm)
pip install -e ".[dev,llm]"
```

#### Trên Linux / macOS:
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo
source .venv/bin/activate

# Cài đặt các thư viện cần thiết
pip install -e ".[dev,llm]"
```

### 2. Cấu hình biến môi trường

Sao chép file `.env.example` thành `.env` và điền các API key cần thiết:

```bash
cp .env.example .env
```

Mở file `.env` và cập nhật các giá trị sau:
- `OPENAI_API_KEY`: API key của OpenAI (bắt buộc).
- `TAVILY_API_KEY`: API key của Tavily (tùy chọn, dùng cho tìm kiếm web).
- `LANGSMITH_API_KEY`: Dùng để theo dõi (trace) luồng chạy trên LangSmith (tùy chọn).

---

## 🛠️ Cách sử dụng

Dự án cung cấp CLI thông qua module `multi_agent_research_lab.cli`.

### 1. Chạy Baseline (Single-Agent)
Chạy một agent duy nhất để trả lời câu hỏi nghiên cứu:
```bash
python -m multi_agent_research_lab.cli baseline --query "Nghiên cứu về GraphRAG và tóm tắt trong 500 chữ"
```

### 2. Chạy Multi-Agent Workflow
Chạy quy trình phối hợp giữa các agent (Supervisor -> Researcher -> Analyst -> Writer):
```bash
python -m multi_agent_research_lab.cli multi-agent --query "Nghiên cứu về GraphRAG và tóm tắt trong 500 chữ"
```

### 3. Chạy Benchmark
So sánh hiệu năng giữa Baseline và Multi-Agent dựa trên một bộ câu hỏi mẫu:
```bash
python -m multi_agent_research_lab.cli benchmark --config configs/lab_default.yaml
```
Kết quả sẽ được lưu vào file `reports/benchmark_report.md`.

---

## 📂 Cấu trúc dự án

```text
.
├── src/multi_agent_research_lab/
│   ├── agents/              # Định nghĩa các Agent (Supervisor, Researcher, v.v.)
│   ├── core/                # Cấu hình, state, schema và xử lý lỗi
│   ├── graph/               # Định nghĩa workflow bằng LangGraph
│   ├── services/            # Client cho LLM, Search, Storage
│   ├── evaluation/          # Logic đánh giá và benchmark
│   ├── observability/       # Logging và Tracing
│   └── cli.py               # Entrypoint chính của ứng dụng
├── configs/                 # File cấu hình YAML cho benchmark
├── data/                    # Dữ liệu mẫu (nếu có)
├── docs/                    # Tài liệu hướng dẫn chi tiết
├── tests/                   # Unit tests
├── notebooks/               # Jupyter Notebooks để thử nghiệm
├── .env.example             # Mẫu file biến môi trường
├── pyproject.toml           # Cấu hình dự án Python (build system, dependencies)
└── Makefile                 # Các lệnh tắt hữu ích (install, test, lint, v.v.)
```

---

## 🧪 Phát triển và Kiểm thử

Nếu bạn muốn đóng góp hoặc tùy chỉnh hệ thống:

- **Chạy Tests:** `pytest` hoặc `make test`
- **Linting:** `ruff check src` hoặc `make lint`
- **Formatting:** `ruff format src` hoặc `make format`
- **Type Checking:** `mypy src` hoặc `make typecheck`

---

## 📝 TODO cho học viên

Nếu bạn đang thực hiện bài lab này, hãy tìm kiếm các marker `TODO(student)` trong mã nguồn để triển khai các phần logic còn thiếu:

```bash
grep -R "TODO(student)" src/
```

Các nhiệm vụ chính bao gồm:
1. Triển khai LLM client.
2. Xây dựng logic điều phối (routing) trong Supervisor.
3. Hoàn thiện các Worker Agent (Researcher, Analyst, Writer).
4. Thiết lập quy trình LangGraph.
5. Phân tích kết quả benchmark.

---

## 🔗 Tài liệu tham khảo

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Building Effective Agents (Anthropic)](https://www.anthropic.com/engineering/building-effective-agents)
