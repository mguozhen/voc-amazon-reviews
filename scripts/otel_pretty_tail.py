#!/usr/bin/env python3
"""Parse OTel collector debug logs into compact metric summaries."""
from __future__ import annotations

import re
import subprocess
import sys


def main() -> int:
    since = sys.argv[1] if len(sys.argv) > 1 else "30m"
    try:
        res = subprocess.run(
            ["docker", "logs", "--since", since, "otel-collector"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.strip() or "failed to read docker logs", file=sys.stderr)
        return 1

    text = (res.stdout or "") + "\n" + (res.stderr or "")
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if "Name: mcp_tool_calls_total" in line:
            attrs = {"tool": "?", "status": "?", "client": "?", "error_type": "?"}
            value = "?"
            j = i + 1
            while j < len(lines) and "Metric #1" not in lines[j]:
                m = re.search(r"-> (\w+): Str\((.+)\)", lines[j])
                if m and m.group(1) in attrs:
                    attrs[m.group(1)] = m.group(2)
                m = re.search(r"Value:\s+(\d+)", lines[j])
                if m:
                    value = m.group(1)
                j += 1

            lat_count, lat_sum, lat_min, lat_max = "?", "?", "?", "?"
            k = j
            while k < len(lines) and "Metric #0" not in lines[k]:
                m = re.search(r"^Count:\s+(\d+)", lines[k].strip())
                if m and lat_count == "?":
                    lat_count = m.group(1)
                m = re.search(r"Sum:\s+([0-9.]+)", lines[k])
                if m:
                    lat_sum = m.group(1)
                m = re.search(r"Min:\s+([0-9.]+)", lines[k])
                if m:
                    lat_min = m.group(1)
                m = re.search(r"Max:\s+([0-9.]+)", lines[k])
                if m:
                    lat_max = m.group(1)
                k += 1

            print(
                f"tool={attrs['tool']} status={attrs['status']} client={attrs['client']} "
                f"calls={value} latency_count={lat_count} latency_sum_ms={lat_sum} "
                f"min_ms={lat_min} max_ms={lat_max}"
            )
            i = k
            continue
        i += 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
