"""CSV / Excel review loader with fuzzy column detection.

Lets `review-analyzer` accept user-provided review files (any e-commerce
platform — Amazon, eBay, AliExpress, Shopify) in addition to the built-in
Shulex VOC OpenAPI fetcher for Amazon ASINs.

Credit: column-sniffing + URL-download patterns adapted from
buluslan/review-analyzer-skill (MIT).
"""
from __future__ import annotations

import atexit
import os
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

BODY_KEYS = ("内容", "评价", "正文", "review", "body", "text", "content")
RATING_KEYS = ("星级", "打分", "评分", "rating", "star", "score")
DATE_KEYS = ("时间", "日期", "date", "time")


def download_if_url(src: str, *, max_mb: int = 100) -> str:
    """Local path → local path. URL → tmp download → local path."""
    if not (src.startswith("http://") or src.startswith("https://")):
        return src

    ext = Path(urllib.parse.urlparse(src).path).suffix.lower() or ".csv"
    if ext not in {".csv", ".xls", ".xlsx"}:
        ext = ".csv"
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext, prefix="review_")
    os.close(tmp_fd)
    atexit.register(lambda p=tmp_path: os.path.exists(p) and os.unlink(p))

    req = urllib.request.Request(src, headers={
        "User-Agent": "review-analyzer/1.0 (+https://github.com/mguozhen/voc-amazon-reviews)"
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            cl = resp.headers.get("Content-Length")
            if cl and int(cl) > max_mb * 1024 * 1024:
                raise ValueError(f"file >{max_mb}MB, refusing: {int(cl)/1024/1024:.1f}MB")
            with open(tmp_path, "wb") as f:
                shutil.copyfileobj(resp, f)
    except urllib.error.URLError as e:
        raise ValueError(f"download failed: {e}") from e
    return tmp_path


def _read(path: str):
    """Read CSV/XLSX into a pandas DataFrame, tolerating common encodings."""
    import pandas as pd

    if path.endswith(".csv"):
        for enc in ("utf-8", "utf-8-sig", "gbk", "latin1"):
            try:
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"could not decode CSV: {path}")
    if path.endswith((".xls", ".xlsx")):
        return pd.read_excel(path)
    raise ValueError("only .csv / .xls / .xlsx supported")


def _find(df, keywords):
    for col in df.columns:
        if any(k in str(col).lower() for k in keywords):
            return col
    return None


def load_reviews(src: str) -> dict:
    """Load a CSV/Excel (local path or URL) and return a normalized review array.

    Returns the same `{reviews, meta}` envelope that fetch_reviews uses, so the
    downstream analyze_reviews tool can consume either source uniformly.
    """
    path = download_if_url(src)
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    df = _read(path)
    body_col = _find(df, BODY_KEYS)
    if not body_col:
        raise ValueError(
            f"no review-body column found. Expected one of: {list(BODY_KEYS)}. "
            f"Got columns: {list(df.columns)}"
        )
    rating_col = _find(df, RATING_KEYS)
    date_col = _find(df, DATE_KEYS)

    reviews = []
    dropped = 0
    for _, row in df.iterrows():
        import pandas as pd
        body = str(row[body_col]).strip()
        if pd.isna(row[body_col]) or body.lower() == "nan" or len(body) < 3:
            dropped += 1
            continue
        try:
            rating = float(row[rating_col]) if rating_col and pd.notna(row[rating_col]) else 0.0
        except (TypeError, ValueError):
            rating = 0.0
        date = str(row[date_col]) if date_col and pd.notna(row[date_col]) else ""
        reviews.append({
            "review_id": str(uuid.uuid4())[:12],
            "body": body,
            "rating": rating,
            "date": date,
        })

    return {
        "reviews": reviews,
        "meta": {
            "source": src,
            "columns_detected": {"body": body_col, "rating": rating_col, "date": date_col},
            "rows_in_file": int(len(df)),
            "rows_used": len(reviews),
            "rows_dropped": dropped,
        },
    }
