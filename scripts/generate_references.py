#!/usr/bin/env python3
"""Generate CoreClaw skill references from the v2 OpenAPI export and MCP server."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path


PHASES = {
    "list_proxy_regions": "Discovery and preflight",
    "list_store_workers": "Discovery and preflight",
    "list_workers": "Discovery and preflight",
    "get_worker": "Discovery and preflight",
    "get_worker_input_schema": "Discovery and preflight",
    "list_worker_tasks": "Discovery and preflight",
    "get_worker_task": "Discovery and preflight",
    "get_worker_task_input": "Discovery and preflight",
    "get_account_info": "Discovery and preflight",
    "create_worker_task": "Task management",
    "update_worker_task": "Task management",
    "update_worker_task_input": "Task management",
    "run_worker": "Execution",
    "run_worker_task": "Execution",
    "list_worker_runs": "Run lookup",
    "get_last_worker_run": "Run lookup",
    "get_worker_run": "Run lookup",
    "get_worker_last_run": "Run lookup",
    "list_last_worker_run_results": "Output retrieval",
    "export_last_worker_run_results": "Output retrieval",
    "get_last_worker_run_log": "Output retrieval",
    "list_worker_run_results": "Output retrieval",
    "export_worker_run_results": "Output retrieval",
    "get_worker_run_log": "Output retrieval",
    "list_worker_last_run_results": "Output retrieval",
    "export_worker_last_run_results": "Output retrieval",
    "get_worker_last_run_log": "Output retrieval",
    "rerun_last_worker_run": "Repeat and control",
    "rerun_worker_run": "Repeat and control",
    "rerun_worker_last_run": "Repeat and control",
    "abort_last_worker_run": "Repeat and control",
    "abort_worker_run": "Repeat and control",
    "abort_worker_last_run": "Repeat and control",
    "delete_worker_task": "Task management",
}


@dataclass(frozen=True)
class Endpoint:
    tag: str
    method: str
    path: str
    summary: str
    operation_id: str
    auth: str


@dataclass(frozen=True)
class Tool:
    name: str
    method: str
    path: str
    phase: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_endpoints(api_docs: Path) -> list[Endpoint]:
    with (api_docs / "endpoints.csv").open("r", encoding="utf-8", newline="") as f:
        return [
            Endpoint(
                tag=row["tag"],
                method=row["method"].upper(),
                path=row["path"],
                summary=row["summary"],
                operation_id=row["operation_id"],
                auth=row["auth"],
            )
            for row in csv.DictReader(f)
        ]


def read_mcp_tools(mcp_server: Path) -> list[Tool]:
    source = (mcp_server / "v2_tools.go").read_text(encoding="utf-8")
    order_block = re.search(r"func v2ToolWorkflowOrder\(\) \[\]string \{(?P<body>.*?)\n\}", source, re.S)
    if not order_block:
        raise RuntimeError("could not find v2ToolWorkflowOrder in v2_tools.go")

    order = re.findall(r'"([a-z0-9_]+)"', order_block.group("body"))
    spec_matches = re.findall(r'\{Name: "([^"]+)", Method: http\.Method([A-Za-z]+), Path: "([^"]+)"', source)
    specs = {
        name: Tool(name=name, method=method.upper(), path=path, phase=PHASES.get(name, "Uncategorized"))
        for name, method, path in spec_matches
    }
    missing = [name for name in order if name not in specs]
    if missing:
        raise RuntimeError(f"workflow order references missing tool specs: {missing}")
    return [specs[name] for name in order]


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def public_openapi(openapi: dict, tools: list[Tool]) -> dict:
    spec = json.loads(json.dumps(openapi))
    public_routes = {(tool.method, tool.path) for tool in tools}
    for path in list(spec.get("paths", {})):
        methods = spec["paths"][path]
        for method in list(methods):
            if (method.upper(), path) not in public_routes:
                methods.pop(method)
        if not methods:
            spec["paths"].pop(path)
    spec.setdefault("info", {})["description"] = (
        spec.get("info", {}).get("description", "")
        + "\n\nSkill bundle note: this packaged contract contains only the public skill/MCP surface: 34 operations."
    ).strip()
    sanitize_public_contract(spec)
    return spec


def sanitize_public_contract(value: object) -> None:
    if isinstance(value, dict):
        for key in list(value):
            if key in {"scraper_slug", "page_index", "page_size"}:
                value.pop(key)
                continue
            child = value[key]
            if isinstance(child, str):
                child = child.replace('"scraper_slug":"run_slug",', "")
                child = child.replace('{"run_slug":"run_slug",', '{"run_status":"succeeded",')
                child = child.replace("WORKER_VERSION_UNAVAILABLE", "WORKER_UNAVAILABLE")
                child = child.replace("the worker version is not available", "the worker is not available")
                value[key] = child
            else:
                sanitize_public_contract(child)
    elif isinstance(value, list):
        for child in value:
            sanitize_public_contract(child)


def read_webui_docs_summary(webui_docs: Path) -> list[str]:
    summary: list[str] = []
    for name in ["index.md", "integration.md", "error-codes.md", "callbacks.md"]:
        path = webui_docs / name
        if path.is_file():
            summary.append(f"- `scraper-webui-docs/src/content/docs/api/{name}`")
    endpoint_docs = [
        path
        for path in webui_docs.rglob("*")
        if path.is_file() and path.suffix in {".md", ".mdx"} and path.parent != webui_docs
    ]
    summary.append(f"- scraper-webui endpoint guide files discovered: {len(endpoint_docs)}")
    return summary


def load_error_table(api_docs: Path) -> list[tuple[str, str, str]]:
    """Parse the error code table from error-codes.md.

    Handles both `| `10000` |` (code wrapped in backticks) and
    `| 10000 | `SYSTEM_ERROR` |` (key wrapped in backticks) row shapes.
    """
    text = (api_docs / "error-codes.md").read_text(encoding="utf-8")
    rows: list[tuple[str, str, str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        parts = [part.strip().strip("`") for part in line.strip("|").split("|")]
        if len(parts) == 3 and parts[0].isdigit():
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def write_workflow(refs: Path, exported_at: str, webui_summary: list[str]) -> None:
    text = f"""# CoreClaw API v2 Agent Workflow

