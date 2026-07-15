# CoreClaw MCP Tool Matrix

Use this reference when choosing the exact MCP tool. The hosted server exposes 34 public tools in workflow order.

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
| 7 | `get_worker_task` | Discovery and preflight | `GET` | `/api/v2/worker-tasks/{workerTaskId}` |
| 8 | `get_worker_task_input` | Discovery and preflight | `GET` | `/api/v2/worker-tasks/{workerTaskId}/input` |
| 9 | `get_account_info` | Discovery and preflight | `GET` | `/api/v2/users/account` |
| 10 | `create_worker_task` | Task management | `POST` | `/api/v2/worker-tasks` |
| 11 | `update_worker_task` | Task management | `PUT` | `/api/v2/worker-tasks/{workerTaskId}` |
| 12 | `update_worker_task_input` | Task management | `PUT` | `/api/v2/worker-tasks/{workerTaskId}/input` |
| 13 | `run_worker` | Execution | `POST` | `/api/v2/workers/{workerId}/runs` |
| 14 | `run_worker_task` | Execution | `POST` | `/api/v2/worker-tasks/{workerTaskId}/runs` |
| 15 | `list_worker_runs` | Run lookup | `GET` | `/api/v2/worker-runs` |
| 16 | `get_last_worker_run` | Run lookup | `GET` | `/api/v2/worker-runs/last` |
| 17 | `get_worker_run` | Run lookup | `GET` | `/api/v2/worker-runs/{runId}` |
| 18 | `get_worker_last_run` | Run lookup | `GET` | `/api/v2/workers/{workerId}/runs/last` |
| 19 | `list_last_worker_run_results` | Output retrieval | `GET` | `/api/v2/worker-runs/last/result` |
| 20 | `export_last_worker_run_results` | Output retrieval | `GET` | `/api/v2/worker-runs/last/export` |
| 21 | `get_last_worker_run_log` | Output retrieval | `GET` | `/api/v2/worker-runs/last/log` |
| 22 | `list_worker_run_results` | Output retrieval | `GET` | `/api/v2/worker-runs/{runId}/result` |
| 23 | `export_worker_run_results` | Output retrieval | `GET` | `/api/v2/worker-runs/{runId}/result/export` |
| 24 | `get_worker_run_log` | Output retrieval | `GET` | `/api/v2/worker-runs/{runId}/log` |
| 25 | `list_worker_last_run_results` | Output retrieval | `GET` | `/api/v2/workers/{workerId}/runs/last/result` |
| 26 | `export_worker_last_run_results` | Output retrieval | `GET` | `/api/v2/workers/{workerId}/runs/last/export` |
| 27 | `get_worker_last_run_log` | Output retrieval | `GET` | `/api/v2/workers/{workerId}/runs/last/log` |
| 28 | `rerun_last_worker_run` | Repeat and control | `POST` | `/api/v2/worker-runs/last/rerun` |
| 29 | `rerun_worker_run` | Repeat and control | `POST` | `/api/v2/worker-runs/{runId}/rerun` |
| 30 | `rerun_worker_last_run` | Repeat and control | `POST` | `/api/v2/workers/{workerId}/runs/last/rerun` |
| 31 | `abort_last_worker_run` | Repeat and control | `POST` | `/api/v2/worker-runs/last/abort` |
| 32 | `abort_worker_run` | Repeat and control | `POST` | `/api/v2/worker-runs/{runId}/abort` |
| 33 | `abort_worker_last_run` | Repeat and control | `POST` | `/api/v2/workers/{workerId}/runs/last/abort` |
| 34 | `delete_worker_task` | Task management | `DELETE` | `/api/v2/worker-tasks/{workerTaskId}` |

## Selection Notes

- Use store tools for public marketplace discovery.
- Use private worker tools when the user asks for their own workers.
- Use worker-specific last-run tools only when a known `worker_id` scopes the request.
- Use account-level last-run tools only when the user means the current account's latest run.
- The `/last` tools (`get_last_worker_run`, `get_worker_last_run`, `list_last_worker_run_results`, `export_last_worker_run_results`, `get_last_worker_run_log`, and the worker-level `/last` variants) can briefly return stale state. When you need authoritative status or results, prefer the runId-specific tools (`get_worker_run`, `list_worker_run_results`, `export_worker_run_results`, `get_worker_run_log`) with a saved `run_id`.
- Prefer export tools for file delivery; prefer result-list tools for previews and analysis.
