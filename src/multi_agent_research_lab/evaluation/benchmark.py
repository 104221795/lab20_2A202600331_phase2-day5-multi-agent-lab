from collections.abc import Callable
from pathlib import Path
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.report import render_markdown_report

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, and lightweight quality signals."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    quality_score = _score_state(state)
    trace_names = [event.get("name", "unknown") for event in state.trace]
    route_history = " -> ".join(state.route_history)
    answer_chars = len(state.final_answer or "")
    source_count = len(state.sources)
    citation_markers = _count_citation_markers(state.final_answer or "")
    provider_fallback_count = _count_provider_fallbacks(state)
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=state.estimated_cost_usd(),
        quality_score=quality_score,
        notes=(
            f"sources={source_count}; trace_events={len(state.trace)}; "
            f"errors={len(state.errors)}"
        ),
        metadata={
            "query": query,
            "source_count": source_count,
            "trace_event_count": len(state.trace),
            "trace_names": trace_names,
            "route_history": route_history,
            "error_count": len(state.errors),
            "errors": state.errors,
            "answer_chars": answer_chars,
            "agent_result_count": len(state.agent_results),
            "citation_marker_count": citation_markers,
            "citation_coverage": _citation_coverage(source_count, citation_markers),
            "provider_fallback_count": provider_fallback_count,
        },
    )
    return state, metrics


def run_single_agent_baseline(query: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query))
    state.final_answer = (
        "Single-agent baseline: answer generated without specialized research, analysis, "
        "or writing handoffs. Use this as a latency and simplicity comparison point."
    )
    state.add_trace_event("baseline", {"mode": "single-agent"})
    return state


def write_benchmark_report(metrics: list[BenchmarkMetrics], path: str | Path) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown_report(metrics), encoding="utf-8")
    return report_path


def _score_state(state: ResearchState) -> float:
    score = 2.0
    if state.sources:
        score += min(2.0, len(state.sources) * 0.4)
    if state.research_notes:
        score += 1.5
    if state.analysis_notes:
        score += 1.5
    if state.final_answer:
        score += 2.0
    if state.errors:
        score -= min(2.0, len(state.errors) * 0.5)
    return max(0.0, min(10.0, score))


def _count_citation_markers(answer: str) -> int:
    return sum(1 for index in range(1, 21) if f"[{index}]" in answer)


def _citation_coverage(source_count: int, citation_marker_count: int) -> float | None:
    if source_count == 0:
        return None
    return round(min(1.0, citation_marker_count / source_count), 2)


def _count_provider_fallbacks(state: ResearchState) -> int:
    return sum(
        1
        for result in state.agent_results
        if "fallback note" in result.content.lower()
    )