Source export: `{exported_at}`

Use this reference when planning a CoreClaw job or explaining the v2 operating model.

## Source Documents

- `exported-api-docs/openapi.json`
- `exported-api-docs/endpoints.csv`
- `coreclaw-mcp-server/v2_tools.go`
- `coreclaw-mcp-server/MCP_TOOL_SPEC.md`
{chr(10).join(webui_summary)}

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
"""
    (refs / "coreclaw-v2-workflow.md").write_text(text, encoding="utf-8")


def write_mcp_tools(refs: Path, tools: list[Tool]) -> None:
    rows = [[str(i), f"`{tool.name}`", tool.phase, f"`{tool.method}`", f"`{tool.path}`"] for i, tool in enumerate(tools, 1)]
    text = f"""# CoreClaw MCP Tool Matrix

Use this reference when choosing the exact MCP tool. The hosted server exposes {len(tools)} public tools in workflow order.

## Hosted Endpoint

```json
{{
  "mcpServers": {{
    "coreclaw": {{
      "url": "https://mcp.coreclaw.com/mcp",
      "headers": {{
        "api-key": "your-coreclaw-token"
      }}
    }}
  }}
}}
```

The hosted MCP server accepts `api-key`, `X-API-Key`, and `Authorization: Bearer <token>` from clients and forwards upstream as Bearer auth.

## Tool Order

{markdown_table(["#", "MCP tool", "Phase", "Method", "API path"], rows)}

## Selection Notes

- Use store tools for public marketplace discovery.
- Use private worker tools when the user asks for their own workers.
- Use worker-specific last-run tools only when a known `worker_id` scopes the request.
- Use account-level last-run tools only when the user means the current account's latest run.
- Prefer export tools for file delivery; prefer result-list tools for previews and analysis.
"""
    (refs / "mcp-tools.md").write_text(text, encoding="utf-8")


def write_rest_fallback(refs: Path, endpoints: list[Endpoint], tools: list[Tool]) -> None:
    public_routes = {(tool.method, tool.path) for tool in tools}
    public_rows: list[list[str]] = []
    for endpoint in endpoints:
        if (endpoint.method, endpoint.path) not in public_routes:
            continue
        row = [endpoint.tag, f"`{endpoint.method}`", f"`{endpoint.path}`", endpoint.summary, endpoint.auth]
        public_rows.append(row)

    text = f"""# CoreClaw REST API Fallback

Use REST only when MCP tools are unavailable or the user explicitly asks for raw HTTP examples.

## Auth

Prefer Bearer auth:

```bash
-H "Authorization: Bearer $CORECLAW_API_KEY"
```

The API also supports the legacy `api-key` header and `?token=` query parameter. Avoid query tokens unless headers are impossible.

## Public Skill Surface

{markdown_table(["Tag", "Method", "Path", "Summary", "Auth"], public_rows)}

## Curl Patterns

List store workers:

```bash
curl -s "https://openapi.coreclaw.com/api/v2/store?keyword=coffee&offset=0&limit=20"
```

Read worker input schema:

```bash
curl -s "https://openapi.coreclaw.com/api/v2/workers/$WORKER_ID/input-schema"
```

Run a worker asynchronously:

