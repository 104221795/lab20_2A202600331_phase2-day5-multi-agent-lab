from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_runs_workflow() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = SupervisorAgent().create_workflow().run(state)
    assert result.research_notes
    assert result.analysis_notes
    assert result.final_answer
    assert "researcher" in result.route_history
