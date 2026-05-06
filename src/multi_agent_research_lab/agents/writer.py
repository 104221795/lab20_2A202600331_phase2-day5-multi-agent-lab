from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""

        source_lines = "\n".join(
            f"- [{index}] {source.title} ({source.url or 'no url'}): {source.snippet}"
            for index, source in enumerate(state.sources, start=1)
        )
        prompt = (
            f"Query: {state.request.query}\n"
            f"Audience: {state.request.audience}\n\n"
            f"Research notes:\n{state.research_notes or 'None'}\n\n"
            f"Analysis notes:\n{state.analysis_notes or 'None'}\n\n"
            f"Sources:\n{source_lines or 'No sources'}\n\n"
            "Write a concise final answer with cited source numbers where useful."
        )
        response = self.llm_client.complete(
            system_prompt=(
                "You are a technical writer. Produce a clear answer grounded in the "
                "provided notes and sources. Mention limitations when evidence is weak."
            ),
            user_prompt=prompt,
        )
        state.final_answer = response.content
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                    "citation_count": len(state.sources),
                },
            )
        )
        state.add_trace_event(self.name, {"final_answer_chars": len(response.content)})
        return state
