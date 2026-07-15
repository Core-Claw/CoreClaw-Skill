# CoreClaw Error Handling

Use this reference when an HTTP call or MCP tool reports a failed CoreClaw request.

## Response Layers

- HTTP status describes transport/request handling.
- JSON `code` describes CoreClaw business outcome.
- `code: 0` means success.
- Keep `message`, `request_id`, and any validation `details` in the user-facing diagnosis.

## Error Codes

| Code | Key | Message |
| --- | --- | --- |
| `10000` | SYSTEM_ERROR | internal server error |
| `11000` | INVALID_ARGUMENT | invalid argument |
| `11004` | NOT_FOUND | not found |
| `12001` | UNAUTHORIZED | authentication required |
| `12002` | INVALID_TOKEN | invalid token |
| `13000` | RATE_LIMITED | too many requests |
| `14000` | DATABASE_ERROR | database error |
| `30001` | INSUFFICIENT_BALANCE | account balance is insufficient |
| `50001` | WORKER_NOT_FOUND | worker does not exist |
| `50002` | WORKER_RUN_FAILED | worker run failed |
| `50003` | WORKER_VERSION_UNAVAILABLE | the worker version is not available |
| `60001` | TASK_NOT_FOUND | task does not exist |
| `70001` | RUN_NOT_FOUND | run record does not exist |
| `70002` | RUN_FAILED | run operation failed |
| `16000` | NOT_IMPLEMENTED | not implemented |

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
