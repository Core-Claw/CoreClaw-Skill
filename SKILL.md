---
name: coreclaw
description: Use CoreClaw from an AI agent. Discover scrapers, read live schemas, run jobs, poll status, fetch or export results, inspect logs, rerun jobs, abort jobs, and check account quota.
homepage: https://coreclaw.com
metadata:
  openclaw:
    primaryEnv: CORECLAW_API_KEY
    requires:
      bins: [curl]
      env: [CORECLAW_API_KEY]
---

# CoreClaw Agent Skill

Use this skill when the user wants an AI agent to operate CoreClaw directly: find a scraper, inspect its live input schema, start a run, watch progress, retrieve data, export files, troubleshoot failures, or repeat a previous run.

This repository is not an SDK. `SKILL.md` is the agent playbook, and `openapi.json` is the API contract reference.

## Runtime

- Base URL: `https://openapi.coreclaw.com`
- API key environment variable: `CORECLAW_API_KEY`
- Auth header: `api-key: $CORECLAW_API_KEY`
- Required local tool: `curl`
- Optional local tool: `jq` for formatting and filtering JSON

Before calling authenticated endpoints, check that `CORECLAW_API_KEY` is set. Do not print the key.

## Core Rules

1. Always fetch scraper detail before running a scraper.
2. Treat `data.parameters.custom` from `GET /api/scraper` as a schema descriptor, not as the run payload.
3. Build `input.parameters.custom` from the live schema. Do not hardcode fields such as `startURLs`, `url`, or `keyword`.
4. Use the `version` returned by scraper detail. Do not invent a version.
5. Keep the returned `run_slug`; every status, result, log, export, rerun, and abort operation depends on it.
6. Prefer inline result preview for small result sets and export for large result sets.
7. If a run fails, inspect run detail first, then logs.

## Endpoint Map

| Job | Endpoint |
| --- | --- |
| Search marketplace | `GET /api/store` |
| Get scraper detail and live schema | `GET /api/scraper` |
| Start scraper run | `POST /api/v1/scraper/run` |
| Abort running job | `POST /api/v1/scraper/abort` |
| List historical runs | `POST /api/v1/run/list` |
| Get run detail/status | `POST /api/v1/run/detail` |
| Read paginated results | `POST /api/v1/run/result/list` |
| Export results | `POST /api/v1/run/result/export` |
| Read latest logs | `POST /api/v1/run/last/log` |
| Rerun previous job | `POST /api/v1/rerun` |
| Run saved task | `POST /api/v1/task/run` |
| Check account quota | `POST /api/v1/account/info` |

Use `openapi.json` for exact parameters, response fields, and examples.

## Standard Workflow

### 1. Discover

Search the marketplace when the user describes a target site or data need.

```bash
curl -s "https://openapi.coreclaw.com/api/store?keyword=amazon"
```

Pick a scraper by relevance and save its `scraper_slug`.

### 2. Inspect

Fetch scraper detail before every new run.

```bash
curl -s "https://openapi.coreclaw.com/api/scraper?slug=$SCRAPER_SLUG"
```

Read:

- `data.version`
- `data.parameters.custom`
- `data.parameters.system`

The system memory field is `memory` in MB. Use it as `input.parameters.system.memory` when starting a run.

### 3. Build Input

Create a run payload with this shape:

```json
{
  "scraper_slug": "SCRAPER_SLUG",
  "version": "VERSION_FROM_DETAIL",
  "is_async": true,
  "input": {
    "parameters": {
      "custom": {},
      "system": {
        "cpus": 0.25,
        "memory": 512,
        "max_total_charge": 0,
        "max_total_traffic": 0,
        "execute_limit_time_seconds": 1800
      }
    }
  }
}
```

Replace `custom` with values derived from the live schema. If required fields are unclear, ask the user for the missing business input rather than guessing.

### 4. Run

```bash
curl -s -X POST "https://openapi.coreclaw.com/api/v1/scraper/run" \
  -H "Content-Type: application/json" \
  -H "api-key: $CORECLAW_API_KEY" \
  -d @payload.json
```

Save `data.run_slug` from the response.

### 5. Track

```bash
curl -s -X POST "https://openapi.coreclaw.com/api/v1/run/detail" \
  -H "Content-Type: application/json" \
  -H "api-key: $CORECLAW_API_KEY" \
  -d "{\"run_slug\":\"$RUN_SLUG\"}"
```

Poll until the run reaches a terminal state. If the API returns numeric statuses, use the response meaning from `openapi.json` and include the raw status in the final explanation.

### 6. Retrieve

Preview smaller result sets:

```bash
curl -s -X POST "https://openapi.coreclaw.com/api/v1/run/result/list" \
  -H "Content-Type: application/json" \
  -H "api-key: $CORECLAW_API_KEY" \
  -d "{\"run_slug\":\"$RUN_SLUG\",\"page_index\":1,\"page_size\":20}"
```

Export larger result sets:

```bash
curl -s -X POST "https://openapi.coreclaw.com/api/v1/run/result/export" \
  -H "Content-Type: application/json" \
  -H "api-key: $CORECLAW_API_KEY" \
  -d "{\"run_slug\":\"$RUN_SLUG\",\"format\":\"csv\"}"
```

### 7. Diagnose

When a run fails or stalls:

1. Read run detail.
2. Read latest logs.
3. Summarize the failure cause, useful evidence, and next action.

```bash
curl -s -X POST "https://openapi.coreclaw.com/api/v1/run/last/log" \
  -H "Content-Type: application/json" \
  -H "api-key: $CORECLAW_API_KEY" \
  -d "{\"run_slug\":\"$RUN_SLUG\"}"
```

## Saved Tasks And Reruns

Use saved tasks when the user already has a configured `task_slug`.

Use rerun when the user wants to repeat an existing `run_slug` with the same inputs.

For REST API calls, follow the `callback_url` requirements in `openapi.json`. When using the CoreClaw MCP server, the server may provide its own callback handling, so prefer the MCP tool schema over hand-written REST assumptions.

## MCP Alternative

If the user's agent has the CoreClaw MCP server configured, prefer MCP tools over manual HTTP calls. The common remote MCP configuration is:

```json
{
  "mcpServers": {
    "coreclaw": {
      "url": "https://mcp.coreclaw.com/mcp",
      "headers": {
        "api-key": "scraper_api_YOUR_KEY_HERE"
      }
    }
  }
}
```

MCP gives the agent named tools for the same workflow. This skill still provides the operating procedure: discover, inspect, run, track, retrieve, and diagnose.

## Response Style

When reporting back to the user:

- explain which scraper was selected and why
- show the required input fields before running when possible
- keep `run_slug` visible for follow-up operations
- preview representative records instead of dumping large datasets
- provide export links for large datasets
- include actionable failure evidence if something breaks

## Final Checklist

Before claiming the task is complete, confirm:

- scraper detail was fetched from the live API
- run payload used the live schema and returned version
- `run_slug` was saved
- terminal status was checked
- results were previewed or exported
- logs were inspected if the run failed
