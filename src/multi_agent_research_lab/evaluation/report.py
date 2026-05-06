"""Benchmark report rendering."""

from collections import defaultdict
from collections.abc import Iterable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown."""

    lines = [
        "# Benchmark Report",
        "",
        "This report compares the single-agent baseline with the multi-agent workflow. "
        "Quality is a lightweight local heuristic, so it should be treated as a "
        "development signal rather than a final human evaluation score.",
        "",
    ]

    if not metrics:
        return "\n".join(lines + ["No benchmark metrics were recorded.", ""])

    lines.extend(_render_summary(metrics))
    lines.extend(_render_detailed_table(metrics))
    lines.extend(_render_trace_section(metrics))
    lines.extend(_render_query_section(metrics))
    lines.extend(_render_failure_section(metrics))
    return "\n".join(lines) + "\n"


def _render_summary(metrics: list[BenchmarkMetrics]) -> list[str]:
    by_run: dict[str, list[BenchmarkMetrics]] = defaultdict(list)
    for item in metrics:
        by_run[item.run_name].append(item)

    lines = [
        "## Summary",
        "",
        "| Run | Count | Avg Latency (s) | Avg Quality | Avg Sources | Avg Trace Events | "
        "Provider Fallbacks | Errors |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for run_name, items in sorted(by_run.items()):
        lines.append(
            "| "
            f"{run_name} | "
            f"{len(items)} | "
            f"{_avg(item.latency_seconds for item in items):.2f} | "
            f"{_avg((item.quality_score or 0.0) for item in items):.1f} | "
            f"{_avg(float(item.metadata.get('source_count', 0)) for item in items):.1f} | "
            f"{_avg(float(item.metadata.get('trace_event_count', 0)) for item in items):.1f} | "
            f"{sum(int(item.metadata.get('provider_fallback_count', 0)) for item in items)} | "
            f"{sum(int(item.metadata.get('error_count', 0)) for item in items)} |"
        )

    best_quality = max(metrics, key=lambda item: item.quality_score or 0)
    fastest = min(metrics, key=lambda item: item.latency_seconds)
    lines.extend(
        [
            "",
            f"- Best quality run: `{best_quality.run_name}` "
            f"on query `{best_quality.metadata.get('query', '')}`",
            f"- Fastest run: `{fastest.run_name}` "
            f"on query `{fastest.metadata.get('query', '')}`",
            "- Main tradeoff: multi-agent runs add latency, but they produce richer traces "
            "and source-backed answers.",
            "",
        ]
    )
    return lines


def _render_detailed_table(metrics: list[BenchmarkMetrics]) -> list[str]:
    lines = [
        "## Detailed Metrics",
        "",
        "| Query | Run | Latency (s) | Cost (USD) | Quality | Sources | Citations | "
        "Citation Coverage | Answer Chars | Trace Events | Provider Fallbacks | Errors |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        coverage = item.metadata.get("citation_coverage")
        coverage_text = "" if coverage is None else f"{float(coverage) * 100:.0f}%"
        lines.append(
            "| "
            f"{_query_label(item)} | "
            f"{item.run_name} | "
            f"{item.latency_seconds:.2f} | "
            f"{cost} | "
            f"{quality} | "
            f"{item.metadata.get('source_count', 0)} | "
            f"{item.metadata.get('citation_marker_count', 0)} | "
            f"{coverage_text} | "
            f"{item.metadata.get('answer_chars', 0)} | "
            f"{item.metadata.get('trace_event_count', 0)} | "
            f"{item.metadata.get('provider_fallback_count', 0)} | "
            f"{item.metadata.get('error_count', 0)} |"
        )
    lines.append("")
    return lines


def _render_trace_section(metrics: list[BenchmarkMetrics]) -> list[str]:
    lines = [
        "## Trace and Routing",
        "",
        "Trace events show which parts of the workflow ran. The multi-agent route should "
        "normally include supervisor, researcher, analyst, and writer.",
        "",
        "| Query | Run | Route History | Trace Names |",
        "|---|---|---|---|",
    ]
    for item in metrics:
        trace_names = item.metadata.get("trace_names", [])
        if isinstance(trace_names, list):
            trace_text = ", ".join(str(name) for name in trace_names)
        else:
            trace_text = str(trace_names)
        lines.append(
            "| "
            f"{_query_label(item)} | "
            f"{item.run_name} | "
            f"{_escape(str(item.metadata.get('route_history', '')))} | "
            f"{_escape(trace_text)} |"
        )
    lines.append("")
    return lines


def _render_query_section(metrics: list[BenchmarkMetrics]) -> list[str]:
    queries = list(dict.fromkeys(str(item.metadata.get("query", "")) for item in metrics))
    lines = ["## Queries Evaluated", ""]
    for index, query in enumerate(queries, start=1):
        lines.append(f"{index}. {query}")
    lines.append("")
    return lines


def _render_failure_section(metrics: list[BenchmarkMetrics]) -> list[str]:
    error_items = [item for item in metrics if int(item.metadata.get("error_count", 0)) > 0]
    lines = [
        "## Failure Modes and Fixes",
        "",
    ]
    if not error_items:
        lines.extend(
            [
                "- No runtime errors were recorded in this benchmark.",
                "- Known risk: multi-agent systems can loop or spend too many calls. "
                "Fix: enforce `MAX_ITERATIONS` and route through the supervisor.",
                "- Known risk: provider/network failures can interrupt Gemini calls. "
                "Fix: the LLM client falls back to deterministic local output.",
                "",
            ]
        )
        return lines

    for item in error_items:
        lines.append(f"- `{item.run_name}` on `{item.metadata.get('query', '')}`:")
        for error in item.metadata.get("errors", []):
            lines.append(f"  - {error}")
    lines.append("")
    return lines


def _avg(values: Iterable[float]) -> float:
    numbers = list(values)
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _query_label(item: BenchmarkMetrics) -> str:
    query = _escape(str(item.metadata.get("query", "")))
    query_index = item.metadata.get("query_index")
    if query_index is None:
        return query
    return f"Q{query_index}: {query}"
