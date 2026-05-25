# MCP Telemetry

This server emits one telemetry event per MCP tool call.

## What is tracked

- `ts`, `day`, `server`, `host`
- `tool`, `client`, `status`, `latency_ms`, `error_type`
- `market`, `limit`
- `asin_hash` (hashed, never raw ASIN)

No review text, API keys, or raw customer payloads are stored.

## Env vars

- `TELEMETRY_ENABLED` (default: `1`)
- `MCP_CLIENT` (optional override, e.g. `cursor`, `claude_code`)
- `TELEMETRY_SERVER_NAME` (default: `voc-amazon-reviews`)
- `TELEMETRY_LOG_PATH` (default: `./logs/telemetry.jsonl`)
- `TELEMETRY_HASH_SALT` (recommended in production)
- `REDIS_URL` (optional; if absent, falls back to JSONL file)

## Storage behavior

1. If `REDIS_URL` is set and Redis is reachable:
   - `INCR mcp:voc:calls:{day}:{client}:{tool}:{status}`
   - `LPUSH mcp:voc:latency:{day}:{client}:{tool} {latency_ms}`
   - `LTRIM mcp:voc:latency:{day}:{client}:{tool} 0 1999`
   - `INCR mcp:voc:errors:{day}:{tool}:{error_type}` (errors only)
   - `XADD mcp:voc:events ... MAXLEN ~ 20000`
2. Otherwise write JSONL to `TELEMETRY_LOG_PATH`.

Telemetry is best-effort and never blocks tool responses.

## OpenTelemetry (optional, parallel sink)

This repo also supports OTel metrics in parallel with Redis/JSONL.

Enable with:

- `OTEL_ENABLED=1`
- `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` (default: `http://localhost:4318/v1/metrics`)
- `OTEL_SERVICE_NAME` (default: `voc-amazon-reviews-mcp`)

Install dependencies:

```bash
pip install "voc-amazon-reviews-mcp[otel]"
```

Emitted metrics:

- `mcp_tool_calls_total` (counter)
- `mcp_tool_latency_ms` (histogram)

Metric attributes:

- `tool`
- `status`
- `client`
- `error_type`

## Quick checks

Daily call count:

```bash
redis-cli KEYS 'mcp:voc:calls:*' | wc -l
```

Top tools today (`YYYY-MM-DD`):

```bash
redis-cli --scan --pattern 'mcp:voc:calls:YYYY-MM-DD:*' | xargs -I {} sh -c 'echo -n "{} "; redis-cli GET "{}"'
```

Tail local fallback logs:

```bash
tail -n 50 logs/telemetry.jsonl
```
