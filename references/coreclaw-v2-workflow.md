# CoreClaw API v2 Agent Workflow

Source export: `2026-07-06T02:40:43+00:00`

Use this reference when planning a CoreClaw job or explaining the v2 operating model.

## Source Documents

- `exported-api-docs/openapi.json`
- `exported-api-docs/endpoints.csv`
- `coreclaw-mcp-server/v2_tools.go`
- `coreclaw-mcp-server/MCP_TOOL_SPEC.md`
- `scraper-webui-docs/src/content/docs/api/index.md`
- `scraper-webui-docs/src/content/docs/api/integration.md`
- `scraper-webui-docs/src/content/docs/api/error-codes.md`
- `scraper-webui-docs/src/content/docs/api/callbacks.md`
- scraper-webui endpoint guide files discovered: 39

## Runtime Contract

- HTTP base URL: `https://openapi.coreclaw.com`
- MCP hosted endpoint: `https://mcp.coreclaw.com/mcp`
- API namespace: `/api/v2`
- Preferred auth for REST: `Authorization: Bearer <CORECLAW_API_KEY>`
- MCP auth headers accepted by the hosted server: `api-key`, `X-API-Key`, or `Authorization: Bearer <token>`
- Public endpoints: proxy regions, store worker search, and worker input schema.
- Authenticated endpoints: account, private workers, saved tasks, runs, results, exports, logs, reruns, and aborts.

## Identifier Rules

| Identifier | Meaning | Notes |
| --- | --- | --- |
| `worker_id` | Worker slug or owner path | MCP parameter name. REST path parameter is `workerId`. Owner paths use `owner~name`. |
| `worker_task_id` | Saved worker task id | Use only with saved task runs. |
| `run_id` | Run record id | REST path parameter is `runId`; start/rerun responses may return it as `data.run_slug`. Save it as `run_id` for follow-up tools. |
| `offset` | Zero-based pagination offset | Default `0`. |
| `limit` | Page size or sync result window | Default `20`, maximum `100` for list/result endpoints. |

## Default MCP-First Workflow

1. Discover workers with `list_store_workers` for public marketplace workers or `list_workers` for authenticated user workers.
2. Inspect `get_worker` when version, README, metadata, or ownership context matters.
3. Always call `get_worker_input_schema` before `run_worker`.
4. If the schema asks for a proxy region, call `list_proxy_regions`.
5. Use `run_worker` for ad-hoc input, or `run_worker_task` for saved task presets.
6. Prefer `is_async: true` for long jobs; save the returned run id.
7. Poll `get_worker_run`, `get_last_worker_run`, or `get_worker_last_run` until terminal state.
8. Preview with result-list tools; export CSV or JSON for large datasets.
9. Inspect logs when a run fails, stalls, or produces unexpected output.
10. Use rerun tools only for explicit retry/repeat requests.
11. Use abort tools only for explicit stop/cancel requests or confirmed active runs.

## Direct Worker Run

For MCP `run_worker`, pass business/custom fields from `get_worker_input_schema` as `input_json`.
The MCP server wraps `input_json` as upstream `input.parameters.custom`.

Use `raw_input_json` only when the caller must control the complete upstream CoreClaw `input` object. Do not combine `input_json` and `raw_input_json`.

## Saved Task Run

Use `list_worker_tasks` before `run_worker_task` unless the user already supplied a trusted `worker_task_id`.
Saved task input is stored by CoreClaw; the request normally controls `is_async`, `callback_url`, `offset`, and `limit`.

## Callback Guidance

`callback_url` receives CoreClaw status-change or completion notifications. It does not replace polling, result, log, or export endpoints. Keep the `run_id` and use follow-up tools for authoritative status and full data retrieval.

## Response Handling

REST responses usually include `code`, `message`, `request_id`, and `data`.
Treat HTTP status and application `code` as separate layers. `code: 0` means the business operation succeeded.
Keep `request_id` when troubleshooting.
