# CoreClaw Agent Skill

[English](README.md) | [Simplified Chinese](README.zh-CN.md)

This repository packages the CoreClaw OpenAPI v2 worker workflow as an AI-agent skill. It is MCP-first, v2-only, and designed for agents that need to discover workers, inspect schemas, run jobs, poll status, retrieve results, export files, inspect logs, rerun jobs, abort jobs, and check account quota.

## Contents

```text
.
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- openapi.json
|-- references/
|   |-- coreclaw-v2-workflow.md
|   |-- error-handling.md
|   |-- mcp-tools.md
|   `-- rest-api-fallback.md
`-- scripts/
    |-- generate_references.py
    `-- validate_skill.py
```

## Runtime

- Hosted MCP endpoint: `https://mcp.coreclaw.com/mcp`
- REST API base URL: `https://openapi.coreclaw.com`
- API namespace: `/api/v2`
- Environment variable for REST fallback: `CORECLAW_API_KEY`
- Preferred REST auth: `Authorization: Bearer $CORECLAW_API_KEY`

## Use The Skill

After installing the folder into a skill-aware client, invoke it explicitly or by natural language:

```text
Use $coreclaw to find a worker for coffee shop data, inspect its input schema, run it, and preview the first 20 records.
```

The skill provides the operating procedure. For real CoreClaw actions, configure the CoreClaw MCP server or set `CORECLAW_API_KEY` for REST fallback.

## Configure MCP

Use the hosted MCP server when the agent supports MCP:

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

The server accepts `api-key`, `X-API-Key`, or `Authorization: Bearer <token>` from MCP clients and forwards CoreClaw API auth upstream as Bearer auth.

## Import Into Codex Desktop

Clone this repository directly into the Codex skills directory:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills"
git clone https://github.com/Core-Claw/CoreClaw-Skill.git "$env:USERPROFILE\.codex\skills\coreclaw"
```

Then restart Codex Desktop. The folder name should be `coreclaw`, and `SKILL.md` must be at the folder root:

```text
%USERPROFILE%\.codex\skills\coreclaw\SKILL.md
```

If Codex Desktop offers an import-from-folder or import-from-zip UI, select the folder or archive whose root contains `SKILL.md`. Do not import a parent folder that contains `CoreClaw-Skill` as a nested directory unless the UI explicitly handles nested archives.

Update an existing Codex Desktop install:

```powershell
cd "$env:USERPROFILE\.codex\skills\coreclaw"
git pull
```

Restart Codex Desktop after updating.

## Import Into Other Skill-Aware Agents

Use the same structural rule for Claude Code or other clients: place the whole folder in the agent's skills directory with `SKILL.md` at the skill root. If the client supports explicit skill invocation, use `$coreclaw`.

If the client does not auto-discover skills, attach or reference:

- `SKILL.md`
- `agents/openai.yaml`
- `references/`
- `openapi.json`

## Package The Skill

Before packaging, validate the repository:

```bash
python scripts/validate_skill.py
python C:/Users/user/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

Create a zip package from the repository root on Windows:

```powershell
New-Item -ItemType Directory -Force dist
$files = @("SKILL.md", "agents", "openapi.json", "references", "scripts", "LICENSE", "README.md", "README.zh-CN.md")
Compress-Archive -Path $files -DestinationPath dist/coreclaw-skill.zip -Force
```

Create a zip package on macOS/Linux:

```bash
mkdir -p dist
zip -r dist/coreclaw-skill.zip SKILL.md agents openapi.json references scripts LICENSE README.md README.zh-CN.md -x "*/__pycache__/*" "*.pyc"
```

The archive root must contain `SKILL.md`. Validate the extracted package before distribution:

```bash
python scripts/validate_skill.py
```

## Public MCP Surface

The CoreClaw MCP server exposes 28 public tools covering:

- discovery and preflight
- ad-hoc worker runs
- saved worker task runs
- run lookup and polling
- result previews
- CSV/JSON exports
- logs
- reruns
- abort controls

The skill deliberately exposes only the public 28-operation CoreClaw MCP/API v2 surface. See `references/mcp-tools.md` for the exact tool matrix.

## Agent Workflow

1. Use `list_store_workers` for public marketplace discovery or `list_workers` for user-owned workers.
2. Use `get_worker_input_schema` before `run_worker`.
3. Use `run_worker` for ad-hoc schema-aligned input or `run_worker_task` for saved task presets.
4. Save the returned run identifier as `run_id`.
5. Poll run detail until terminal status.
6. Preview results with list-result tools or export large outputs.
7. Inspect logs when a run fails or produces unexpected output.

## REST Fallback

REST is a fallback when MCP is unavailable. Set an API key without committing it:

```bash
export CORECLAW_API_KEY="your-coreclaw-token"
```

PowerShell:

```powershell
$env:CORECLAW_API_KEY = "your-coreclaw-token"
```

Use only `/api/v2` endpoints. See `references/rest-api-fallback.md` for curl examples.

## Maintenance

Regenerate references from the sibling source repositories:

```bash
python scripts/generate_references.py --copy-openapi
```

Validate the package:

```bash
python scripts/validate_skill.py
python C:/Users/user/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

Expected contract:

- Bundled public OpenAPI operations: 28
- Public MCP tools: 28
- Excluded operations: 3
- No legacy v1 workflow terms in the skill docs

## Example Prompts

- "Use CoreClaw to find a worker for coffee shop data, inspect its input schema, run it, and preview the first 20 records."
- "Run this saved CoreClaw task asynchronously, poll until it finishes, then export CSV."
- "This CoreClaw run failed. Check run detail and logs, then explain the failure with request id evidence."
- "Rerun the latest CoreClaw worker run and show the new run id."
