"""Vercel serverless entry point.

Vercel's Python runtime auto-discovers ASGI/WSGI callables named `app`
at module level. FastMCP exposes its streamable-HTTP transport as a
Starlette app via `streamable_http_app()` — we just hand that to Vercel.

All tool registrations live in `mcp_server/server.py`; this file is
deployment plumbing only.

Required env vars (set in Vercel project Settings → Environment Variables):
  - VOC_API_KEY        — Shulex VOC OpenAPI key (required)
  - ANTHROPIC_API_KEY  — only needed for extract_listing_improvements

Note on timeouts: Vercel functions cap at 10s (Hobby), 60s (configured
Hobby via vercel.json), or 300s (Pro). Long-running tools like
`voc_full` and `extract_listing_improvements` may exceed these limits.
For unbounded execution, host with the Dockerfile on Render/Fly/etc.
or install the package locally via `uvx voc-amazon-reviews-mcp`.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Vercel mounts /api/* as functions; make the sibling mcp_server package importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_server.server import mcp  # noqa: E402

app = mcp.streamable_http_app()
