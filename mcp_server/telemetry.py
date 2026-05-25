"""Lightweight tool-call telemetry for the MCP server.

Design goals:
- Never break user-facing tool calls if telemetry storage fails.
- Redis-first for aggregation; local JSONL fallback for zero-config use.
- No sensitive payload storage (no review text, no API keys, no raw ASIN).
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SERVER_NAME = "voc-amazon-reviews"
DEFAULT_LOG_PATH = "./logs/telemetry.jsonl"


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def enabled() -> bool:
    return _env_flag("TELEMETRY_ENABLED", True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _detect_client() -> str:
    explicit = os.getenv("MCP_CLIENT")
    if explicit:
        return explicit.strip().lower()

    markers = {
        "claude_code": ["CLAUDECODE", "CLAUDE_CODE"],
        "cursor": ["CURSOR_TRACE_ID", "CURSOR_SESSION_ID"],
        "cline": ["CLINE", "CLINE_VERSION"],
        "windsurf": ["WINDSURF", "CODEIUM"],
        "codex": ["CODEX_SANDBOX", "CODEX_ENV"],
    }
    for label, keys in markers.items():
        if any(os.getenv(k) for k in keys):
            return label
    return "unknown"


def detect_client() -> str:
    """Public helper for other telemetry sinks (e.g., OpenTelemetry attrs)."""
    return _detect_client()


def detect_client_instance_id() -> str | None:
    """Stable per-install/client identifier for retention cohorts.

    Expected to be set by the MCP client/integration layer.
    """
    return (
        os.getenv("MCP_CLIENT_INSTANCE_ID")
        or os.getenv("CLIENT_INSTANCE_ID")
        or None
    )


def detect_source_catalog() -> str:
    """Installation/source attribution label."""
    return os.getenv("MCP_SOURCE_CATALOG", "unknown").strip().lower()


def detect_session_id() -> str | None:
    return os.getenv("MCP_SESSION_ID") or None


def _hash_asin(asin: str | None) -> str | None:
    if not asin:
        return None
    salt = os.getenv("TELEMETRY_HASH_SALT", "")
    value = f"{salt}:{asin.strip().upper()}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _jsonl_write(event: dict[str, Any]) -> None:
    path = Path(os.getenv("TELEMETRY_LOG_PATH", DEFAULT_LOG_PATH)).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=True) + "\n")


def _redis_client():
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        import redis  # type: ignore
    except Exception:
        return None
    try:
        return redis.from_url(url, decode_responses=True)
    except Exception:
        return None


def _redis_write(event: dict[str, Any]) -> bool:
    client = _redis_client()
    if client is None:
        return False

    day = _today()
    tool = event.get("tool", "unknown")
    status = event.get("status", "unknown")
    client_name = event.get("client", "unknown")
    latency = int(event.get("latency_ms", 0))
    error_type = event.get("error_type") or "none"
    source_catalog = event.get("source_catalog", "unknown")
    client_instance_id = event.get("client_instance_id")
    business_success = str(bool(event.get("business_success"))).lower()
    cost_usd = event.get("cost_usd")
    event_type = event.get("event_type", "tool_call")

    try:
        pipe = client.pipeline()
        if event_type == "install":
            pipe.incr(f"mcp:voc:install:{day}:{source_catalog}")
        else:
            pipe.incr(f"mcp:voc:calls:{day}:{client_name}:{tool}:{status}")
            pipe.incr(f"mcp:voc:calls_by_source:{day}:{source_catalog}:{tool}:{status}")
            pipe.incr(f"mcp:voc:business_success:{day}:{tool}:{business_success}")
            pipe.lpush(f"mcp:voc:latency:{day}:{client_name}:{tool}", latency)
            pipe.ltrim(f"mcp:voc:latency:{day}:{client_name}:{tool}", 0, 1999)
            if status == "error":
                pipe.incr(f"mcp:voc:errors:{day}:{tool}:{error_type}")
            if cost_usd is not None:
                try:
                    pipe.incrbyfloat(f"mcp:voc:cost_usd:{day}:{tool}", float(cost_usd))
                except Exception:
                    pass
            if client_instance_id:
                # Daily active set for D1/D7/D30 retention.
                pipe.sadd(f"mcp:voc:active:{day}", client_instance_id)
                # First-call funnel marker.
                first_key = f"mcp:voc:first_seen:{client_instance_id}"
                pipe.setnx(first_key, day)
                pipe.expire(first_key, 120 * 24 * 3600)
                pipe.sadd(f"mcp:voc:active_by_source:{day}:{source_catalog}", client_instance_id)
                pipe.sadd(f"mcp:voc:active_by_tool:{day}:{tool}", client_instance_id)
        pipe.xadd("mcp:voc:events", event, maxlen=20000, approximate=True)
        pipe.execute()
        return True
    except Exception:
        return False


def track_tool_call(
    *,
    tool: str,
    status: str,
    latency_ms: int,
    error_type: str | None = None,
    asin: str | None = None,
    market: str | None = None,
    limit: int | None = None,
    business_success: bool | None = None,
    cost_usd: float | None = None,
) -> None:
    """Track one tool call. Exceptions are swallowed by design."""
    if not enabled():
        return

    event: dict[str, Any] = {
        "event_type": "tool_call",
        "ts": _now_iso(),
        "day": _today(),
        "server": os.getenv("TELEMETRY_SERVER_NAME", DEFAULT_SERVER_NAME),
        "host": socket.gethostname(),
        "tool": tool,
        "client": _detect_client(),
        "client_instance_id": detect_client_instance_id(),
        "session_id": detect_session_id(),
        "source_catalog": detect_source_catalog(),
        "status": status,
        "latency_ms": int(latency_ms),
        "error_type": error_type,
        "business_success": business_success,
        "cost_usd": cost_usd,
        "asin_hash": _hash_asin(asin),
        "market": market,
        "limit": limit,
    }

    try:
        written = _redis_write(event)
        if not written:
            _jsonl_write(event)
    except Exception:
        pass


def track_install_event(
    *,
    source_catalog: str | None = None,
    client_instance_id: str | None = None,
) -> None:
    """Optional install-side event for install->first_call funnel."""
    if not enabled():
        return

    event: dict[str, Any] = {
        "event_type": "install",
        "ts": _now_iso(),
        "day": _today(),
        "server": os.getenv("TELEMETRY_SERVER_NAME", DEFAULT_SERVER_NAME),
        "host": socket.gethostname(),
        "source_catalog": (source_catalog or detect_source_catalog()),
        "client_instance_id": client_instance_id or detect_client_instance_id(),
    }
    try:
        written = _redis_write(event)
        if not written:
            _jsonl_write(event)
    except Exception:
        pass
