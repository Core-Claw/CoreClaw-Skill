# Cafe Agent Skill

[English](README.md) | [简体中文](README.zh-CN.md)

A reusable Cafe workflow definition for AI coding agents.

## Overview

Cafe provides scraper discovery and execution through its REST API. This repository packages the standard Cafe workflow in a skill-oriented format built around `SKILL.md` and `openapi.json`.

It is intended for AI agent environments, including:

- Codex
- Claude Code
- other agent runtimes that can consume structured workflow instructions

The repository covers the operational flow required to:

- find the right scraper in Cafe Store
- read scraper metadata, version, and input schema
- launch asynchronous scraper runs
- monitor run status safely
- read paginated result data inline
- export larger result sets as CSV or JSON
- inspect logs, rerun jobs, abort runs, and check account info

## What This Repository Includes

```text
.
├── README.md      # GitHub-facing project documentation
├── SKILL.md       # The skill definition, workflow, and operational instructions
└── openapi.json   # Cafe OpenAPI spec used as the API reference
```

## Current Capability

The skill currently covers the main Cafe API workflow:

- search Cafe Store for available scrapers
- get scraper details, parameter schema, and README content
- start scraper runs
- poll run status with guardrails
- fetch inline paginated results
- export results to CSV or JSON
- run saved tasks
- rerun previous jobs
- inspect recent logs
- abort in-progress runs
- read account balance and traffic usage
- list historical runs

## How It Works

This repository is not an SDK. It is a workflow package centered on `SKILL.md`.

- `SKILL.md` defines when the skill should trigger and how the agent should operate
- `openapi.json` provides the complete API-level reference
- the agent follows the documented Cafe workflow step by step once the skill is triggered

At a high level, the workflow is:

1. `GET /api/store` to find a scraper
2. `GET /api/scraper` to read `version`, system defaults, and custom input schema
3. `POST /api/v1/scraper/run` to start an async job
4. `POST /api/v1/run/detail` to monitor progress
5. `POST /api/v1/run/result/list` or `POST /api/v1/run/result/export` to retrieve output
6. optionally use logs, rerun, abort, history, and account endpoints

## Compatibility

This repository provides workflow and API definitions. Host-specific loading or installation depends on the target environment.

- Codex: can use the repository as a skill package
- Claude Code: can use `SKILL.md` as workflow instructions and `openapi.json` as the API reference
- Other agent environments: can reuse the same files through their own prompt, tool, or workflow conventions

## Prerequisites

Before using this skill, make sure you have:

- `curl`
- `jq`
- a valid `CAFE_API_KEY`
- network access to `https://openapi.cafescraper.com`

Set your API key:

```bash
export CAFE_API_KEY="your_api_key"
```

## Installation

For environments that support skill directories, place this repository according to the host environment's conventions.

For example, in Codex-style setups:

```bash
~/.codex/skills/cafe
```

The required entry file is:

```bash
SKILL.md
```

Restart your agent environment after installation so the skill is loaded.

## Example Prompts

These are examples of requests that fit this workflow:

- "Find a Cafe scraper for Amazon product listings."
- "Read the scraper parameters and start a run for me."
- "Keep polling this `run_slug` and show me the first 20 results when it finishes."
- "Export this run's results as CSV."
- "Check why this run failed and extract the error logs."
- "Show my current Cafe account balance and traffic usage."

## Design Decisions

This skill intentionally enforces a few workflow rules:

- a scraper run should always begin by reading `/api/scraper`
- `version` should come from the scraper detail response, not from guesswork
- small datasets are better handled with `result/list`
- larger datasets are better handled with `result/export`
- polling should include consecutive-error protection to avoid infinite loops
- logs, rerun, abort, and account endpoints are included so the workflow is operationally complete

## When To Use Inline Results vs Export

Use inline result listing when:

- you want the agent to inspect or summarize the data immediately
- the dataset is small enough to fit comfortably in context

Use export when:

- the user wants a downloadable file
- the result set is large
- you need a clean CSV or JSON artifact outside the context window

## Notes

- most endpoints require `CAFE_API_KEY`
- the run endpoints require a `callback_url`; the skill currently documents a test callback
- large result sets should usually be exported instead of injected directly into the model context
- polling logic should sanitize malformed control characters before passing JSON into `jq`

## References

- Cafe Store: https://cafescraper.com
- Cafe OpenAPI spec: `openapi.json`
- Skill entry point: `SKILL.md`

## License

This project is released under the MIT License. See `LICENSE` for details.

---

This repository provides a structured starting point for integrating Cafe scraping workflows into AI agent environments.
