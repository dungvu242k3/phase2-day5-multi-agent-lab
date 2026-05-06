"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from typing import Any

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import (
    AgentExecutionError,
    ValidationError,
)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


MODEL_PRICING_PER_1M_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 5.00, "output": 15.00},
}


class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _estimate_cost(self, input_tokens: int | None, output_tokens: int | None) -> float | None:
        pricing = MODEL_PRICING_PER_1M_TOKENS.get(self.settings.openai_model)
        if pricing is None or input_tokens is None or output_tokens is None:
            return None
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(AgentExecutionError),
    )
    def _request_completion(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AgentExecutionError(
                "The `openai` package is required for live LLM calls. Install the `[llm]` extra."
            ) from exc

        try:
            client = OpenAI(
                api_key=self.settings.openai_api_key, timeout=self.settings.timeout_seconds
            )
            response = client.chat.completions.create(
                model=self.settings.openai_model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            raise AgentExecutionError(f"OpenAI completion failed: {exc}") from exc

        content = self._extract_content(response)
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None)
        output_tokens = getattr(usage, "completion_tokens", None)
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self._estimate_cost(input_tokens, output_tokens),
        )

    def _extract_content(self, response: Any) -> str:
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise AgentExecutionError("OpenAI returned no choices.")
        message = getattr(choices[0], "message", None)
        if message is None:
            raise AgentExecutionError("OpenAI returned an unexpected response shape.")
        content = getattr(message, "content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                text = getattr(item, "text", None)
                if text:
                    parts.append(text)
            joined = "\n".join(parts).strip()
            if joined:
                return joined
        raise AgentExecutionError("OpenAI returned an empty completion.")

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion."""
        if not self.settings.openai_api_key:
            raise ValidationError("OPENAI_API_KEY is required for live LLM calls.")
        return self._request_completion(system_prompt=system_prompt, user_prompt=user_prompt)
