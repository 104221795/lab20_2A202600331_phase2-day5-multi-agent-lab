# Multi-Agent Research Lab

This project implements a runnable multi-agent research system for comparing a
single-agent baseline against a structured multi-agent workflow.

The system uses four main agents:

- **Supervisor**: routes the task and decides which worker should run next.
- **Researcher**: collects source documents using Tavily when available, or a local mock source.
- **Analyst**: turns research notes into structured insights.
- **Writer**: produces the final answer from research and analysis notes.

The workflow is implemented with **LangGraph**, supports **Gemini 2.5 Flash Lite**,
records trace events with **OpenTelemetry**, and writes a benchmark report comparing
latency, quality, cost, source count, and errors.

## Overview

The goal is to show why a multi-agent workflow can produce better research output
than a simple single-agent baseline.

```text
User Query
   |
   v
Supervisor / Router
   |
   +--> Researcher Agent -> sources + research_notes
   |
   +--> Analyst Agent    -> analysis_notes
   |
   +--> Writer Agent     -> final_answer
   |
   v
Trace Events + Benchmark Report
```

The system is designed to run in two modes:

- **Online mode**: uses Gemini through `GEMINI_API_KEY`.
- **Offline fallback mode**: uses deterministic local responses when API access is unavailable.

This makes the project usable for demos, testing, and development even without network access.

## Features

- LangGraph-based multi-agent workflow.
- Gemini 2.5 Flash Lite support through REST API.
- OpenAI fallback support if `OPENAI_API_KEY` is configured.
- Tavily search support if `TAVILY_API_KEY` is configured.
- Local mock search fallback.
- Deterministic offline LLM fallback.
- OpenTelemetry tracing.
- Benchmark report generation.
- Max-iteration guardrail to avoid infinite loops.
- Typed state with Pydantic models.
- CLI commands for baseline, multi-agent run, single-query benchmark, and config benchmark.

## Requirements

- Python 3.11 or newer.
- PowerShell, Bash, or another terminal.
- Optional: Gemini API key.
- Optional: Tavily API key.

## Setup

Create and activate a virtual environment.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project in editable mode:

```bash
pip install -e ".[dev]"
```

If you already have another environment named `venv`, make sure the environment you activate
is the same one where the package is installed. If you see:

```text
ModuleNotFoundError: No module named 'multi_agent_research_lab'
```

run:

```bash
pip install -e ".[dev]"
```

inside the active environment.

## Environment Variables

Create a `.env` file in the project root.

Minimum Gemini setup:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

Optional OpenAI fallback:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
```

Optional Tavily search:

```env
TAVILY_API_KEY=
```

Runtime config:

```env
APP_ENV=local
LOG_LEVEL=INFO
MAX_ITERATIONS=6
TIMEOUT_SECONDS=60
OTEL_CONSOLE_EXPORTER=false
```

## Running the Project

Run the single-agent baseline:

```bash
python -m multi_agent_research_lab.cli baseline --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Run the multi-agent workflow:

```bash
python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Run a benchmark for one query:

```bash
python -m multi_agent_research_lab.cli benchmark --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Run the benchmark for every query in `configs/lab_default.yaml`:

```bash
python -m multi_agent_research_lab.cli benchmark-config
```

Run the config benchmark with a custom report path:

```bash
python -m multi_agent_research_lab.cli benchmark-config --report-path reports/benchmark_all.md
```

The benchmark commands write:

```text
reports/benchmark_report.md
```

View the benchmark report in PowerShell:

```powershell
Get-Content reports\benchmark_report.md
```

View the benchmark report in Bash:

```bash
cat reports/benchmark_report.md
```

## Benchmark Queries

The default config contains three benchmark queries:

```yaml
benchmark:
  queries:
    - "Research GraphRAG state-of-the-art and write a 500-word summary"
    - "Compare single-agent and multi-agent workflows for customer support"
    - "Summarize production guardrails for LLM agents"
```

Use `benchmark --query ...` when you want to test one query.

Use `benchmark-config` when you want to run all configured queries and generate one combined report.

## Benchmark Report

The benchmark report includes:

- per-query baseline and multi-agent rows
- latency
- estimated cost
- quality score
- source count
- citation marker count
- citation coverage
- answer length
- trace event count
- provider fallback count
- route history
- recorded errors
- failure-mode notes

## Benchmark Conclusion

The current benchmark shows that the multi-agent workflow has higher quality than
the baseline, but it is slower.

Example result:

```text
baseline    latency=0.00s  quality=4.0  sources=0
multi-agent latency=1.41s  quality=9.0  sources=5
```

Conclusion:

- Use the **multi-agent workflow** when answer quality, source coverage, and traceability matter.
- Use the **baseline** when speed is more important than research depth.

## Tracing

This project uses **OpenTelemetry** for tracing.

Tracing is configured in:

```text
src/multi_agent_research_lab/observability/tracing.py
```

By default, console span export is disabled to keep terminal output clean.

To view OpenTelemetry spans in the terminal:

### PowerShell

```powershell
$env:OTEL_CONSOLE_EXPORTER="true"
python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

### Bash

```bash
OTEL_CONSOLE_EXPORTER=true python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

You will see spans such as:

```text
agent.supervisor
agent.researcher
agent.analyst
agent.writer
```

To turn console tracing off again:

```powershell
$env:OTEL_CONSOLE_EXPORTER="false"
```

The CLI also prints lightweight workflow trace information:

