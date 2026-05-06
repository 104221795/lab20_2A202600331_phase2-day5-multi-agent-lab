"""Command-line entrypoint for the lab starter."""

from pathlib import Path
from typing import Annotated

import typer
import yaml  # type: ignore[import-untyped]
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import (
    run_benchmark,
    run_single_agent_baseline,
    write_benchmark_report,
)
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import configure_tracing

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()

def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    configure_tracing()


def _run_multi_agent(query_text: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query_text))
    workflow = SupervisorAgent().create_workflow()
    return workflow.run(state)

@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline placeholder."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    state.final_answer = (
        "Single-agent baseline: answer generated without specialized research, analysis, "
        "or writing handoffs. Use benchmark output to compare this against the graph workflow."
    )
    state.add_trace_event("baseline", {"mode": "single-agent"})
    console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline"))

@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()

    try:
        result = _run_multi_agent(query)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    
    console.print(
        Panel.fit(result.final_answer or "No final answer produced.", title="Multi-Agent Result")
    )
    console.print(f"Routes: {', '.join(result.route_history)}")
    console.print(f"Trace events: {len(result.trace)}")


@app.command("benchmark")
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
    report_path: Annotated[
        str, typer.Option("--report-path", help="Markdown report output path")
    ] = "reports/benchmark_report.md",
) -> None:
    """Run baseline and multi-agent benchmark and write a markdown report."""

    _init()

    _, baseline_metrics = run_benchmark("baseline", query, run_single_agent_baseline)
    _, multi_agent_metrics = run_benchmark("multi-agent", query, _run_multi_agent)
    path = write_benchmark_report([baseline_metrics, multi_agent_metrics], report_path)
    console.print(Panel.fit(f"Wrote benchmark report to {path}", title="Benchmark"))


@app.command("benchmark-config")
def benchmark_config(
    config_path: Annotated[
        str,
        typer.Option("--config", help="YAML config with benchmark.queries"),
    ] = "configs/lab_default.yaml",
    report_path: Annotated[
        str,
        typer.Option("--report-path", help="Markdown report output path"),
    ] = "reports/benchmark_report.md",
) -> None:
    """Run baseline and multi-agent benchmarks for every query in the YAML config."""

    _init()
    queries = _load_benchmark_queries(Path(config_path))
    metrics = []
    for index, query_text in enumerate(queries, start=1):
        console.print(f"Running benchmark query {index}/{len(queries)}")
        _, baseline_metrics = run_benchmark(
            "baseline",
            query_text,
            run_single_agent_baseline,
        )
        baseline_metrics.metadata["query_index"] = index
        _, multi_agent_metrics = run_benchmark(
            "multi-agent",
            query_text,
            _run_multi_agent,
        )
        multi_agent_metrics.metadata["query_index"] = index
        metrics.extend([baseline_metrics, multi_agent_metrics])

    path = write_benchmark_report(metrics, report_path)
    console.print(Panel.fit(f"Wrote benchmark report to {path}", title="Benchmark Config"))


def _load_benchmark_queries(config_path: Path) -> list[str]:
    if not config_path.exists():
        raise typer.BadParameter(f"Config file not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    benchmark_data = data.get("benchmark") or {}
    queries = benchmark_data.get("queries") or []
    if not isinstance(queries, list) or not all(isinstance(query, str) for query in queries):
        raise typer.BadParameter("Config must contain benchmark.queries as a list of strings.")
    if not queries:
        raise typer.BadParameter("No benchmark queries found in config.")
    return queries

if __name__ == "__main__":
    app()
