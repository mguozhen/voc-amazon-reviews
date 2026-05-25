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

    try:
        pipe = client.pipeline()
        pipe.incr(f"mcp:voc:calls:{day}:{client_name}:{tool}:{status}")
        pipe.lpush(f"mcp:voc:latency:{day}:{client_name}:{tool}", latency)
        pipe.ltrim(f"mcp:voc:latency:{day}:{client_name}:{tool}", 0, 1999)
        if status == "error":
            pipe.incr(f"mcp:voc:errors:{day}:{tool}:{error_type}")
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
) -> None:
    """Track one tool call. Exceptions are swallowed by design."""
    if not enabled():
        return

    event: dict[str, Any] = {
        "ts": _now_iso(),
        "day": _today(),
        "server": os.getenv("TELEMETRY_SERVER_NAME", DEFAULT_SERVER_NAME),
        "host": socket.gethostname(),
        "tool": tool,
        "client": _detect_client(),
        "status": status,
        "latency_ms": int(latency_ms),
        "error_type": error_type,
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
