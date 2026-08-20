#!/usr/bin/env python3
"""Parse Feishu/Lark URLs into stable source coordinates."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

SUPPORTED_PATH_TYPES = {
    "base": "bitable",
    "sheets": "sheet",
    "spreadsheets": "sheet",
    "docx": "docx",
    "wiki": "wiki",
}
URL_PATTERN = re.compile(r"https?://[^\s<>()\]\"']+")


def parse_feishu_url(url: str) -> dict[str, Any]:
    """Return a non-secret, standardized description of a Feishu URL."""
    original = str(url).strip()
    parsed = urlparse(original)
    parts = [part for part in parsed.path.split("/") if part]
    source_type = "unknown"
    token = None
    route = None
    for index, part in enumerate(parts):
        if part in SUPPORTED_PATH_TYPES and index + 1 < len(parts):
            route = part
            source_type = SUPPORTED_PATH_TYPES[part]
            token = parts[index + 1]
            break
    query = parse_qs(parsed.query)
    return {
        "original_url": original,
        "source_type": source_type,
        "route": route,
        "token": token,
        "table_id": (query.get("table") or [None])[0],
        "view_id": (query.get("view") or [None])[0],
        "sheet_id": (query.get("sheet") or [None])[0],
        "recognized": source_type != "unknown",
    }


def extract_feishu_urls(text: str) -> list[dict[str, Any]]:
    """Extract and de-duplicate supported and unsupported Feishu-like URLs."""
    seen: set[str] = set()
    parsed: list[dict[str, Any]] = []
    for match in URL_PATTERN.findall(text):
        url = match.rstrip(".,;:，。；：")
        host = (urlparse(url).hostname or "").lower()
        if not any(domain in host for domain in ("feishu.cn", "larksuite.com", "larkoffice.com")):
            continue
        if url not in seen:
            seen.add(url)
            parsed.append(parse_feishu_url(url))
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="+", help="Feishu/Lark URL to parse")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = [parse_feishu_url(url) for url in args.url]
    print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
