#!/usr/bin/env python3
"""Shared, testable helpers for read-only Feishu snapshot acquisition."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import yaml

VALID_STATUSES = {
    "Complete",
    "Complete with Warnings",
    "Partial",
    "Failed",
    "Permission Required",
    "Unverified",
}
SENSITIVE_KEY = re.compile(
    r"(access[_-]?token|refresh[_-]?token|app[_-]?secret|authorization|cookie|session)",
    re.IGNORECASE,
)
AUTHORIZATION_VALUE = re.compile(
    r"(?i)\b(authorization\s*[=:]\s*)(?:(?:bearer|basic)\s+)?[A-Za-z0-9._~+/=-]+"
)
COOKIE_VALUE = re.compile(r"(?i)\b(cookie\s*[=:]\s*)[^\r\n]+")
TOKEN_VALUE = re.compile(
    r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+|"
    r"((?:access[_-]?token|refresh[_-]?token|app[_-]?secret|session(?:[_-]?(?:id|token))?)\s*[=:]\s*)[^\s,;]+"
)


class FetchError(RuntimeError):
    """Structured source-fetch failure."""

    def __init__(self, message: str, *, status: str = "Failed", method: str = "lark-cli"):
        super().__init__(message)
        self.status = status if status in VALID_STATUSES else "Failed"
        self.method = method


@dataclass
class FetchResult:
    source_id: str
    source_name: str
    source_url: str
    source_type: str
    retrieval_method: str
    retrieval_time: str
    status: str
    document_name: str | None = None
    object_name: str | None = None
    row_count: int | None = None
    column_count: int | None = None
    date_range: str | None = None
    warning: list[str] = field(default_factory=list)
    error: str | None = None
    snapshot_file: list[str] = field(default_factory=list)
    normalized_file: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_manifest_entry(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "retrieval_method": self.retrieval_method,
            "retrieval_time": self.retrieval_time,
            "document_name": self.document_name,
            "table_or_sheet_name": self.object_name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "date_range": self.date_range,
            "status": self.status,
            "warning": self.warning,
            "error": self.error,
            "snapshot_file": self.snapshot_file,
            "normalized_file": self.normalized_file,
            "metadata": self.metadata,
        }


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def safe_name(value: str, default: str = "source") -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value).strip()).strip("-._")
    return name or default


def redact(value: Any) -> Any:
    """Recursively remove credentials from logs and manifest-safe payloads."""
    if isinstance(value, dict):
        return {
            str(key): ("[REDACTED]" if SENSITIVE_KEY.search(str(key)) else redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    if isinstance(value, str):
        value = COOKIE_VALUE.sub(lambda match: match.group(1) + "[REDACTED]", value)
        value = AUTHORIZATION_VALUE.sub(lambda match: match.group(1) + "[REDACTED]", value)
        return TOKEN_VALUE.sub(lambda match: (match.group(1) or match.group(2) or "") + "[REDACTED]", value)
    return value


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(payload), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def relative_to(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def normalize_cell(value: Any) -> Any:
    """Preserve scalars; serialize complex Feishu fields without dropping data."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(redact(value), ensure_ascii=False, sort_keys=True, default=str)


def records_to_csv(records: Iterable[dict[str, Any]], path: Path) -> tuple[int, int]:
    records = list(records)
    rows: list[dict[str, Any]] = []
    columns: list[str] = ["record_id"]
    for record in records:
        fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
        row = {"record_id": record.get("record_id") or record.get("id")}
        for key, value in fields.items():
            if key not in columns:
                columns.append(str(key))
            row[str(key)] = normalize_cell(value)
        rows.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows), len(columns)


