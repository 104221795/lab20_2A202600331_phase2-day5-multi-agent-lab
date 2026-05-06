# Benchmark Report

This report compares the single-agent baseline with the multi-agent workflow. Quality is a lightweight local heuristic, so it should be treated as a development signal rather than a final human evaluation score.

## Summary

| Run | Count | Avg Latency (s) | Avg Quality | Avg Sources | Avg Trace Events | Provider Fallbacks | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 3 | 0.00 | 4.0 | 0.0 | 1.0 | 0 | 0 |
| multi-agent | 3 | 0.82 | 9.0 | 5.0 | 8.0 | 6 | 0 |

- Best quality run: `multi-agent` on query `Research GraphRAG state-of-the-art and write a 500-word summary`
- Fastest run: `baseline` on query `Summarize production guardrails for LLM agents`
- Main tradeoff: multi-agent runs add latency, but they produce richer traces and source-backed answers.

## Detailed Metrics

| Query | Run | Latency (s) | Cost (USD) | Quality | Sources | Citations | Citation Coverage | Answer Chars | Trace Events | Provider Fallbacks | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Q1: Research GraphRAG state-of-the-art and write a 500-word summary | baseline | 0.00 |  | 4.0 | 0 | 0 |  | 155 | 1 | 0 | 0 |
| Q1: Research GraphRAG state-of-the-art and write a 500-word summary | multi-agent | 1.46 | 0.0000 | 9.0 | 5 | 0 | 0% | 770 | 8 | 2 | 0 |
| Q2: Compare single-agent and multi-agent workflows for customer support | baseline | 0.00 |  | 4.0 | 0 | 0 |  | 155 | 1 | 0 | 0 |
| Q2: Compare single-agent and multi-agent workflows for customer support | multi-agent | 0.49 | 0.0000 | 9.0 | 5 | 0 | 0% | 782 | 8 | 2 | 0 |
| Q3: Summarize production guardrails for LLM agents | baseline | 0.00 |  | 4.0 | 0 | 0 |  | 155 | 1 | 0 | 0 |
| Q3: Summarize production guardrails for LLM agents | multi-agent | 0.53 | 0.0000 | 9.0 | 5 | 0 | 0% | 719 | 8 | 2 | 0 |

## Trace and Routing

Trace events show which parts of the workflow ran. The multi-agent route should normally include supervisor, researcher, analyst, and writer.

| Query | Run | Route History | Trace Names |
|---|---|---|---|
| Q1: Research GraphRAG state-of-the-art and write a 500-word summary | baseline |  | baseline |
| Q1: Research GraphRAG state-of-the-art and write a 500-word summary | multi-agent | supervisor -> researcher -> supervisor -> analyst -> supervisor -> writer -> supervisor | supervisor, researcher, supervisor, analyst, supervisor, writer, supervisor, workflow |
| Q2: Compare single-agent and multi-agent workflows for customer support | baseline |  | baseline |
| Q2: Compare single-agent and multi-agent workflows for customer support | multi-agent | supervisor -> researcher -> supervisor -> analyst -> supervisor -> writer -> supervisor | supervisor, researcher, supervisor, analyst, supervisor, writer, supervisor, workflow |
| Q3: Summarize production guardrails for LLM agents | baseline |  | baseline |
| Q3: Summarize production guardrails for LLM agents | multi-agent | supervisor -> researcher -> supervisor -> analyst -> supervisor -> writer -> supervisor | supervisor, researcher, supervisor, analyst, supervisor, writer, supervisor, workflow |

## Queries Evaluated

1. Research GraphRAG state-of-the-art and write a 500-word summary
2. Compare single-agent and multi-agent workflows for customer support
3. Summarize production guardrails for LLM agents

## Failure Modes and Fixes

- No runtime errors were recorded in this benchmark.
- Known risk: multi-agent systems can loop or spend too many calls. Fix: enforce `MAX_ITERATIONS` and route through the supervisor.
- Known risk: provider/network failures can interrupt Gemini calls. Fix: the LLM client falls back to deterministic local output.

