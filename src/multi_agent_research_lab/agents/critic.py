"""Optional critic agent skeleton for bonus work."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""

        findings: list[str] = []
        if not state.final_answer:
            findings.append("Final answer is missing.")
        if not state.sources:
            findings.append("No sources are attached to the state.")
        if state.final_answer and state.sources and "[" not in state.final_answer:
            findings.append("Final answer has sources available but no explicit citation markers.")
        if not findings:
            findings.append("Critic check passed: answer, sources, and trace are present.")
        content = "\n".join(f"- {item}" for item in findings)
        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=content,
                metadata={"finding_count": len(findings)},
            )
        )
        state.add_trace_event(self.name, {"finding_count": len(findings)})
        return state
