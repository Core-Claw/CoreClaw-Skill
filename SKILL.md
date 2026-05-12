---
name: cafe
description: Run Cafe scrapers and retrieve structured results using the Cafe REST API with curl. Use when the user wants to scrape websites, collect data from supported platforms, run a Cafe scraper, monitor runs, fetch results, export data, or debug a failed run.
homepage: https://cafescraper.com
metadata:
  openclaw:
    primaryEnv: CAFE_API_KEY
    requires:
      bins:
        - curl
        - jq
      env:
        - CAFE_API_KEY
---

# Cafe

Run scrapers on [Cafe Store](https://cafescraper.com) and retrieve structured results via the REST API.

Full OpenAPI spec: [openapi.json](openapi.json)

## Authentication

Most endpoints need the `CAFE_API_KEY` env var. Use it as an `api-key` header:

```bash
-H "api-key: $CAFE_API_KEY"
```

Base URL: `https://openapi.cafescraper.com`

**Public endpoints** (no API key needed): `/api/store` (search scrapers), `/api/scraper` (scraper detail).

## Core workflow

### 1. Find the right scraper

Search the Cafe Store by keyword:

```bash
curl -s "https://openapi.cafescraper.com/api/store?search=amazon&limit=5" | jq '.data.scraper[] | {slug, title, description}'
```

Response returns `data.scraper[]` with `slug`, `title`, `description` for each match.

- `search`: search keyword (required, use `""` for all)
- `limit`: max number of results to return (required)

### 2. Get scraper detail and input schema

Before running a scraper, fetch its parameter schema and README:

```bash
curl -s "https://openapi.cafescraper.com/api/scraper?slug=SCRAPER_SLUG" | jq '.data | {version, parameters, readme}'
```

The response includes:
- `data.version` — the current version string (e.g. `"v1.0.2"`). **Use this value when running the scraper.**
- `data.parameters.system` — default system resource settings (cpus, memory_bytes, execute_limit_time_seconds)
- `data.parameters.custom` — scraper-specific input fields. Read `custom.properties[]` to see each field's `name`, `type`, `title`, `editor`, `default`, `required`, and `description`.
- `data.parameters.custom.b` — the primary input field name (e.g. `"startURLs"`)
- `data.readme` — usage documentation for the scraper

### 3. Run a scraper (async)

Start a scraper and get the `run_slug` back immediately. **`version`, `system`, `custom` parameters must all come from Step 2** (scraper detail response):

- `version` → `data.version`
- `system` → use `data.parameters.system` defaults (cpus, memory_bytes, execute_limit_time_seconds, etc.)
- `custom` → read `data.parameters.custom.properties[]` to see each scraper's specific input fields, then fill in accordingly

```bash
curl -s -X POST "https://openapi.cafescraper.com/api/v1/scraper/run" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "scraper_slug": "SCRAPER_SLUG",
    "version": "VERSION_FROM_STEP_2",
    "input": {
      "parameters": {
        "system": {
          "cpus": <from Step 2: data.parameters.system.cpus>,
          "memory": <from Step 2: data.parameters.system.memory_bytes>,
          "execute_limit_time_seconds": <from Step 2: data.parameters.system.execute_limit_time_seconds>,
          "max_total_charge": 0,
          "max_total_traffic": 0
        },
        "custom": {
          <fields from Step 2: data.parameters.custom.properties[]>
        }
      }
    },
    "callback_url": "https://openapi.cafescraper.com/api//v1/test/callback"
  }'
```

Response: `{"code": 0, "message": "success", "data": {"run_slug": "01KKDXV2G26BT7NH4ZQR2R4NPZ"}}`

Save the `run_slug` — you need it for all subsequent operations.

**Important**: `callback_url` is required. Use `"https://openapi.cafescraper.com/api//v1/test/callback"` as a test callback when you don't need a real callback endpoint.

### 4. Poll run status

Check run status until it reaches a terminal state. **Always use the robust polling pattern below** to avoid infinite loops when the API returns unexpected responses:

```bash
CONSECUTIVE_ERRORS=0
while true; do
  RESP=$(curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/detail" \
    -H "api-key: $CAFE_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"run_slug": "RUN_SLUG"}')
  # Sanitize control characters before passing to jq
  RESP_CLEAN=$(echo "$RESP" | tr -d '\000-\011\013-\037')
  STATUS=$(echo "$RESP_CLEAN" | jq -r '.data.status // empty' 2>/dev/null)
  if [ -z "$STATUS" ]; then
    CONSECUTIVE_ERRORS=$((CONSECUTIVE_ERRORS + 1))
    ERR_CODE=$(echo "$RESP_CLEAN" | jq -r '.code // empty' 2>/dev/null)
    echo "$(date +%H:%M:%S) - Parse error or empty status (errors: $CONSECUTIVE_ERRORS, code: $ERR_CODE)"
    if [ "$CONSECUTIVE_ERRORS" -ge 5 ]; then
      echo "ERROR: 5 consecutive failures. Raw response:"
      echo "$RESP" | head -c 500
      break
    fi
    sleep 10
    continue
  fi
  CONSECUTIVE_ERRORS=0
  echo "$(date +%H:%M:%S) - Status: $STATUS"
  case "$STATUS" in
    3) echo "$RESP_CLEAN" | jq '.data | {status, results, duration, usage}'; break;;
    4) echo "$RESP_CLEAN" | jq '.data | {status, err_msg, duration, usage}'; break;;
  esac
  sleep 10
done
```

Status codes:

| Code | State | Terminal? |
|------|-------|-----------|
| 1 | Ready | No |
| 2 | Running | No |
| 3 | Succeeded | Yes |
| 4 | Failed | Yes |
| 5 | Aborting | No |

Response also includes: `scraper_title`, `scraper_slug`, `usage` (cost), `started_at`, `finished_at`, `duration` (seconds), `traffic` (bytes), `version`, `origin` (api/web).

**Polling safeguards:**
- `tr -d '\000-\011\013-\037'` strips control characters that break jq parsing
- `CONSECUTIVE_ERRORS` counter breaks after 5 consecutive parse/API failures,并打印原始响应便于调试
- `jq -r '.data.status // empty' 2>/dev/null` safely handles missing fields

### 5. Get results

There are **two ways** to retrieve results. Choose based on the scenario:

| Scenario | Use | Why |
|----------|-----|-----|
| Preview data, show to user, analyze inline | `result/list` | Returns JSON directly — AI can read and process it |
| User asks to save/download, or data is large | `result/export` | Returns a download URL for CSV/JSON file |

**Option A: Paginated inline data (`result/list`)** — preferred for AI analysis

```bash
curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/result/list" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"run_slug": "RUN_SLUG", "page": 1, "page_size": 20}'
```

Response includes:
- `data.count` — total number of result records
- `data.headers[]` — column definitions with `label`, `key`, `format`
- `data.list[]` — the actual data records (each record also contains a `__cafe_data_id__`)

First call with `page_size: 20` to check `data.count`. If the user needs all data and count is large (>100), switch to export. Otherwise paginate through with `page: 2, 3, ...`.

**Option B: File export (`result/export`)** — preferred for saving to disk

```bash
curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/result/export" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"run_slug": "RUN_SLUG", "format": "csv", "filter_keys": []}'
```

- `format`: `"csv"` or `"json"`
- `filter_keys`: array of field key names to export. Use `[]` for all fields.

Response returns a temporary download URL (valid ~30 min), not raw data:

```json
{"code": 0, "message": "success", "data": {"download_url": "https://..."}}
```

Then download the file:

```bash
DL_URL=$(curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/result/export" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"run_slug": "RUN_SLUG", "format": "csv", "filter_keys": []}' | jq -r '.data.download_url')
curl -L -o results.csv "$DL_URL"
```

### 6. Run a saved task

Tasks are pre-configured scraper runs saved in the Cafe console. Run one by its `task_slug`:

```bash
curl -s -X POST "https://openapi.cafescraper.com/api/v1/task/run" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"task_slug": "TASK_SLUG", "callback_url": "https://openapi.cafescraper.com/api//v1/test/callback"}'
```

Returns a `run_slug` in the response — use it to poll status and fetch results as usual.

### 7. Re-run a previous job

Re-run using the same parameters from a previous run:

```bash
curl -s -X POST "https://openapi.cafescraper.com/api/v1/rerun" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"run_slug": "PREVIOUS_RUN_SLUG", "callback_url": "https://openapi.cafescraper.com/api//v1/test/callback"}'
```

Returns a new `run_slug` for the re-run.

### 8. View run logs

Get logs for a run to debug issues:

```bash
curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/last/log" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"run_slug": "RUN_SLUG"}' | jq '.data.list[] | {type, group, content, timestamp}'
```

Log type codes:

| Code | Level |
|------|-------|
| 1 | Debug |
| 2 | Info |
| 3 | Warn |
| 4 | Error |

Response also includes:
- `data.all_logs_url` — URL to download the full log file
- `data.result_count` — total number of scraped records

### 9. Abort a run

Stop a running scraper:

```bash
curl -s -X POST "https://openapi.cafescraper.com/api/v1/scraper/abort" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"run_slug": "RUN_SLUG"}'
```

### 10. Check account info

Check your balance and traffic usage:

```bash
curl -s -X POST "https://openapi.cafescraper.com/api/v1/account/info" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.data | {balance, traffic, traffic_expiration_at}'
```

Returns:
- `balance` — account balance (string, e.g. `"10122.5547"`)
- `traffic` — traffic used in bytes
- `traffic_expiration_at` — Unix timestamp when traffic expires

## Quick recipes

### Scrape and get results (full async workflow)

```bash
# 1. Search for a scraper
SLUG=$(curl -s "https://openapi.cafescraper.com/api/store?search=amazon&limit=1" \
  | jq -r '.data.scraper[0].slug')

# 2. Get scraper detail — extract version, system defaults, and custom field schema
DETAIL=$(curl -s "https://openapi.cafescraper.com/api/scraper?slug=$SLUG")
VERSION=$(echo "$DETAIL" | jq -r '.data.version')
CPUS=$(echo "$DETAIL" | jq -r '.data.parameters.system.cpus')
MEMORY=$(echo "$DETAIL" | jq -r '.data.parameters.system.memory_bytes')
TIMEOUT=$(echo "$DETAIL" | jq -r '.data.parameters.system.execute_limit_time_seconds')
# Check data.parameters.custom.properties[] for scraper-specific input fields

# 3. Start the run (use values from Step 2, customize "custom" per scraper)
RUN=$(curl -s -X POST "https://openapi.cafescraper.com/api/v1/scraper/run" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "scraper_slug": "'"$SLUG"'",
    "version": "'"$VERSION"'",
    "input": {
      "parameters": {
        "system": {
          "cpus": '"$CPUS"',
          "memory": '"$MEMORY"',
          "execute_limit_time_seconds": '"$TIMEOUT"',
          "max_total_charge": 0,
          "max_total_traffic": 0
        },
        "custom": {
          "startURLs": [{"url": "https://example.com"}],
          "proxy_region": "US"
        }
      }
    },
    "callback_url": "https://openapi.cafescraper.com/api//v1/test/callback"
  }')
RUN_SLUG=$(echo "$RUN" | jq -r '.data.run_slug')
echo "Started run: $RUN_SLUG"

# 4. Poll until done (with safeguards)
CONSECUTIVE_ERRORS=0
while true; do
  RESP=$(curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/detail" \
    -H "api-key: $CAFE_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"run_slug": "'"$RUN_SLUG"'"}')
  RESP_CLEAN=$(echo "$RESP" | tr -d '\000-\011\013-\037')
  STATUS=$(echo "$RESP_CLEAN" | jq -r '.data.status // empty' 2>/dev/null)
  if [ -z "$STATUS" ]; then
    CONSECUTIVE_ERRORS=$((CONSECUTIVE_ERRORS + 1))
    echo "Parse error (errors: $CONSECUTIVE_ERRORS)"
    if [ "$CONSECUTIVE_ERRORS" -ge 5 ]; then echo "Too many errors"; break; fi
    sleep 10; continue
  fi
  CONSECUTIVE_ERRORS=0; echo "Status: $STATUS"
  case "$STATUS" in 3|4) break;; esac
  sleep 5
done

# 5. Check result count
RESULT=$(curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/result/list" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"run_slug": "'"$RUN_SLUG"'", "page": 1, "page_size": 20}')
COUNT=$(echo "$RESULT" | jq '.data.count')
echo "Total results: $COUNT"

# 6a. Small dataset (≤100) — read inline for analysis
echo "$RESULT" | jq '.data.list'

# 6b. Large dataset (>100) — export to file
DL_URL=$(curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/result/export" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"run_slug": "'"$RUN_SLUG"'", "format": "json", "filter_keys": []}' | jq -r '.data.download_url')
curl -L -o results.json "$DL_URL"
```

### Run a saved task

```bash
curl -s -X POST "https://openapi.cafescraper.com/api/v1/task/run" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"task_slug": "TASK_SLUG", "callback_url": "https://openapi.cafescraper.com/api//v1/test/callback"}'
```

### Debug a failed run

```bash
# 1. Check run detail
curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/detail" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"run_slug": "RUN_SLUG"}' | jq '.data | {status, err_msg, duration, usage}'

# 2. Get logs (filter for errors)
curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/last/log" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"run_slug": "RUN_SLUG"}' | jq '.data.list[] | select(.type == 4) | {content, timestamp}'
```

## Run history

List past runs with pagination and optional filters:

```bash
curl -s -X POST "https://openapi.cafescraper.com/api/v1/run/list" \
  -H "api-key: $CAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"page": 1, "page_size": 20, "status": 0, "scraper_slug": ""}'
```

- `status`: `0` = all, `1` = ready, `2` = running, `3` = succeeded, `4` = failed, `5` = aborting
- `scraper_slug`: filter by scraper slug, or `""` for all scrapers

Response: `data.count` (total), `data.list[]` with `slug`, `status`, `scraper_title`, `scraper_slug`, `results`, `usage`, `started_at`, `finished_at`, `duration`, `origin`, `traffic`, `version`.

## Error handling

All responses use a standard envelope: `{"code": <int>, "message": "<string>", "data": <object|null>}`.

`code: 0` means success. Non-zero codes indicate errors:

| Code | Meaning |
|------|---------|
| 4000 | Invalid request parameters |
| 4010 | Unauthorized access / task does not belong to you |
| 4040 | Resource not found |
| 4290 | Rate limited |
| 5000 | Internal server error |
| 10001 | User not found / unavailable |
| 10002 | User disabled |
| 20001 | Invalid API key |
| 20002 | API key expired |
| 30001 | Insufficient balance |
| 30002 | Insufficient traffic |
| 50001 | Script not found |
| 50002 | Script run failed |
| 50003 | Script version unavailable |
| 60001 | Task not found |
| 70001 | Run record does not exist |
| 70002 | Abort run failed |

HTTP status codes:
- **400**: bad request — check required fields and parameter types.
- **401**: `CAFE_API_KEY` is missing, invalid, or expired.
- **404**: scraper, run, or task not found — verify the slug.
- **429**: too many requests — back off and retry.
- **5xx**: server error — retry with backoff.

## System parameter reference

When running a scraper via `/v1/scraper/run`, the `input.parameters.system` object controls resource allocation:

| Parameter | Type | Options / Range | Description |
|-----------|------|-----------------|-------------|
| `cpus` | number | 0.125, 0.25, 0.5, 1.0, 2.0, 4.0 | CPU cores allocated |
| `memory` | integer | 512, 1024, 2048, 4096, 8192, 16384 | Memory in MB |
| `execute_limit_time_seconds` | integer | e.g. 1800 | Timeout in seconds |
| `max_total_charge` | integer | 0 = unlimited | Max cost cap in USD |
| `max_total_traffic` | integer | 0 = unlimited | Max traffic cap in MB |

The `input.parameters.custom` object contains scraper-specific fields. Common fields:
- `startURLs` — array of `{"url": "..."}` objects
- `proxy_region` — ISO 3166-1 alpha-2 country code (e.g. `"US"`, `"GB"`, `"JP"`)

Always fetch the scraper detail first (`GET /api/scraper?slug=...`) to see the exact custom fields, types, and defaults for the specific scraper you want to run.

## Proxy region codes

The `proxy_region` field in `input.parameters.custom` accepts ISO 3166-1 alpha-2 country codes. Common examples: `US`, `GB`, `JP`, `DE`, `FR`, `CN`, `BR`, `IN`, `AU`, `KR`.

## Additional resources

- OpenAPI spec: [openapi.json](openapi.json)
- Cafe Store (browse scrapers): https://cafescraper.com
