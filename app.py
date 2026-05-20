"""Vercel ASGI entrypoint.

Vercel's Python runtime auto-discovers an `app` callable in a root-level
file named `app.py`, `index.py`, `server.py`, etc. FastMCP exposes its
streamable-HTTP transport as a Starlette app via `streamable_http_app()`;
we hand that callable to Vercel.

All tool registrations live in `mcp_server/server.py`. This file is
deployment plumbing only.

Required env vars (set in Vercel project Settings → Environment Variables):
  - VOC_API_KEY        — Shulex VOC OpenAPI key (required)
  - ANTHROPIC_API_KEY  — only needed for extract_listing_improvements

Note on timeouts: Vercel functions cap at 10s (Hobby default), 60s
(Hobby with maxDuration), or 300s (Pro). Long-running tools like
`voc_full` and `extract_listing_improvements` may exceed these limits.
For unbounded execution, host with the Dockerfile on Render/Fly/etc.
or install the package locally via `uvx voc-amazon-reviews-mcp`.
"""
from mcp_server.server import mcp

app = mcp.streamable_http_app()