def registry_fingerprint(registry: dict[str, Any]) -> str:
    serialized = json.dumps(registry, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registry(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ValueError("Source registry must be a mapping with a sources list")
    if not payload["sources"]:
        raise ValueError("Source registry must contain at least one source")
    project = payload.setdefault("project", {})
    if not isinstance(project, dict):
        raise ValueError("project must be a mapping")
    project.setdefault("market", "Japan")
    project.setdefault("currency", "JPY")
    project.setdefault("timezone", "Asia/Tokyo")
    seen: set[str] = set()
    allowed_source_types = {"auto", "bitable", "sheet", "docx", "wiki", "file", "unknown"}
    for index, source in enumerate(payload["sources"], start=1):
        if not isinstance(source, dict):
            raise ValueError(f"sources[{index}] must be a mapping")
        source.setdefault("id", f"source-{index}")
        source.setdefault("name", source["id"])
        source.setdefault("source_type", "auto")
        source.setdefault("required", True)
        source.setdefault("url", "")
        if not str(source.get("id") or "").strip():
            raise ValueError(f"sources[{index}].id is required")
        if not str(source.get("url") or "").strip():
            raise ValueError(f"sources[{index}].url is required")
        if source["source_type"] not in allowed_source_types:
            raise ValueError(
                f"sources[{index}].source_type must be one of {sorted(allowed_source_types)}"
            )
        if source["id"] in seen:
            raise ValueError(f"Duplicate source id: {source['id']}")
        seen.add(source["id"])
    return payload


CommandRunner = Callable[[list[str], Optional[Path]], dict[str, Any]]


def run_lark_cli(args: list[str], cwd: Path | None = None) -> dict[str, Any]:
    """Run a read-only lark-cli command without a shell or credential logging."""
    command = ["lark-cli", *args]
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )
    if completed.returncode != 0:
        message = redact(completed.stderr.strip() or completed.stdout.strip() or "lark-cli failed")
        lowered = str(message).lower()
        status = (
            "Permission Required"
            if any(term in lowered for term in ("permission", "forbidden", "unauthorized", "auth", "login"))
            else "Failed"
        )
        raise FetchError(str(message), status=status)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise FetchError(f"Invalid JSON from lark-cli: {exc}") from exc
    if isinstance(payload, dict) and payload.get("ok") is False:
        error = payload.get("error") or payload.get("message") or "Feishu request failed"
        raise FetchError(str(redact(error)))
    return payload


def envelope_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data", payload)
    return data if isinstance(data, dict) else {"items": data}


def list_items(data: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def paginated_cli(
    base_args: list[str],
    runner: CommandRunner,
    *,
    cwd: Path | None = None,
    page_size: int = 200,
    item_keys: tuple[str, ...] = ("items", "records"),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Serially exhaust offset or page-token pagination with an audit trail."""
    offset = 0
    page_token: str | None = None
    pages: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    seen_cursors: set[str] = set()
    while True:
        args = [*base_args, "--limit", str(page_size), "--format", "json"]
        if page_token:
            args.extend(["--page-token", page_token])
        elif offset:
            args.extend(["--offset", str(offset)])
        payload = runner(args, cwd)
        data = envelope_data(payload)
        page_items = list_items(data, *item_keys)
        pages.append(redact(payload))
        items.extend(page_items)
        has_more = bool(data.get("has_more") or data.get("hasMore"))
        next_token = data.get("page_token") or data.get("pageToken") or data.get("next_page_token")
        if not has_more and not next_token:
            break
        if next_token:
            cursor = f"token:{next_token}"
            if cursor in seen_cursors:
                raise FetchError("Pagination cursor repeated; completeness cannot be verified", status="Partial")
            seen_cursors.add(cursor)
            # Current lark-cli Base list commands expose offset pagination even
            # when an upstream envelope also reports a page token. Advance by
            # returned records so the next invocation remains CLI-compatible.
            offset += len(page_items)
            page_token = None
        else:
            offset += len(page_items)
            cursor = f"offset:{offset}"
            if not page_items or cursor in seen_cursors:
                raise FetchError("Pagination stopped before completeness was verified", status="Partial")
            seen_cursors.add(cursor)
    return items, pages


def copy_read_only(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite snapshot file: {destination}")
    shutil.copy2(source, destination)
    return destination