```bash
curl -s -X POST "https://openapi.coreclaw.com/api/v2/workers/$WORKER_ID/runs" \\
  -H "Authorization: Bearer $CORECLAW_API_KEY" \\
  -H "Content-Type: application/json" \\
  --data '{{"input":{{"parameters":{{"custom":{{"keyword":"coffee","limit":10}}}}}},"is_async":true,"offset":0,"limit":20}}'
```

Run a saved task asynchronously:

```bash
curl -s -X POST "https://openapi.coreclaw.com/api/v2/worker-tasks/$WORKER_TASK_ID/runs" \\
  -H "Authorization: Bearer $CORECLAW_API_KEY" \\
  -H "Content-Type: application/json" \\
  --data '{{"is_async":true}}'
```

Poll a run:

```bash
curl -s "https://openapi.coreclaw.com/api/v2/worker-runs/$RUN_ID" \\
  -H "Authorization: Bearer $CORECLAW_API_KEY"
```

Preview results:

```bash
curl -s "https://openapi.coreclaw.com/api/v2/worker-runs/$RUN_ID/result?offset=0&limit=20" \\
  -H "Authorization: Bearer $CORECLAW_API_KEY"
```

Export results:

```bash
curl -s "https://openapi.coreclaw.com/api/v2/worker-runs/$RUN_ID/result/export?format=csv&filter_keys=title%2Caddress" \\
  -H "Authorization: Bearer $CORECLAW_API_KEY"
```
"""
    (refs / "rest-api-fallback.md").write_text(text, encoding="utf-8")


def write_error_handling(refs: Path, api_docs: Path) -> None:
    rows = [[f"`{code}`", key, message] for code, key, message in load_error_table(api_docs)]
    text = f"""# CoreClaw Error Handling

Use this reference when an HTTP call or MCP tool reports a failed CoreClaw request.

## Response Layers

- HTTP status describes transport/request handling.
- JSON `code` describes CoreClaw business outcome.
- `code: 0` means success.
- Keep `message`, `request_id`, and any validation `details` in the user-facing diagnosis.

## Error Codes

{markdown_table(["Code", "Key", "Message"], rows)}

## Triage

| Symptom | Action |
| --- | --- |
| `12001` or `12002` | Check whether the token is missing, expired, malformed, or sent in an unsupported place. |
| `13000` or HTTP `429` | Back off and retry later; do not tight-loop polling. |
| `30001` | Tell the user the account has insufficient balance before starting more runs. |
| `50001`, `50003`, `60001`, or `70001` | Re-check worker, version, task, or run identifiers. |
| Failed or stalled run | Fetch run detail first, then logs. |
| Empty or suspicious output | Check run status, result count, logs, and input schema alignment before rerunning. |

## Reporting Failures

Include operation/tool name, relevant identifiers, HTTP status if using REST, CoreClaw `code`, `message`, `request_id`, log evidence, and the next actionable step.
"""
    (refs / "error-handling.md").write_text(text, encoding="utf-8")


def generate(args: argparse.Namespace) -> None:
    root = repo_root()
    workspace = root.parent
    api_docs = (args.api_docs or workspace / "exported-api-docs").resolve()
    mcp_server = (args.mcp_server or workspace / "coreclaw-mcp-server").resolve()
    webui_docs = (args.webui_docs or workspace / "scraper-webui-docs" / "src" / "content" / "docs" / "api").resolve()
    refs = root / "references"
    refs.mkdir(exist_ok=True)

    endpoints = read_endpoints(api_docs)
    tools = read_mcp_tools(mcp_server)
    openapi = json.loads((api_docs / "openapi.json").read_text(encoding="utf-8"))
    manifest = json.loads((api_docs / "manifest.json").read_text(encoding="utf-8"))

    if len(endpoints) != 37:
        raise RuntimeError(f"expected 37 OpenAPI endpoints, found {len(endpoints)}")
    if len(tools) != 34:
        raise RuntimeError(f"expected 34 MCP tools, found {len(tools)}")
    if len(openapi.get("paths", {})) != 33:
        raise RuntimeError(f"OpenAPI path count is not 33, got {len(openapi.get('paths', {}))}")

    if args.copy_openapi:
        (root / "openapi.json").write_text(
            json.dumps(public_openapi(openapi, tools), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    write_workflow(refs, manifest.get("exported_at_utc", "unknown"), read_webui_docs_summary(webui_docs))
    write_mcp_tools(refs, tools)
    write_rest_fallback(refs, endpoints, tools)
    write_error_handling(refs, api_docs)

    print("Generated CoreClaw references")
    print(f"Source OpenAPI endpoints: {len(endpoints)}")
    print(f"Packaged public OpenAPI operations: {len(tools)}")
    print(f"MCP public tools: {len(tools)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-docs", type=Path)
    parser.add_argument("--mcp-server", type=Path)
    parser.add_argument("--webui-docs", type=Path)
    parser.add_argument("--copy-openapi", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    generate(parse_args())
