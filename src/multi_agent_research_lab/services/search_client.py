"""Search client abstraction for ResearcherAgent."""

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client skeleton."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _mock_search(self, query: str, max_results: int, reason: str) -> list[SourceDocument]:
        normalized_query = " ".join(query.split())
        sources = [
            SourceDocument(
                title="Background overview",
                url="https://example.com/background-overview",
                snippet=(
                    "Mock source summarizing background information relevant to: "
                    f"{normalized_query}."
                ),
                metadata={"source_type": "mock", "fallback_reason": reason},
            ),
            SourceDocument(
                title="Recent developments",
                url="https://example.com/recent-developments",
                snippet=(
                    "Mock source outlining recent developments, tradeoffs, "
                    f"and known limitations for {normalized_query}."
                ),
                metadata={"source_type": "mock", "fallback_reason": reason},
            ),
            SourceDocument(
                title="Operational guidance",
                url="https://example.com/operational-guidance",
                snippet=(
                    "Mock source capturing practical guidance, safeguards, "
                    f"and evaluation ideas for {normalized_query}."
                ),
                metadata={"source_type": "mock", "fallback_reason": reason},
            ),
        ]
        return sources[:max_results]

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""
        if not self.settings.tavily_api_key:
            return self._mock_search(query=query, max_results=max_results, reason="missing_api_key")

        payload = json.dumps(
            {
                "api_key": self.settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            }
        ).encode("utf-8")
        request = Request(
            url="https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError):
            return self._mock_search(
                query=query, max_results=max_results, reason="tavily_request_failed"
            )

        results = data.get("results", [])
        documents = [
            SourceDocument(
                title=item.get("title") or "Untitled source",
                url=item.get("url"),
                snippet=item.get("content") or item.get("snippet") or "",
                metadata={"source_type": "tavily"},
            )
            for item in results
            if item.get("content") or item.get("snippet")
        ]
        if documents:
            return documents[:max_results]
        return self._mock_search(
            query=query, max_results=max_results, reason="tavily_empty_results"
        )
