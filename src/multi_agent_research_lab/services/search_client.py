"""Search client abstraction for ResearcherAgent."""

import json
from urllib import request
from urllib.error import URLError

from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client with Tavily and local fallback."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""

        if self.settings.tavily_api_key:
            try:
                return self._search_tavily(query, max_results)
            except (OSError, URLError, TimeoutError, ValueError):
                return self._mock_search(query, max_results)
        return self._mock_search(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        payload = json.dumps(
            {
                "api_key": self.settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False,
            }
        ).encode("utf-8")
        req = request.Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=self.settings.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        results = data.get("results", [])
        return [
            SourceDocument(
                title=item.get("title") or "Untitled source",
                url=item.get("url"),
                snippet=item.get("content") or item.get("snippet") or "",
                metadata={"provider": "tavily", "score": item.get("score")},
            )
            for item in results[:max_results]
        ]

    def _mock_search(self, query: str, max_results: int) -> list[SourceDocument]:
        topics = [
            (
                "Agent orchestration patterns",
                "Use routing, prompt chaining, evaluator loops, and explicit handoffs "
                "when task decomposition improves reliability.",
            ),
            (
                "Production guardrails for LLM agents",
                "Set max iterations, timeouts, retries, validation, and trace capture "
                "before deploying multi-step agents.",
            ),
            (
                "Research synthesis workflow",
                "Separate evidence gathering, analysis, and writing to reduce context "
                "overload and make failures easier to debug.",
            ),
            (
                "Benchmarking multi-agent systems",
                "Compare quality, latency, estimated cost, citation coverage, and "
                "failure modes against a single-agent baseline.",
            ),
            (
                "Graph-based agent execution",
                "A graph runtime makes control flow explicit, observable, and easier "
                "to test than ad hoc recursive calls.",
            ),
        ]
        return [
            SourceDocument(
                title=title,
                url=f"local://mock-search/{index}",
                snippet=f"{snippet} Query focus: {query}",
                metadata={"provider": "mock", "rank": index},
            )
            for index, (title, snippet) in enumerate(topics[:max_results], start=1)
        ]
