from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"
    
    def __init__(self, search_client: SearchClient | None = None):
        self.search_client = search_client or SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""

        query = state.request.query
        search_results = self.search_client.search(query, max_results=state.request.max_sources)
        notes = [
            f"{index}. {source.title}: {source.snippet}"
            for index, source in enumerate(search_results, start=1)
        ]
        research_notes = "\n".join(notes)
        state.research_notes = research_notes
        state.sources = search_results
        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=research_notes,
                metadata={"source_count": len(search_results)},
            )
        )
        state.add_trace_event(self.name, {"source_count": len(search_results)})
        return state
