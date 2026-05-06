from collections.abc import Callable
from time import perf_counter
from typing import Any, TypedDict, cast

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class GraphState(TypedDict, total=False):
    request: dict[str, Any]
    iteration: int
    route_history: list[str]
    sources: list[dict[str, Any]]
    research_notes: str | None
    analysis_notes: str | None
    final_answer: str | None
    agent_results: list[dict[str, Any]]
    trace: list[dict[str, Any]]
    errors: list[str]


class MultiAgentWorkflow:
    """Builds and runs the LangGraph multi-agent workflow."""

    def __init__(
        self,
        supervisor: Any,
        researcher: BaseAgent,
        analyst: BaseAgent,
        writer: BaseAgent,
        settings: Settings | None = None,
    ) -> None:
        self.supervisor = supervisor
        self.researcher = researcher
        self.analyst = analyst
        self.writer = writer
        self.settings = settings or get_settings()
        self.graph: Any | None = None

    def build(self) -> "MultiAgentWorkflow":
        """Create and compile a LangGraph graph, with a manual fallback."""

        try:
            from langgraph.graph import END, StateGraph

            graph = StateGraph(GraphState)
            graph.add_node("supervisor", cast(Any, self._node(self.supervisor)))
            graph.add_node("researcher", cast(Any, self._node(self.researcher)))
            graph.add_node("analyst", cast(Any, self._node(self.analyst)))
            graph.add_node("writer", cast(Any, self._node(self.writer)))

            graph.set_entry_point("supervisor")
            graph.add_conditional_edges(
                "supervisor",
                self._route_from_supervisor,
                {
                    "researcher": "researcher",
                    "analyst": "analyst",
                    "writer": "writer",
                    "done": END,
                },
            )
            graph.add_edge("researcher", "supervisor")
            graph.add_edge("analyst", "supervisor")
            graph.add_edge("writer", "supervisor")
            self.graph = graph.compile()
        except Exception as exc:
            self.graph = None
            self._build_error = exc
        return self

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""

        if self.graph is None:
            return self._run_manual(state)

        started = perf_counter()
        try:
            result = self.graph.invoke(state.model_dump(mode="json"))
        except Exception as exc:
            raise AgentExecutionError(f"LangGraph workflow failed: {exc}") from exc

        final_state = ResearchState.model_validate(result)
        final_state.add_trace_event(
            "workflow",
            {
                "runtime": "langgraph",
                "duration_seconds": perf_counter() - started,
                "iterations": final_state.iteration,
            },
        )
        return final_state

    def _node(self, agent: Any) -> Callable[[GraphState], GraphState]:
        def run_agent(raw_state: GraphState) -> GraphState:
            state = ResearchState.model_validate(raw_state)
            with trace_span(f"agent.{agent.name}", {"agent": agent.name}):
                next_state = agent.run(state)
            next_state.record_route(agent.name)
            return cast(GraphState, next_state.model_dump(mode="json"))

        return run_agent

    def _route_from_supervisor(self, raw_state: GraphState) -> str:
        state = ResearchState.model_validate(raw_state)
        return str(self.supervisor.decide_next(state))

    def _run_manual(self, state: ResearchState) -> ResearchState:
        started = perf_counter()
        agents = {
            "researcher": self.researcher,
            "analyst": self.analyst,
            "writer": self.writer,
        }
        while state.iteration < self.settings.max_iterations:
            with trace_span("agent.supervisor", {"agent": "supervisor", "runtime": "manual"}):
                state = self.supervisor.run(state)
            state.record_route("supervisor")
            next_route = self.supervisor.decide_next(state)
            if next_route == "done":
                break
            agent = agents.get(next_route)
            if agent is None:
                raise AgentExecutionError(f"Unknown workflow route: {next_route}")
            with trace_span(f"agent.{agent.name}", {"agent": agent.name, "runtime": "manual"}):
                state = agent.run(state)
            state.record_route(agent.name)

        state.add_trace_event(
            "workflow",
            {
                "runtime": "manual",
                "duration_seconds": perf_counter() - started,
                "iterations": state.iteration,
            },
        )
        return state
