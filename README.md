# CoreClaw Agent Skill

[English](README.md) | [简体中文](README.zh-CN.md)

This repository packages CoreClaw usage instructions for AI agents. It helps an agent move through the full CoreClaw workflow: discover a scraper, read its live schema, start a run, poll status, fetch results, export files, inspect logs, rerun jobs, abort jobs, and check account quota.

It is intentionally small:

```text
.
├── LICENSE
├── README.md
├── README.zh-CN.md
├── SKILL.md
└── openapi.json
```

## What Each File Does

- `SKILL.md`: the agent playbook. Skill-enabled agents load this file and follow its workflow.
- `openapi.json`: the API contract reference for exact endpoints, parameters, and response shapes.
- `README.md` / `README.zh-CN.md`: concise human setup and maintenance notes.
- `LICENSE`: repository license.

## Install The Skill

### Codex

Place the repository under the Codex skills directory:

```bash
~/.codex/skills/coreclaw
```

On Windows, the equivalent path is usually:

```powershell
$env:USERPROFILE\.codex\skills\coreclaw
```

Restart Codex after copying the folder.

### Claude Code Or Other Skill-Aware Agents

Place the full repository in the agent's skill directory and make sure `SKILL.md` stays at the folder root.

If the agent does not support automatic skill discovery, attach or reference:

- `SKILL.md`
- `openapi.json`

## Runtime Requirements

- API base URL: `https://openapi.coreclaw.com`
- Environment variable: `CORECLAW_API_KEY`
- Auth header: `api-key: $CORECLAW_API_KEY`
- Required command-line tool: `curl`
- Optional command-line tool: `jq` for formatting and filtering JSON

Set the API key:

```bash
export CORECLAW_API_KEY="your_api_key"
```

PowerShell:

```powershell
$env:CORECLAW_API_KEY = "your_api_key"
```

Do not commit real API keys.

## How The Agent Should Work

The safe workflow is:

1. Search for a scraper with `/api/store`.
2. Fetch scraper detail with `/api/scraper`.
3. Read `data.version`, `data.parameters.custom`, and `data.parameters.system`.
4. Build `input.parameters.custom` from the live schema.
5. Start a run with `/api/v1/scraper/run`.
6. Save `run_slug`.
7. Poll `/api/v1/run/detail`.
8. Read results with `/api/v1/run/result/list` or export with `/api/v1/run/result/export`.
9. If anything fails, inspect `/api/v1/run/last/log`.

The most important rule: `data.parameters.custom` is a schema descriptor. It is not the payload to paste into `input.parameters.custom`.

## Core API Capabilities

| Capability | Endpoint |
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

## Example Prompts

- "Find a CoreClaw scraper for Amazon product listings, read its live schema, run it with keyword `wireless mouse`, and show the first 20 results."
- "Start this scraper asynchronously, save the `run_slug`, poll status until it finishes, then export CSV if there are more than 50 records."
- "This run failed. Check run detail and latest logs, then summarize the real failure reason."
- "Rerun this historical `run_slug`, track the new run, and preview the first 10 records."

## MCP Option

If the agent supports MCP, configure the CoreClaw remote MCP server instead of writing HTTP calls by hand:

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

MCP gives the agent named tools. This skill still provides the operating method: discover, inspect, run, track, retrieve, and diagnose.

## Maintainer Checks

Before publishing a change:

```bash
git diff --check
node -e "JSON.parse(require('fs').readFileSync('openapi.json','utf8'))"
```

Then verify:

- `SKILL.md` frontmatter is valid YAML.
- README links point to existing files.
- All examples use the current `memory` field for MB allocation.
- Scraper run examples fetch `/api/scraper` before `/api/v1/scraper/run`.
- Task and rerun examples follow the current `callback_url` rules in `openapi.json`.

## Support Boundary

Open an issue with:

- the agent or host application used
- the scraper slug or run slug, if relevant
- sanitized request payload
- sanitized response or log excerpt
- steps to reproduce

Do not share real API keys, private datasets, or full credentials in issues.

For product documentation, visit [CoreClaw](https://coreclaw.com).
