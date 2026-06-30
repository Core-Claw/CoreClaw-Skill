# CoreClaw MCP Tool Matrix

Use this reference when choosing the exact MCP tool. The hosted server exposes 28 public tools in workflow order.

## Hosted Endpoint

```json
{
  "mcpServers": {
    "coreclaw": {
      "url": "https://mcp.coreclaw.com/mcp",
      "headers": {
        "api-key": "your-coreclaw-token"
      }
    }
  }
}
```

The hosted MCP server accepts `api-key`, `X-API-Key`, and `Authorization: Bearer <token>` from clients and forwards upstream as Bearer auth.

## Tool Order

| # | MCP tool | Phase | Method | API path |
| --- | --- | --- | --- | --- |
| 1 | `list_proxy_regions` | Discovery and preflight | `GET` | `/api/v2/proxy/region` |
| 2 | `list_store_workers` | Discovery and preflight | `GET` | `/api/v2/store` |
| 3 | `list_workers` | Discovery and preflight | `GET` | `/api/v2/workers` |
| 4 | `get_worker` | Discovery and preflight | `GET` | `/api/v2/workers/{workerId}` |
| 5 | `get_worker_input_schema` | Discovery and preflight | `GET` | `/api/v2/workers/{workerId}/input-schema` |
| 6 | `list_worker_tasks` | Discovery and preflight | `GET` | `/api/v2/worker-tasks` |
| 7 | `get_account_info` | Discovery and preflight | `GET` | `/api/v2/users/account` |
| 8 | `run_worker` | Execution | `POST` | `/api/v2/workers/{workerId}/runs` |
| 9 | `run_worker_task` | Execution | `POST` | `/api/v2/worker-tasks/{workerTaskId}/runs` |
| 10 | `list_worker_runs` | Run lookup | `GET` | `/api/v2/worker-runs` |
| 11 | `get_last_worker_run` | Run lookup | `GET` | `/api/v2/worker-runs/last` |
| 12 | `get_worker_run` | Run lookup | `GET` | `/api/v2/worker-runs/{runId}` |
| 13 | `get_worker_last_run` | Run lookup | `GET` | `/api/v2/workers/{workerId}/runs/last` |
| 14 | `list_last_worker_run_results` | Output retrieval | `GET` | `/api/v2/worker-runs/last/result` |
| 15 | `export_last_worker_run_results` | Output retrieval | `GET` | `/api/v2/worker-runs/last/export` |
| 16 | `get_last_worker_run_log` | Output retrieval | `GET` | `/api/v2/worker-runs/last/log` |
| 17 | `list_worker_run_results` | Output retrieval | `GET` | `/api/v2/worker-runs/{runId}/result` |
| 18 | `export_worker_run_results` | Output retrieval | `GET` | `/api/v2/worker-runs/{runId}/result/export` |
| 19 | `get_worker_run_log` | Output retrieval | `GET` | `/api/v2/worker-runs/{runId}/log` |
| 20 | `list_worker_last_run_results` | Output retrieval | `GET` | `/api/v2/workers/{workerId}/runs/last/result` |
| 21 | `export_worker_last_run_results` | Output retrieval | `GET` | `/api/v2/workers/{workerId}/runs/last/export` |
| 22 | `get_worker_last_run_log` | Output retrieval | `GET` | `/api/v2/workers/{workerId}/runs/last/log` |
| 23 | `rerun_last_worker_run` | Repeat and control | `POST` | `/api/v2/worker-runs/last/rerun` |
| 24 | `rerun_worker_run` | Repeat and control | `POST` | `/api/v2/worker-runs/{runId}/rerun` |
| 25 | `rerun_worker_last_run` | Repeat and control | `POST` | `/api/v2/workers/{workerId}/runs/last/rerun` |
| 26 | `abort_last_worker_run` | Repeat and control | `POST` | `/api/v2/worker-runs/last/abort` |
| 27 | `abort_worker_run` | Repeat and control | `POST` | `/api/v2/worker-runs/{runId}/abort` |
| 28 | `abort_worker_last_run` | Repeat and control | `POST` | `/api/v2/workers/{workerId}/runs/last/abort` |

## Selection Notes

- Use store tools for public marketplace discovery.
- Use private worker tools when the user asks for their own workers.
- Use worker-specific last-run tools only when a known `worker_id` scopes the request.
- Use account-level last-run tools only when the user means the current account's latest run.
- Prefer export tools for file delivery; prefer result-list tools for previews and analysis.
