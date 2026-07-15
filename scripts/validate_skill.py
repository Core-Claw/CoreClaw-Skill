#!/usr/bin/env python3
"""Validate the CoreClaw skill package against the public v2 MCP/API surface."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


EXPECTED_TOOL_ORDER = [
    "list_proxy_regions",
    "list_store_workers",
    "list_workers",
    "get_worker",
    "get_worker_input_schema",
    "list_worker_tasks",
    "get_worker_task",
    "get_worker_task_input",
    "get_account_info",
    "create_worker_task",
    "update_worker_task",
    "update_worker_task_input",
    "run_worker",
    "run_worker_task",
    "list_worker_runs",
    "get_last_worker_run",
    "get_worker_run",
    "get_worker_last_run",
    "list_last_worker_run_results",
    "export_last_worker_run_results",
    "get_last_worker_run_log",
    "list_worker_run_results",
    "export_worker_run_results",
    "get_worker_run_log",
    "list_worker_last_run_results",
    "export_worker_last_run_results",
    "get_worker_last_run_log",
    "rerun_last_worker_run",
    "rerun_worker_run",
    "rerun_worker_last_run",
    "abort_last_worker_run",
    "abort_worker_run",
    "abort_worker_last_run",
    "delete_worker_task",
]

FORBIDDEN_PATTERNS = [
    "/api/v1",
    "/api/scraper",
    "scraper_slug",
    "task_slug",
    "page_index",
    "page_size",
]

DOC_FILES = [
    "skills/coreclaw/SKILL.md",
    "README.md",
    "README.zh-CN.md",
    "skills/coreclaw/references/coreclaw-v2-workflow.md",
    "skills/coreclaw/references/mcp-tools.md",
    "skills/coreclaw/references/rest-api-fallback.md",
    "skills/coreclaw/references/error-handling.md",
    "agents/openai.yaml",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{path} is not valid UTF-8: {exc}")


def parse_frontmatter(skill: str) -> dict[str, str]:
    match = re.match(r"---\n(?P<body>.*?)\n---\n", skill, re.S)
    if not match:
        fail("SKILL.md is missing YAML frontmatter")
    data: dict[str, str] = {}
    for line in match.group("body").splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            fail(f"invalid frontmatter line: {line}")
        value = value.strip()
        if ": " in value and not (value.startswith('"') and value.endswith('"')):
            fail(f"frontmatter value containing colon must be quoted: {key}")
        data[key.strip()] = value.strip('"')
    return data


def validate_skill_md(repo: Path) -> None:
    text = read_text(repo / "skills" / "coreclaw" / "SKILL.md")
    frontmatter = parse_frontmatter(text)
    if set(frontmatter) != {"name", "description"}:
        fail("SKILL.md frontmatter must contain only name and description")
    if frontmatter["name"] != "coreclaw":
        fail("skill name must be coreclaw")
    description = frontmatter["description"]
    if not description.startswith("Use when"):
        fail("description must start with 'Use when'")
    for needle in ["CoreClaw", "MCP", "workers", "runs"]:
        if needle not in description:
            fail(f"description must mention {needle}")
    for needle in ["MCP-first", "run_worker", "get_worker_input_schema", "run_id"]:
        if needle not in text:
            fail(f"SKILL.md missing required workflow term: {needle}")


def validate_openapi(repo: Path) -> None:
    raw = read_text(repo / "openapi.json")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"openapi.json is not valid JSON: {exc}")
    paths = spec.get("paths", {})
    if spec.get("openapi") != "3.1.0":
        fail("openapi.json must be OpenAPI 3.1.0")
    operations = sum(
        1
        for item in paths.values()
        for method in item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    )
    if operations != 34:
        fail(f"openapi.json must contain 34 public operations, found {operations}")
    if not all(path.startswith("/api/v2/") for path in paths):
        fail("all OpenAPI paths must be /api/v2")
    serialized = json.dumps(spec, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in serialized:
            fail(f"openapi.json contains forbidden term: {pattern}")
    validate_no_duplicate_json_keys(raw)
    validate_run_worker_input_examples(spec)


def validate_no_duplicate_json_keys(raw: str) -> None:
    """json.loads silently keeps the last value on duplicate object keys, so
    scan the raw text for the actual defect. This catches generator sanitize
    regressions like {"run_status":"succeeded","run_status":"succeeded"}.
    """
    # Tokenize JSON object keys and track open object scopes so we only flag
    # the same key appearing twice inside the same object.
    stack: list[set[str]] = []
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == '"':
            # Read the full string token.
            j = i + 1
            while j < n:
                c = raw[j]
                if c == "\\":
                    j += 2
                    continue
                if c == '"':
                    break
                j += 1
            token = raw[i + 1 : j]
            # Peek past the closing quote to see whether this string is a key
            # (followed by ':') — keys are what we deduplicate within a scope.
            k = j + 1
            while k < n and raw[k] in " \t\r\n":
                k += 1
            is_key = k < n and raw[k] == ":"
            if is_key and stack:
                if token in stack[-1]:
                    fail(f"openapi.json has duplicate object key: {token!r}")
                stack[-1].add(token)
            i = j + 1
            continue
        if ch == "{":
            stack.append(set())
            i += 1
            continue
        if ch == "}":
            if stack:
                stack.pop()
            i += 1
            continue
        i += 1


def validate_run_worker_input_examples(spec: dict) -> None:
    """run_worker request-body examples must nest business input under
    input.parameters.custom. A flat input ({"input":{"keyword":"coffee"}})
    makes a saved task un-runnable upstream ("Keyword is required"), so guard
    against the upstream flat-example shape sneaking back into the bundle.
    """
    runs_post = spec.get("paths", {}).get("/api/v2/workers/{workerId}/runs", {}).get("post", {})
    content = runs_post.get("requestBody", {}).get("content", {})
    for media in content.values():
        for name, example in media.get("examples", {}).items():
            value = example.get("value")
            if not isinstance(value, dict):
                continue
            input_field = value.get("input")
            if not isinstance(input_field, dict):
                continue
            if "parameters" not in input_field:
                fail(
                    f"run_worker example {name!r} must nest input under "
                    f"input.parameters.custom, got flat input: {input_field!r}"
                )
            custom = input_field.get("parameters", {}).get("custom")
            if not isinstance(custom, dict):
                fail(
                    f"run_worker example {name!r} has input.parameters.custom "
                    f"missing or not an object"
                )


def validate_references(repo: Path) -> None:
    for name in DOC_FILES:
        if not (repo / name).is_file():
            fail(f"missing file: {name}")

    mcp = read_text(repo / "skills" / "coreclaw" / "references" / "mcp-tools.md")
    positions: list[int] = []
    for tool in EXPECTED_TOOL_ORDER:
        pos = mcp.find(f"`{tool}`")
        if pos < 0:
            fail(f"mcp-tools.md missing tool {tool}")
        positions.append(pos)
    if positions != sorted(positions):
        fail("mcp-tools.md tool order does not match MCP workflow order")


def validate_agents(repo: Path) -> None:
    text = read_text(repo / "agents" / "openai.yaml")
    for needle in [
        'display_name: "CoreClaw"',
        'default_prompt: "Use $coreclaw',
        'type: "mcp"',
        'value: "coreclaw"',
        'transport: "streamable_http"',
        'url: "https://mcp.coreclaw.com/mcp"',
    ]:
        if needle not in text:
            fail(f"agents/openai.yaml missing {needle}")


def validate_text(repo: Path) -> None:
    for name in DOC_FILES:
        text = read_text(repo / name)
        if "\ufffd" in text or "鈹" in text or "锟" in text:
            fail(f"{name} contains mojibake or replacement characters")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in text:
                fail(f"{name} contains forbidden term: {pattern}")


def main() -> None:
    repo = repo_root()
    validate_skill_md(repo)
    validate_openapi(repo)
    validate_references(repo)
    validate_agents(repo)
    validate_text(repo)
    print("CoreClaw skill validation passed")
    print("OpenAPI v2 public operations: 34")
    print("MCP public tools: 34")


if __name__ == "__main__":
    main()
