from typing import Any

from pydantic import BaseModel, Field

from multi_agent_research_lab.core.schemas import AgentResult, ResearchQuery, SourceDocument


class ResearchState(BaseModel):
    """Single source of truth passed through the workflow."""

    request: ResearchQuery
    iteration: int = 0
    route_history: list[str] = Field(default_factory=list)
    sources: list[SourceDocument] = Field(default_factory=list)
    research_notes: str | None = None
    analysis_notes: str | None = None
    final_answer: str | None = None
    agent_results: list[AgentResult] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    def record_route(self, route: str) -> None:
        self.route_history.append(route)
        self.iteration += 1

    def add_trace_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.trace.append({"name": name, "attributes": attributes or {}})

    def estimated_cost_usd(self) -> float | None:
        costs: list[float] = []
        for result in self.agent_results:
            cost = result.metadata.get("cost_usd")
            if isinstance(cost, int | float):
                costs.append(float(cost))
        if not costs:
            return None
        return sum(costs)