```text
Routes: supervisor, researcher, supervisor, analyst, supervisor, writer, supervisor
Trace events: 8
```

A ready-to-submit tracing proof is available at:

```text
reports/tracing_proof.md
```

It includes the command, provider, observed span names, example trace IDs, route history,
and reproduction steps.

## Repository Structure

```text
.
|-- configs/
|   `-- lab_default.yaml
|-- docs/
|   |-- design_template.md
|   |-- lab_guide.md
|   `-- peer_review_rubric.md
|-- reports/
|   |-- benchmark_report.md
|   `-- tracing_proof.md
|-- scripts/
|   `-- check_todos.sh
|-- src/
|   `-- multi_agent_research_lab/
|       |-- agents/
|       |   |-- analyst.py
|       |   |-- base.py
|       |   |-- critic.py
|       |   |-- researcher.py
|       |   |-- supervisor.py
|       |   `-- writer.py
|       |-- core/
|       |   |-- config.py
|       |   |-- errors.py
|       |   |-- schemas.py
|       |   `-- state.py
|       |-- evaluation/
|       |   |-- benchmark.py
|       |   `-- report.py
|       |-- graph/
|       |   `-- workflow.py
|       |-- observability/
|       |   |-- logging.py
|       |   `-- tracing.py
|       |-- services/
|       |   |-- llm_client.py
|       |   |-- search_client.py
|       |   `-- storage.py
|       `-- cli.py
|-- tests/
|   |-- test_agents_todo.py
|   |-- test_config.py
|   |-- test_report.py
|   `-- test_state.py
|-- .env.example
|-- Dockerfile
|-- Makefile
|-- pyproject.toml
`-- README.md
```

## Main Components

### Supervisor

File:

```text
src/multi_agent_research_lab/agents/supervisor.py
```

The supervisor decides the next route based on the current shared state:

```text
researcher -> analyst -> writer -> done
```

It also applies the max-iteration guardrail.

### Researcher

File:

```text
src/multi_agent_research_lab/agents/researcher.py
```

The researcher collects sources and creates `research_notes`.

It uses:

- Tavily if `TAVILY_API_KEY` is configured.
- Local mock search otherwise.

### Analyst

File:

```text
src/multi_agent_research_lab/agents/analyst.py
```

The analyst turns research notes into structured insights using the configured LLM client.

### Writer

File:

```text
src/multi_agent_research_lab/agents/writer.py
```

The writer produces the final answer using the research notes, analysis notes, and sources.

### LLM Client

File:

```text
src/multi_agent_research_lab/services/llm_client.py
```

Provider priority:

1. Gemini, if `GEMINI_API_KEY` is configured.
2. OpenAI, if `OPENAI_API_KEY` is configured.
3. Local deterministic fallback.

The Gemini model can be configured as:

```env
GEMINI_MODEL=gemini-2.5-flash-lite
```

The client also accepts the shorter form:

```env
GEMINI_MODEL=2.5-flash-lite
```

and normalizes it automatically.

### Workflow

File:

```text
src/multi_agent_research_lab/graph/workflow.py
```

The workflow is built with LangGraph. If LangGraph is unavailable, the code falls back
to a manual execution loop so the project remains runnable.

### Benchmark

Files:

```text
src/multi_agent_research_lab/evaluation/benchmark.py
src/multi_agent_research_lab/evaluation/report.py
```

The benchmark compares:

- latency
- estimated cost
- quality score
- source count
- trace events
- errors
- route history
- answer length
- citation marker count
- citation coverage
- provider fallback count

The quality score is a lightweight local heuristic. For production work, replace it
with human evaluation or a task-specific evaluation pipeline.

## Testing and Quality Checks

Run tests:

```bash
pytest
```

Run lint:

```bash
ruff check src tests
```

Run type checking:

```bash
mypy src
```

Expected result:

```text
4 passed
All checks passed
Success: no issues found
```

## Failure Mode and Fix

### Failure Mode 1: Package not found

Problem:

```text
ModuleNotFoundError: No module named 'multi_agent_research_lab'
```

Cause:

The active virtual environment did not have the project installed.

Fix:

```bash
pip install -e ".[dev]"
```

Run this command inside the same virtual environment used to run the CLI.

### Failure Mode 2: Gemini network access blocked

Problem:

The Gemini API call fails with a socket or network permission error.

Cause:

The environment blocks outbound network access.

Fix:

Allow network access for the command, or run in offline fallback mode. The LLM client
automatically falls back to a deterministic local response when Gemini cannot be reached.

### Failure Mode 3: Infinite agent loop

Problem:

A multi-agent system can loop forever if routing is not guarded.

Fix:

The supervisor checks `MAX_ITERATIONS` and stops the graph when the task is complete
or the iteration limit is reached.

## Deliverables

This project produces the following deliverables:

1. Runnable multi-agent research system.
2. CLI output for baseline and multi-agent runs.
3. OpenTelemetry trace events.
4. Benchmark report at `reports/benchmark_report.md`.
5. Tracing proof at `reports/tracing_proof.md`.
6. Failure-mode explanation and fixes.

## Notes

- The LangGraph warning about cache serializer defaults is from the installed LangGraph package.
  It does not prevent the workflow from running.
- If Gemini is configured correctly and network access is available, the multi-agent command
  uses Gemini 2.5 Flash Lite.
- If API access is unavailable, the project still runs using deterministic local fallback output.
