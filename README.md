# CoreClaw Agent Skill

[English](README.md) | [Simplified Chinese](README.zh-CN.md)

This repository packages the CoreClaw OpenAPI v2 worker workflow as an AI-agent skill. It is MCP-first, v2-only, and designed for agents that need to discover workers, inspect schemas, run jobs, poll status, retrieve results, export files, inspect logs, rerun jobs, abort jobs, and check account quota.

## Contents

```text
.
|-- .claude-plugin/
|   |-- marketplace.json
|   `-- plugin.json
|-- .mcp.json
|-- agents/
|   `-- openai.yaml
|-- openapi.json
|-- skills/
|   `-- coreclaw/
|       |-- SKILL.md
|       `-- references/
|           |-- coreclaw-v2-workflow.md
|           |-- error-handling.md
|           |-- mcp-tools.md
|           `-- rest-api-fallback.md
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
- Scripts require Python 3.9+ (standard library only; no third-party packages).

## Use The Skill

After installing the folder into a skill-aware client, invoke it explicitly or by natural language:

```text
Use $coreclaw to find a worker for coffee shop data, inspect its input schema, run it, and preview the first 20 records.
```

The skill provides the operating procedure. For real CoreClaw actions, configure the CoreClaw MCP server or set `CORECLAW_API_KEY` for REST fallback.

## Install as a Claude Code Plugin (Recommended)

Add this repository as a plugin marketplace and install in two commands:

```bash
claude plugin marketplace add Core-Claw/CoreClaw-Skill
claude plugin install coreclaw@coreclaw-skill
```

Or inside a Claude Code session:

```text
/plugin marketplace add Core-Claw/CoreClaw-Skill
/plugin install coreclaw@coreclaw-skill
```

The plugin bundles the CoreClaw MCP server (`.mcp.json`) and the skill. After install, set your API token once so the MCP server can authenticate:

```bash
export CORECLAW_API_KEY="your-coreclaw-token"        # macOS/Linux
```

```powershell
$env:CORECLAW_API_KEY = "your-coreclaw-token"        # Windows PowerShell
```

When invoked through the plugin, the skill is namespaced as `/coreclaw-skill:coreclaw`.

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

The Codex skill layout requires `SKILL.md` at `<skills-dir>/coreclaw/SKILL.md`. This repo keeps the skill under `skills/coreclaw/`, so clone it to a working location and expose that subfolder to Codex:

```powershell
git clone https://github.com/Core-Claw/CoreClaw-Skill.git "$env:USERPROFILE\CoreClaw-Skill"
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.codex\skills\coreclaw" -Target "$env:USERPROFILE\CoreClaw-Skill\skills\coreclaw"
```

Then restart Codex Desktop. Codex sees the skill at:

```text
%USERPROFILE%\.codex\skills\coreclaw\SKILL.md
```

If Codex Desktop offers an import-from-folder or import-from-zip UI, point it at the `skills/coreclaw` folder (whose root contains `SKILL.md`). Do not import the repository root.

Update an existing Codex Desktop install:

```powershell
cd "$env:USERPROFILE\CoreClaw-Skill"
git pull
```

Restart Codex Desktop after updating.

## Use as a Standalone Claude Code Skill

Clone directly into the Claude Code skills directory (no manifest, no install step):

```bash
git clone https://github.com/Core-Claw/CoreClaw-Skill.git ~/.claude/skills/coreclaw
```

The skill loads as `/coreclaw` (no namespace). The bundled `.mcp.json` only auto-registers the CoreClaw MCP server when the repo is installed as a plugin; for standalone use you must configure the MCP server or set `CORECLAW_API_KEY` yourself (see [Configure MCP](#configure-mcp) and [REST Fallback](#rest-fallback)).

## Import Into Other Skill-Aware Agents

For clients other than Claude Code and Codex Desktop, use the same structural rule: place the `skills/coreclaw` folder in the agent's skills directory with `SKILL.md` at the skill root. If the client supports explicit skill invocation, use `$coreclaw`.

If the client does not auto-discover skills, attach or reference:

- `skills/coreclaw/SKILL.md`
- `agents/openai.yaml`
- `skills/coreclaw/references/`
- `openapi.json`

## Package The Skill

Before packaging, validate the repository:

```bash
python scripts/validate_skill.py
```

If the Codex skill-creator toolchain is installed, its validator can also be run (optional, machine-dependent path):

```bash
python "$USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .   # Windows
python "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .           # macOS/Linux
```

Create a zip package from the repository root on Windows:

```powershell
New-Item -ItemType Directory -Force dist
$files = @("skills", "agents", "openapi.json", ".mcp.json", ".claude-plugin", "scripts", "LICENSE", "README.md", "README.zh-CN.md")
Compress-Archive -Path $files -DestinationPath dist/coreclaw-skill.zip -Force
```

Create a zip package on macOS/Linux:

```bash
mkdir -p dist
zip -r dist/coreclaw-skill.zip skills agents openapi.json .mcp.json .claude-plugin scripts LICENSE README.md README.zh-CN.md -x "*/__pycache__/*" "*.pyc"
```

The archive root must contain `.claude-plugin/` and `skills/coreclaw/SKILL.md`. Validate the extracted package before distribution:

```bash
python scripts/validate_skill.py
```

## Public MCP Surface

The CoreClaw MCP server exposes 34 public tools covering:

- discovery and preflight
- saved worker task CRUD (create, get, update, update input, delete)
- ad-hoc worker runs
- saved worker task runs
- run lookup and polling
- result previews
- CSV/JSON exports
- logs
- reruns
- abort controls

The skill deliberately exposes only the public 34-operation CoreClaw MCP/API v2 surface. See `references/mcp-tools.md` for the exact tool matrix.

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
```

If the Codex skill-creator toolchain is installed, its `quick_validate.py` can also be run (optional, machine-dependent path; see the Package The Skill section).

Expected contract:

- Bundled public OpenAPI operations: 34
- Public MCP tools: 34
- Excluded operations: 3
- No legacy v1 workflow terms in the skill docs

## Example Prompts

- "Use CoreClaw to find a worker for coffee shop data, inspect its input schema, run it, and preview the first 20 records."
- "Run this saved CoreClaw task asynchronously, poll until it finishes, then export CSV."
- "This CoreClaw run failed. Check run detail and logs, then explain the failure with request id evidence."
- "Rerun the latest CoreClaw worker run and show the new run id."
