# CoreClaw REST API Fallback

Use REST only when MCP tools are unavailable or the user explicitly asks for raw HTTP examples.

## Auth

Prefer Bearer auth:

```bash
-H "Authorization: Bearer $CORECLAW_API_KEY"
```

The API also supports the legacy `api-key` header and `?token=` query parameter. Avoid query tokens unless headers are impossible.

## Public Skill Surface

| Tag | Method | Path | Summary | Auth |
| --- | --- | --- | --- | --- |
| proxy | `GET` | `/api/v2/proxy/region` | List proxy regions | Public |
| store | `GET` | `/api/v2/store` | List store workers | Public |
| account | `GET` | `/api/v2/users/account` | Get user account | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/worker-runs` | List worker runs | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/worker-runs/last` | Get last worker run | BearerAuth OR QueryTokenAuth |
| worker-runs | `POST` | `/api/v2/worker-runs/last/abort` | Abort last worker run | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/worker-runs/last/export` | Export last worker run results | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/worker-runs/last/log` | Get last worker run log | BearerAuth OR QueryTokenAuth |
| worker-runs | `POST` | `/api/v2/worker-runs/last/rerun` | Rerun last worker run | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/worker-runs/last/result` | List last worker run results | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/worker-runs/{runId}` | Get worker run detail | BearerAuth OR QueryTokenAuth |
| worker-runs | `POST` | `/api/v2/worker-runs/{runId}/abort` | Abort worker run | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/worker-runs/{runId}/log` | Get worker run log | BearerAuth OR QueryTokenAuth |
| worker-runs | `POST` | `/api/v2/worker-runs/{runId}/rerun` | Rerun worker run | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/worker-runs/{runId}/result` | List worker run results | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/worker-runs/{runId}/result/export` | Export worker run results | BearerAuth OR QueryTokenAuth |
| worker-tasks | `GET` | `/api/v2/worker-tasks` | List worker tasks | BearerAuth OR QueryTokenAuth |
| worker-tasks | `POST` | `/api/v2/worker-tasks/{workerTaskId}/runs` | Run worker task | BearerAuth OR QueryTokenAuth |
| workers | `GET` | `/api/v2/workers` | List current user workers | BearerAuth OR QueryTokenAuth |
| workers | `GET` | `/api/v2/workers/{workerId}` | Get worker detail | BearerAuth OR QueryTokenAuth |
| workers | `GET` | `/api/v2/workers/{workerId}/input-schema` | Get worker input schema | Public |
| workers | `POST` | `/api/v2/workers/{workerId}/runs` | Run worker | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/workers/{workerId}/runs/last` | Get worker last run | BearerAuth OR QueryTokenAuth |
| worker-runs | `POST` | `/api/v2/workers/{workerId}/runs/last/abort` | Abort worker last run | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/workers/{workerId}/runs/last/export` | Export worker last run results | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/workers/{workerId}/runs/last/log` | Get worker last run log | BearerAuth OR QueryTokenAuth |
| worker-runs | `POST` | `/api/v2/workers/{workerId}/runs/last/rerun` | Rerun worker last run | BearerAuth OR QueryTokenAuth |
| worker-runs | `GET` | `/api/v2/workers/{workerId}/runs/last/result` | List worker last run results | BearerAuth OR QueryTokenAuth |

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
curl -s -X POST "https://openapi.coreclaw.com/api/v2/workers/$WORKER_ID/runs" \
  -H "Authorization: Bearer $CORECLAW_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{"input":{"parameters":{"custom":{"keyword":"coffee","limit":10}}},"is_async":true,"offset":0,"limit":20}'
```

Run a saved task asynchronously:

```bash
curl -s -X POST "https://openapi.coreclaw.com/api/v2/worker-tasks/$WORKER_TASK_ID/runs" \
  -H "Authorization: Bearer $CORECLAW_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{"is_async":true}'
```

Poll a run:

```bash
curl -s "https://openapi.coreclaw.com/api/v2/worker-runs/$RUN_ID" \
  -H "Authorization: Bearer $CORECLAW_API_KEY"
```

Preview results:

```bash
curl -s "https://openapi.coreclaw.com/api/v2/worker-runs/$RUN_ID/result?offset=0&limit=20" \
  -H "Authorization: Bearer $CORECLAW_API_KEY"
```

Export results:

```bash
curl -s "https://openapi.coreclaw.com/api/v2/worker-runs/$RUN_ID/result/export?format=csv&filter_keys=title%2Caddress" \
  -H "Authorization: Bearer $CORECLAW_API_KEY"
```
