from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import Settings, get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow


class SupervisorAgent:
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def decide_next(self, state: ResearchState) -> str:
        """Return the next worker route based on available state."""

        if not state.research_notes:
            if state.iteration >= self.settings.max_iterations:
                state.errors.append("Max iterations reached before research completed.")
                return "done"
            return "researcher"
        if not state.analysis_notes:
            if state.iteration >= self.settings.max_iterations:
                state.errors.append("Max iterations reached before analysis completed.")
                return "done"
            return "analyst"
        if not state.final_answer:
            if state.iteration >= self.settings.max_iterations:
                state.errors.append("Max iterations reached before final answer completed.")
                return "done"
            return "writer"
        return "done"

    def run(self, state: ResearchState) -> ResearchState:
        """Record routing decision for observability."""

        next_route = self.decide_next(state)
        state.agent_results.append(
            AgentResult(
                agent=AgentName.SUPERVISOR,
                content=f"Next route: {next_route}",
                metadata={"next_route": next_route},
            )
        )
        state.add_trace_event(self.name, {"next_route": next_route})
        return state

    def create_workflow(self) -> MultiAgentWorkflow:
        """Create a runnable workflow with default worker agents."""

        return MultiAgentWorkflow(
            supervisor=self,
            researcher=ResearcherAgent(),
            analyst=AnalystAgent(),
            writer=WriterAgent(),
            settings=self.settings,
        ).build()
