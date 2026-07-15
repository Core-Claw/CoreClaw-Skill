---
name: coreclaw
description: "Use when an agent needs to operate CoreClaw API v2 or CoreClaw MCP: discover/list workers, inspect input schemas, run workers or saved tasks, poll run status, retrieve/export results, inspect logs, rerun/abort runs, check account quota, use proxy regions, or troubleshoot CoreClaw worker execution in English or Chinese."
---

# CoreClaw Agent Skill

Use this skill to operate CoreClaw through the OpenAPI v2 worker model. This is an MCP-first skill: when CoreClaw MCP tools are available, use them instead of hand-written HTTP.

## Sources

- Hosted MCP endpoint: `https://mcp.coreclaw.com/mcp`
- REST API base URL: `https://openapi.coreclaw.com`
- Bundled contract: `openapi.json`
- Detailed references:
  - `references/coreclaw-v2-workflow.md`
  - `references/mcp-tools.md`
  - `references/rest-api-fallback.md`
  - `references/error-handling.md`

Read the relevant reference file only when the task needs more detail than this playbook provides.

## Operating Rules

1. Prefer MCP tools over REST. Use REST only when MCP is unavailable or the user asks for raw HTTP.
2. Use v2 identifiers: `worker_id`, `worker_task_id`, and `run_id`.
3. Use only the public 34-operation CoreClaw MCP/API v2 surface bundled with this skill.
4. Always inspect `get_worker_input_schema` before `run_worker`.
5. Build `run_worker.input_json` from the live schema. Do not invent field names.
6. Use `run_worker_task` for saved task presets instead of rebuilding their input.
7. Save the returned run identifier as `run_id`; REST responses may expose it as `data.run_slug`.
8. Poll with backoff. Do not tight-loop status or result calls.
9. Preview small result sets with list-result tools; use export tools for downloadable CSV or JSON.
10. If a run fails, inspect run detail first, then logs.
11. Rerun only when the user asks to repeat or retry a previous run.
12. Abort only when the user asks to stop/cancel or an active run is confirmed.

## MCP Tool Workflow

Use this default sequence:

1. Discovery and preflight:
   - `list_store_workers` for public marketplace workers.
   - `list_workers` for authenticated user-owned workers.
   - `get_worker` for version, README, and metadata.
   - `get_worker_input_schema` before ad-hoc runs.
   - `list_worker_tasks` before saved task runs.
   - `get_worker_task` and `get_worker_task_input` to inspect a saved task; `create_worker_task`, `update_worker_task`, `update_worker_task_input`, and `delete_worker_task` to manage saved tasks.
   - `list_proxy_regions` when the schema asks for a proxy region.
   - `get_account_info` when balance, quota, or auth health matters.
2. Execution:
   - `run_worker` for ad-hoc input.
   - `run_worker_task` for saved task presets.
3. Run lookup:
   - `get_worker_run` for a known `run_id`.
   - `get_last_worker_run` for account-level latest run.
   - `get_worker_last_run` for latest run scoped to a `worker_id`.
4. Output:
   - `list_worker_run_results`, `list_last_worker_run_results`, or `list_worker_last_run_results` for previews.
   - `export_worker_run_results`, `export_last_worker_run_results`, or `export_worker_last_run_results` for downloads.
   - `get_worker_run_log`, `get_last_worker_run_log`, or `get_worker_last_run_log` for diagnosis.
5. Repeat/control:
   - `rerun_last_worker_run`, `rerun_worker_run`, or `rerun_worker_last_run`.
   - `abort_last_worker_run`, `abort_worker_run`, or `abort_worker_last_run`.

For the exact 34-tool matrix and order, read `references/mcp-tools.md`.

## Direct Worker Runs

Before calling `run_worker`:

1. Identify the worker through `list_store_workers` or `list_workers`.
2. Call `get_worker_input_schema` with the selected `worker_id`.
3. Map user-provided business input to the schema.
4. If required schema fields are missing, ask the user for those values instead of guessing.

For MCP `run_worker`, pass schema-aligned business fields as `input_json`, for example:

```json
{"keyword":"coffee","limit":10}
```

The MCP server wraps this as upstream `input.parameters.custom`. The same wrapping applies to `create_worker_task` and `update_worker_task_input` `input_json`. Use `raw_input_json` only for advanced callers who need to send the complete CoreClaw `input` object.

## Saved Task Runs

Use `list_worker_tasks` when the user wants a saved preset, scheduled configuration, or known task template. To inspect a saved task's input, use `get_worker_task` or `get_worker_task_input`. To create, update metadata/schedule, update input, or remove a saved task, use `create_worker_task`, `update_worker_task`, `update_worker_task_input`, or `delete_worker_task` — their `input_json` is wrapped as `input.parameters.custom` automatically. If the user provides a `worker_task_id`, call `run_worker_task` directly unless the request needs confirmation or task lookup.

`run_worker_task` normally needs only execution controls such as `is_async`, `callback_url`, `offset`, and `limit`.

## Results And Exports

Use result-list tools for inspecting records in the conversation. Use export tools when the user asks for a file, a large dataset, CSV, JSON, or all rows.

Pagination uses zero-based `offset` and `limit` capped at `100` for list/result endpoints.

## Error Handling

When a tool or REST call fails:

1. Preserve the operation name, status, `code`, `message`, and `request_id`.
2. For auth errors, check whether the token is present and valid.
3. For validation errors, compare input against `get_worker_input_schema`.
4. For failed runs, fetch run detail and logs before proposing a rerun.
5. For rate limits, back off instead of retrying immediately.

Read `references/error-handling.md` for the error code table.

## REST Fallback

When MCP is unavailable:

1. Check `CORECLAW_API_KEY` without printing it.
2. Prefer `Authorization: Bearer $CORECLAW_API_KEY`.
3. Use `/api/v2` endpoints only.
4. Follow `references/rest-api-fallback.md` for exact curl patterns.

## Reporting Back

Keep responses concise and operational:

- name the selected worker and why it matched
- show unresolved required input fields before running
- keep `worker_id`, `worker_task_id`, and `run_id` visible for follow-up
- preview representative records instead of dumping large result sets
- provide export links for large outputs
- include logs and `request_id` when explaining failures

## Completion Checklist

Before saying a CoreClaw task is complete, confirm:

- worker discovery or identifier validation happened
- `get_worker_input_schema` was used before `run_worker`
- saved tasks used `run_worker_task`
- the returned `run_id` was saved
- terminal status was checked for async runs
- results were previewed or exported
- logs were inspected for failed or suspicious runs
