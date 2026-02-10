# Multi-Agent Observability

This module provides hooks to monitor the sequence of LLM calls and agent interactions in the multi-agent system.

## Features

- **Session tracking**: Each workflow run is a session with a unique ID.
- **Span hierarchy**: Workflow → Agent steps → LLM calls (nested under the active agent).
- **In-memory store**: Recent sessions and spans are kept in memory and exposed via API.
- **Web monitor**: Built-in monitor UI at `/monitor` to view sessions and timeline.

## Usage

### Viewing traces in the web app

1. Start the web app: `python -m web.app`
2. Open **http://localhost:5000/monitor**
3. Trigger a run (e.g. POST to `/api/v2/comprehensive-review` with `user_context`).
4. Refresh the monitor; select a session to see the timeline of spans (workflow → agents → LLM calls).

### API

- **GET /api/observability/sessions**  
  List recent sessions (query: `limit`, default 50).

- **GET /api/observability/sessions/<session_id>**  
  Get one session with all spans (ordered by start time).

Responses include:

- Session: `session_id`, `query`, `workflow_type`, `start_time`, `end_time`, `status`, `span_count`, `spans`.
- Span: `span_id`, `session_id`, `parent_span_id`, `kind`, `name`, `start_time`, `end_time`, `duration_ms`, `metadata`, `error`.

### Span kinds

- **workflow**: Root span for the whole run.
- **agent**: One agent step (e.g. `portfolio_data`, `tax_advisor`, `estate_planner`, `investment_analyst`).
- **llm_call**: A single LLM request (nested under the agent that made it).
- **agent_message**: Optional; for explicit “data passed from A to B” events.

## Extending with OpenTelemetry or Langfuse

The current implementation is an in-memory collector. You can extend it to export to standard observability backends.

### Option 1: OpenTelemetry

[OpenTelemetry](https://opentelemetry.io/) is a standard for traces and metrics. You can:

1. Install: `pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp`
2. In `collector.py`, after `add_span()` (or in a separate exporter), create an OTLP span from each `Span` and export it.
3. Run a collector (e.g. Jaeger) that receives OTLP and view traces in Jaeger UI.

Example (pseudo): when `add_span(span)` is called, start an OpenTelemetry span with the same `name`, `parent_span_id` → OTel parent context, and set attributes from `metadata`; when `end_span(span_id)` is called, end the corresponding OTel span.

### Option 2: Langfuse

[Langfuse](https://langfuse.com/) is an open-source LLM observability platform. It supports:

- OpenTelemetry export (see [Langfuse + OpenTelemetry](https://langfuse.com/docs/opentelemetry/get-started)).
- Or use the Langfuse Python SDK and create a trace/span for each workflow and child spans for each agent and LLM call inside the hooks (e.g. in `hooks.py` and in `llm_tools` where we call `_record_llm_span`).

Integration steps:

1. Install: `pip install langfuse`
2. Set `LANGFUSE_SECRET_KEY` and `LANGFUSE_PUBLIC_KEY` (and optionally `LANGFUSE_HOST`).
3. In the observability hooks, create a Langfuse trace for the session and Langfuse spans for each workflow/agent/LLM span, and add generation spans for LLM calls (input/output, model, latency).

This keeps the existing in-memory collector and UI; you add a parallel export to Langfuse (or OTel) so you can use both the built-in monitor and external tools.

## Implementation notes

- **Context variables**: `set_current_context(session_id, parent_span_id)` is set by the workflow orchestrator before each agent step. LLM tools read this via `get_current_context()` so each LLM call is recorded under the current agent span.
- **Thread safety**: The in-memory collector uses a lock; safe for multi-threaded use.
- **Limits**: Defaults are 100 sessions and 500 spans per session; older sessions are dropped.
