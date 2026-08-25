#!/usr/bin/env python3
"""Build a proposal-only Product Truth review package in a private runtime.

The runner intentionally does not call Feishu or write Product Knowledge. A
Feishu MCP response is a private-runtime input supplied by the orchestrator.
Local fallback is accepted only when the request contains an explicit human
confirmation. All claims remain unapproved and the flow stops for review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


FLOW_VERSION = "0.1.0-p0.1"
TERMINAL_GATE = "PRODUCT_TRUTH_HUMAN_REVIEW_GATE"
ALLOWED_FINAL_STATES = {
    "P0_1_READY_FOR_REVIEW",
    "P0_1_PARTIAL",
    "P0_1_BLOCKED",
}
OUTPUT_NAMES = {
    "source_snapshot": "source-snapshot.json",
    "product_knowledge_change_proposal": "product-knowledge-change-proposal.json",
    "product_truth_proposal": "product-truth-proposal.json",
    "conflict_missing_report": "conflict-missing-report.json",
    "claim_human_review_queue": "claim-human-review-queue.json",
    "product_truth_review_html": "product-truth-review.html",
}
DISALLOWED_OUTPUT_TOKENS = (
    "storyline",
    "gallery",
    "pdp-final",
    "final-pdp",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
)
CANONICAL_SOURCE_ID = re.compile(r"SRC-\d{3}")
FACT_SECTIONS = {
    "sku_offers",
    "specifications",
    "compatibility",
    "installation",
    "pricing",
    "bundles",
}
FACT_STATUS_MAP = {
    "confirmed": "CONFIRMED",
    "working": "CONDITIONAL",
    "conditional": "CONDITIONAL",
    "conflicted": "CONFLICT",
    "conflict": "CONFLICT",
    "missing": "MISSING",
    "prohibited": "PROHIBITED",
    "unverified": "UNKNOWN",
    "unknown": "UNKNOWN",
}
CLAIM_STATUS_MAP = {
    "conditional": "PENDING",
    "pending verification": "PENDING",
    "pending": "PENDING",
    "conflicted": "CONFLICT",
    "conflict": "CONFLICT",
    "prohibited": "PROHIBITED",
    "unverified": "UNKNOWN",
    "unknown": "UNKNOWN",
}


class FlowError(RuntimeError):
    """A fail-closed flow error suitable for a blocked manifest."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FlowError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FlowError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)


def required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FlowError(f"{label} must be a non-empty string")
    return value.strip()


def optional_string(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return required_string(value, label)


def ensure_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise FlowError(f"{label} must be a list")
    return value


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def assert_private_runtime(runtime_dir: Path, repo_root: Path) -> None:
    runtime = runtime_dir.resolve()
    root = repo_root.resolve()
    if is_relative_to(runtime, root):
        raise FlowError("private runtime must be outside the Git repository")
    for ancestor in (runtime, *runtime.parents):
        if (ancestor / ".git").exists():
            raise FlowError("private runtime must not be inside any Git repository")
    protected_skill_roots = [
        Path.home() / ".codex" / "skills",
        Path.home() / ".agents" / "skills",
    ]
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        protected_skill_roots.append(Path(codex_home).expanduser().resolve() / "skills")
    if any(is_relative_to(runtime, path.resolve()) for path in protected_skill_roots):
        raise FlowError("private runtime must not be an installed Skill or canonical knowledge path")


def assert_runtime_input(path: Path, runtime_dir: Path, label: str) -> None:
    resolved = path.expanduser().resolve()
    inputs_dir = (runtime_dir / "inputs").resolve()
    if not is_relative_to(resolved, inputs_dir):
        raise FlowError(f"{label} must be frozen under the run's private inputs directory")
    if not resolved.is_file():
        raise FlowError(f"{label} does not exist: {resolved}")


def secure_runtime(runtime_dir: Path, request_path: Path, input_paths: Iterable[Path]) -> None:
    runtime_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    runtime_dir.chmod(0o700)
    inputs_dir = runtime_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    inputs_dir.chmod(0o700)
    if request_path.is_file() and is_relative_to(request_path, runtime_dir):
        request_path.chmod(0o600)
    for path in input_paths:
        path.chmod(0o600)


def git_provenance(repo_root: Path) -> tuple[str, bool]:
    try:
        commit = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=normal"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise FlowError(f"cannot capture workspace Git provenance: {exc}") from exc
    return commit, bool(status)


def parse_upstream_refs(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        candidates = value
    elif isinstance(value, str):
        candidates = CANONICAL_SOURCE_ID.findall(value)
    else:
        raise FlowError("upstream source refs must be a list or source-id string")
    refs = []
    for candidate in candidates:
        candidate = required_string(candidate, "upstream source ref")
        if not CANONICAL_SOURCE_ID.fullmatch(candidate):
            raise FlowError(f"invalid canonical upstream source id: {candidate}")
        if candidate not in refs:
            refs.append(candidate)
    return refs


def validate_payload_shape(path: Path, raw_type: str) -> None:
    if raw_type in {"local_file", "derived_artifact"}:
        if path.stat().st_size == 0:
            raise FlowError(f"empty source file: {path}")
        return
    payload = load_json(path)
    candidate = payload.get("result") if isinstance(payload.get("result"), dict) else payload
    if raw_type == "feishu_sheet_export":
        required = {"annotated_csv", "actual_range", "revision"}
        if not required.issubset(candidate) or not isinstance(candidate.get("annotated_csv"), str):
            raise FlowError(f"invalid annotated Feishu Sheet export shape: {path}")
        return
    if raw_type == "manual_snapshot":
        return
    resource_type = candidate.get("resource_type")
    content = candidate.get("content")
    if raw_type == "docx":
        if resource_type != "docx" or not isinstance(content, (str, dict)):
            raise FlowError(f"invalid Feishu Docx connector payload: {path}")
        return
    if raw_type == "sheets":
        if resource_type != "sheets" or not isinstance(content, dict):
            raise FlowError(f"invalid Feishu Sheet connector payload: {path}")
        sheets = content.get("sheets")
        if not isinstance(sheets, list) or not sheets:
            raise FlowError(f"Feishu Sheet connector payload has no sheets: {path}")
        if any(not isinstance(sheet, dict) or not isinstance(sheet.get("values"), list) for sheet in sheets):
            raise FlowError(f"Feishu Sheet connector payload lost two-dimensional values: {path}")
        return
    if raw_type == "bitable":
        if resource_type != "bitable" or not isinstance(content, dict):
            raise FlowError(f"invalid Feishu Bitable connector payload: {path}")
        return
    raise FlowError(f"unsupported payload shape validation for {raw_type}")


def validate_json(value: Any, schema_path: Path, label: str) -> None:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    if errors:
        lines = []
        for error in errors[:20]:
            where = ".".join(str(part) for part in error.absolute_path) or "<root>"
            lines.append(f"{where}: {error.message}")
        raise FlowError(f"{label} validation failed: " + " | ".join(lines))


def resolve_schema_owner(
    repo_root: Path,
    reference: dict[str, Any],
    explicit_schema: Path | None,
) -> tuple[Path, Path, str]:
    schema_meta = reference["schema"]
    owner_meta = reference["ownership"]
    relative = Path(schema_meta["path"])
    candidates: list[tuple[Path, Path]] = []
    if explicit_schema is not None:
        resolved = explicit_schema.resolve()
        candidates.append((resolved.parents[len(relative.parts) - 1], resolved))
    env_root = os.environ.get("JP_COMMERCE_CREATIVE_FLOW_DIR")
    if env_root:
        owner = Path(env_root).expanduser().resolve()
        candidates.append((owner, owner / relative))
    for parent in [repo_root, *repo_root.parents]:
        owner = parent / "jp-commerce-creative-flow"
        candidates.append((owner, owner / relative))

    seen: set[Path] = set()
    for owner_root, schema_path in candidates:
        schema_path = schema_path.resolve()
        if schema_path in seen or not schema_path.is_file():
            continue
        seen.add(schema_path)
        actual_sha = sha256_file(schema_path)
        if actual_sha != schema_meta["sha256"]:
            raise FlowError(
                f"Product Truth schema SHA mismatch: {actual_sha} != {schema_meta['sha256']}"
            )
        schema = load_json(schema_path)
        if schema.get("$id") != schema_meta["$id"]:
            raise FlowError("Product Truth schema $id does not match locked reference")
        if schema.get("$schema") != schema_meta["$schema"]:
            raise FlowError("Product Truth schema dialect does not match locked reference")
        if schema.get("properties", {}).get("schema_version", {}).get("const") != "1.0":
            raise FlowError("Product Truth logical schema version is not 1.0")
        try:
            commit = subprocess.run(
                ["git", "-C", str(owner_root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise FlowError(f"cannot verify Product Truth owner repository: {exc}") from exc
        if commit != owner_meta["locked_commit"]:
            raise FlowError(
                f"Product Truth owner commit mismatch: {commit} != {owner_meta['locked_commit']}"
            )
        return owner_root, schema_path, commit
    raise FlowError("locked Product Truth schema could not be resolved")


def read_csv_index(path: Path, key: str) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise FlowError(f"cannot read CSV {path}: {exc}") from exc
    if not rows or key not in rows[0]:
        raise FlowError(f"CSV {path} is empty or missing {key}")
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        item_id = row.get(key, "").strip()
        if not item_id:
            raise FlowError(f"CSV {path} contains a blank {key}")
        if item_id in indexed:
            raise FlowError(f"CSV {path} contains duplicate {key}: {item_id}")
        indexed[item_id] = row
    return rows, indexed


def normalize_source(
    raw: dict[str, Any],
    captured_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_id = required_string(raw.get("source_id"), "source.source_id")
    path = Path(required_string(raw.get("path"), f"source {source_id}.path")).expanduser().resolve()
    if not path.is_file():
        raise FlowError(f"source file does not exist: {path}")
    actual_sha = sha256_file(path)
    expected_sha = raw.get("expected_sha256")
    if expected_sha and actual_sha != expected_sha:
        raise FlowError(f"source hash mismatch for {source_id}: {actual_sha} != {expected_sha}")
    raw_type = required_string(raw.get("raw_resource_type"), f"source {source_id}.raw_resource_type")
    validate_payload_shape(path, raw_type)
    normalized_type = required_string(
        raw.get("normalized_source_type"), f"source {source_id}.normalized_source_type"
    )
    mapping_rule = required_string(raw.get("mapping_rule"), f"source {source_id}.mapping_rule")
    payload_shape = required_string(raw.get("payload_shape"), f"source {source_id}.payload_shape")
    extraction_status = required_string(
        raw.get("extraction_status", "READ_SUCCESS"), f"source {source_id}.extraction_status"
    )
    snapshot_source = {
        "source_id": source_id,
        "title": required_string(raw.get("title"), f"source {source_id}.title"),
        "authority": required_string(raw.get("authority"), f"source {source_id}.authority"),
        "original_uri": optional_string(raw.get("original_uri"), f"source {source_id}.original_uri"),
        "source_revision": optional_string(raw.get("source_revision"), f"source {source_id}.source_revision"),
        "source_updated_at": optional_string(
            raw.get("source_updated_at"), f"source {source_id}.source_updated_at"
        ),
        "captured_at": captured_at,
        "extraction_status": extraction_status,
        "content_sha256": actual_sha,
        "content_ref": str(path),
        "allowed_use": required_string(raw.get("allowed_use"), f"source {source_id}.allowed_use"),
        "derived_from": parse_upstream_refs(raw.get("derived_from", [])),
        "adapter_mapping": {
            "raw_resource_type": raw_type,
            "normalized_source_type": normalized_type,
            "mapping_rule": mapping_rule,
            "payload_shape": payload_shape,
            "payload_ref": str(path),
        },
    }
    product_truth_source = {
        "id": source_id,
        "source_type": normalized_type,
        "title": snapshot_source["title"],
        "original_url": snapshot_source["original_uri"],
        "token": optional_string(raw.get("token"), f"source {source_id}.token"),
        "updated_at": snapshot_source["source_updated_at"],
        "retrieved_at": captured_at,
        "content_sha256": actual_sha,
        "status": required_string(raw.get("packet_source_status", "PARTIAL"), f"source {source_id}.packet_source_status"),
    }
    return snapshot_source, product_truth_source


def as_datetime(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value + "T00:00:00+08:00"
    return value


def pointer_source(
    row: dict[str, str],
    source_index_path: Path,
    captured_at: str,
) -> dict[str, Any]:
    source_id = required_string(row.get("Source_ID"), "source index Source_ID")
    raw_kind = (row.get("Type") or "").strip().lower()
    if "sheet" in raw_kind:
        normalized = "feishu_sheet"
    elif "docx" in raw_kind or "wiki" in raw_kind:
        normalized = "feishu_docx"
    elif "base" in raw_kind or "bitable" in raw_kind:
        normalized = "feishu_bitable"
    elif "folder" in raw_kind or "drive" in raw_kind:
        normalized = "feishu_drive"
    else:
        normalized = "human_decision"
    return {
        "source_id": source_id,
        "title": required_string(row.get("Title"), f"source pointer {source_id}.title"),
        "authority": "CANONICAL_SOURCE",
        "original_uri": optional_string(row.get("URL") or None, f"source pointer {source_id}.URL"),
        "source_revision": optional_string(
            (f"updated:{row.get('Updated_At')}" if row.get("Updated_At") else None),
            f"source pointer {source_id}.revision",
        ),
        "source_updated_at": as_datetime(row.get("Updated_At")),
        "captured_at": captured_at,
        "extraction_status": "NOT_EXTRACTED",
        "content_sha256": None,
        "content_ref": None,
        "allowed_use": "BLOCKED",
        "derived_from": [],
        "adapter_mapping": {
            "raw_resource_type": "source_pointer",
            "normalized_source_type": normalized,
            "mapping_rule": "pointer_only_no_content",
            "payload_shape": "no_payload",
            "payload_ref": f"{source_index_path}#{source_id}",
        },
    }


def validate_snapshot_lineage(sources: list[dict[str, Any]]) -> None:
    source_ids = [source["source_id"] for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise FlowError("Source Snapshot contains duplicate source IDs")
    known = set(source_ids)
    for source in sources:
        derived = source.get("derived_from", [])
        missing = sorted(set(derived) - known)
        if missing:
            raise FlowError(
                f"source {source['source_id']} has unregistered upstream lineage: {', '.join(missing)}"
            )
        if source["source_id"] in derived:
            raise FlowError(f"source {source['source_id']} cannot derive from itself")


def canonical_revision_map(sources: list[dict[str, Any]]) -> dict[str, str]:
    revisions: dict[str, str] = {}
    for source in sources:
        source_id = source["source_id"]
        revision = source.get("source_revision")
        if CANONICAL_SOURCE_ID.fullmatch(source_id) and revision:
            revisions[source_id] = revision
    for source in sources:
        mapping = source["adapter_mapping"]
        if mapping["raw_resource_type"] not in {"docx", "sheets", "bitable", "feishu_sheet_export"}:
            continue
        revision = source.get("source_revision")
        if not revision:
            continue
        for upstream_id in source.get("derived_from", []):
            revisions[upstream_id] = revision
    return revisions


def check_request(request: dict[str, Any]) -> None:
    if request.get("request_version") != "1.0":
        raise FlowError("request_version must be 1.0")
    required_string(request.get("run_id"), "run_id")
    required_string(request.get("generated_at"), "generated_at")
    scope = request.get("scope")
    if not isinstance(scope, dict):
        raise FlowError("scope must be an object")
    expected = {
        "project_id": "s30-mini",
        "market": "JP",
        "locale": "ja-JP",
        "channel": "Amazon.co.jp",
        "offer": "水箱版のみ",
    }
    for field, value in expected.items():
        if scope.get(field) != value:
            raise FlowError(f"P0-1 pilot scope requires {field}={value}")
    required_string(scope.get("product_id"), "scope.product_id")
    acquisition = request.get("acquisition")
    if not isinstance(acquisition, dict):
        raise FlowError("acquisition must be an object")
    requested = acquisition.get("requested_adapter")
    if requested not in {"FEISHU_MCP", "LOCAL_FILE", "MANUAL_SNAPSHOT"}:
        raise FlowError("unsupported requested_adapter")
    status = acquisition.get("adapter_status")
    if status not in {"SUCCESS", "PARTIAL", "BLOCKED", "NOT_ATTEMPTED"}:
        raise FlowError("unsupported acquisition.adapter_status")
    fallback = acquisition.get("fallback_confirmation")
    input_confirmation = acquisition.get("input_confirmation")
    effective = acquisition.get("effective_adapter")
    if status == "BLOCKED" and effective is None:
        return
    if status == "BLOCKED":
        if effective not in {"LOCAL_FILE", "MANUAL_SNAPSHOT"}:
            raise FlowError("blocked primary adapter requires a supported fallback")
        if not isinstance(fallback, dict) or fallback.get("confirmed") is not True:
            raise FlowError("fallback requires explicit human confirmation")
        for field in ("confirmed_by", "confirmed_at", "reason"):
            required_string(fallback.get(field), f"fallback_confirmation.{field}")
    elif effective != requested:
        raise FlowError("effective_adapter must equal requested_adapter when the primary adapter succeeds")
    if effective in {"LOCAL_FILE", "MANUAL_SNAPSHOT"}:
        if not isinstance(input_confirmation, dict) or input_confirmation.get("confirmed") is not True:
            raise FlowError(f"{effective} input requires explicit human confirmation")
        for field in ("confirmed_by", "confirmed_at", "reason"):
            required_string(input_confirmation.get(field), f"input_confirmation.{field}")
    elif input_confirmation is not None:
        raise FlowError("FEISHU_MCP input must not carry a human input confirmation")

    entities = request.get("entity_registry")
    if not isinstance(entities, dict):
        raise FlowError("entity_registry must be an object")
    for field in ("product_id", "tank_dock_product_id", "offer_id"):
        required_string(entities.get(field), f"entity_registry.{field}")
    if entities["product_id"] != scope["product_id"]:
        raise FlowError("entity_registry.product_id must equal scope.product_id")
    source_priorities = request.get("product_knowledge_source_priorities")
    if not isinstance(source_priorities, dict) or not source_priorities:
        raise FlowError("product_knowledge_source_priorities must be a non-empty object")
    for source_id, priority in source_priorities.items():
        if not CANONICAL_SOURCE_ID.fullmatch(str(source_id)):
            raise FlowError(f"invalid Product Knowledge priority source ID: {source_id}")
        if priority not in {"P1", "P2", "P3", "P4", "P5"}:
            raise FlowError(f"invalid Product Knowledge source priority for {source_id}: {priority}")


def validate_adapter_policy(request: dict[str, Any], sources: list[dict[str, Any]]) -> None:
    effective = request["acquisition"].get("effective_adapter")
    if not sources:
        raise FlowError("at least one immediate source is required")
    primary_sources = 0
    for raw in sources:
        raw_type = raw.get("raw_resource_type")
        normalized = raw.get("normalized_source_type")
        authority = raw.get("authority")
        packet_status = raw.get("packet_source_status", "PARTIAL")
        is_derivative = raw_type == "derived_artifact"
        if is_derivative:
            if not (
                normalized == "product_knowledge"
                and authority == "DERIVED_ARTIFACT"
                and packet_status == "PARTIAL"
            ):
                raise FlowError(
                    "derived artifacts must remain PARTIAL Product Knowledge derivatives"
                )
            continue
        primary_sources += 1
        if effective == "FEISHU_MCP":
            if raw_type not in {"docx", "sheets", "bitable"}:
                raise FlowError("FEISHU_MCP success requires an actual connector payload")
            if authority != "CANONICAL_SOURCE" or normalized not in {
                "feishu_docx",
                "feishu_sheet",
                "feishu_bitable",
            }:
                raise FlowError("FEISHU_MCP source authority or normalized type is invalid")
            if packet_status not in {"VERIFIED_READ", "PARTIAL"}:
                raise FlowError("FEISHU_MCP source status is invalid")
        elif effective == "MANUAL_SNAPSHOT":
            if not (
                raw_type == "manual_snapshot"
                and normalized == "human_decision"
                and authority == "USER_PROVIDED"
                and packet_status == "PARTIAL"
            ):
                raise FlowError("MANUAL_SNAPSHOT cannot impersonate a Feishu or verified canonical source")
        elif effective == "LOCAL_FILE":
            if raw_type not in {"feishu_sheet_export", "local_file"}:
                raise FlowError("LOCAL_FILE source requires an honest local export or official-file mapping")
            if authority not in {"CONFIRMED_FALLBACK", "CONFIRMED_LOCAL_INPUT"}:
                raise FlowError("LOCAL_FILE source must be explicitly confirmed")
            if packet_status != "PARTIAL":
                raise FlowError("LOCAL_FILE source cannot claim VERIFIED_READ in this run")
        else:
            raise FlowError("no effective source adapter is available")
    if primary_sources == 0:
        raise FlowError(f"{effective} requires at least one non-derived primary input")


def acquisition_is_blocked(request: dict[str, Any]) -> bool:
    acquisition = request["acquisition"]
    return acquisition["adapter_status"] == "BLOCKED" and acquisition.get("effective_adapter") is None


def build_source_snapshot(
    request: dict[str, Any],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    acquisition = request["acquisition"]
    fallback_used = (
        acquisition.get("adapter_status") == "BLOCKED"
        and acquisition.get("effective_adapter") in {"LOCAL_FILE", "MANUAL_SNAPSHOT"}
    )
    status = "BLOCKED" if acquisition_is_blocked(request) else (
        "PARTIAL" if fallback_used or acquisition.get("adapter_status") == "PARTIAL" else "COMPLETE"
    )
    error_items = []
    if acquisition.get("adapter_status") == "BLOCKED":
        error_items.append(
            {
                "code": required_string(acquisition.get("blocked_code", "SOURCE_ACCESS_BLOCKED"), "blocked_code"),
                "message": required_string(acquisition.get("blocked_reason"), "blocked_reason"),
                "source_id": None,
            }
        )
    return {
        "contract_version": "1.0",
        "snapshot_id": f"SNAP-{request['run_id']}",
        "run_id": request["run_id"],
        "project_id": request["scope"]["project_id"],
        "product_id": request["scope"]["product_id"],
        "captured_at": request["generated_at"],
        "scope": {
            "market": request["scope"]["market"],
            "locale": request["scope"]["locale"],
            "channel": request["scope"]["channel"],
            "offer": request["scope"]["offer"],
        },
        "acquisition": {
            "requested_adapter": acquisition["requested_adapter"],
            "adapter_status": acquisition["adapter_status"],
            "adapter_attempted_at": acquisition.get("attempted_at"),
            "blocked_reason": acquisition.get("blocked_reason"),
            "effective_adapter": acquisition.get("effective_adapter"),
            "input_confirmation": acquisition.get("input_confirmation"),
            "fallback_used": fallback_used,
            "fallback_confirmation": acquisition.get("fallback_confirmation") if fallback_used else None,
        },
        "storage_policy": {
            "runtime_outside_git_repository": True,
            "raw_feishu_body_committed": False,
            "prices_committed": False,
            "approval_records_committed": False,
            "unreleased_assets_committed": False,
        },
        "sources": sources,
        "status": status,
        "errors": error_items,
    }


def fact_status(raw: str, override: str | None = None) -> str:
    if override:
        status = override.upper()
        if status not in set(FACT_STATUS_MAP.values()):
            raise FlowError(f"invalid fact status override: {override}")
        return status
    value = FACT_STATUS_MAP.get(raw.strip().lower())
    if value is None:
        raise FlowError(f"cannot map fact status: {raw}")
    return value


def claim_status(raw: str, override: str | None = None) -> str:
    if override:
        status = override.upper()
        if status not in {"PENDING", "CONFLICT", "PROHIBITED", "UNKNOWN"}:
            raise FlowError(f"invalid claim status override: {override}")
        return status
    value = CLAIM_STATUS_MAP.get(raw.strip().lower())
    if value is None:
        raise FlowError(f"cannot map claim status: {raw}")
    return value


def make_fact_item(mapping: dict[str, Any], row: dict[str, str] | None) -> dict[str, Any]:
    fact_id = required_string(mapping.get("fact_id"), "fact mapping.fact_id")
    if row is None and "value" not in mapping:
        raise FlowError(f"inline fact {fact_id} requires value")
    label = mapping.get("label") or (row or {}).get("Field")
    value: Any = mapping["value"] if "value" in mapping else (row or {}).get("Value")
    unit = mapping.get("unit") if "unit" in mapping else (row or {}).get("Unit")
    if value is not None and unit and not mapping.get("value_includes_unit", False):
        value = f"{value} {unit}".strip()
    source_refs = [required_string(item, f"{fact_id}.source_refs") for item in ensure_list(mapping.get("source_refs"), f"{fact_id}.source_refs")]
    if not source_refs:
        raise FlowError(f"fact {fact_id} requires at least one source_ref")
    raw_status = mapping.get("raw_status") or (row or {}).get("Status") or "Unverified"
    item = {
        "id": fact_id,
        "label": required_string(label, f"{fact_id}.label"),
        "value": value,
        "status": fact_status(raw_status, mapping.get("status")),
        "scope": required_string(mapping.get("scope", "水箱版のみ"), f"{fact_id}.scope"),
        "conditions": [
            required_string(item, f"{fact_id}.conditions")
            for item in ensure_list(mapping.get("conditions", []), f"{fact_id}.conditions")
        ],
        "source_refs": source_refs,
    }
    return item


def make_pk_fact(
    item: dict[str, Any],
    mapping: dict[str, Any],
    row: dict[str, str] | None,
    section: str,
    canonical_source_revisions: dict[str, str],
    canonical_source_priorities: dict[str, str],
) -> dict[str, Any]:
    evidence = mapping.get("evidence_location") or (row or {}).get("Evidence_Location")
    upstream_refs = parse_upstream_refs((row or {}).get("Source_ID"))
    for ref in parse_upstream_refs(mapping.get("upstream_source_refs", [])):
        if ref not in upstream_refs:
            upstream_refs.append(ref)
    if not upstream_refs:
        raise FlowError(f"{item['id']} requires canonical upstream source lineage")
    source_revision = mapping.get("source_revision") or canonical_source_revisions.get(
        upstream_refs[0]
    )
    if not source_revision:
        raise FlowError(
            f"{item['id']} requires the canonical source revision; a derivative CSV version is insufficient"
        )
    source_priority = mapping.get("source_priority") or canonical_source_priorities.get(
        upstream_refs[0]
    )
    if source_priority not in {"P1", "P2", "P3", "P4", "P5"}:
        raise FlowError(f"{item['id']} requires a Product Knowledge P1-P5 source priority")
    source_market = mapping.get("source_market") or (row or {}).get("Market") or "Unknown"
    applicability = mapping.get("market_applicability") or (
        "jp_applicable_pending_review" if source_market == "JP" else "needs_jp_verification"
    )
    if applicability not in {"jp_applicable_pending_review", "needs_jp_verification"}:
        raise FlowError(f"invalid market applicability for {item['id']}")
    if source_market != "JP" and item["status"] == "CONFIRMED":
        raise FlowError(f"Global/non-JP fact {item['id']} cannot be silently confirmed for JP")
    return {
        "proposal_fact_id": item["id"],
        "source_id": upstream_refs[0],
        "source_revision_id": required_string(source_revision, f"{item['id']}.source_revision_id"),
        "product_id": required_string(mapping.get("subject_product_id"), f"{item['id']}.subject_product_id"),
        "information_type": section,
        "field": item["label"],
        "value": item["value"],
        "conditions": " | ".join(item["conditions"]) or None,
        "condition_items": item["conditions"],
        "market": "JP",
        "source_market": required_string(source_market, f"{item['id']}.source_market"),
        "market_applicability": applicability,
        "source_priority": source_priority,
        "proposed_review_status": "pending_verification",
        "subject_product_id": required_string(
            mapping.get("subject_product_id"), f"{item['id']}.subject_product_id"
        ),
        "capability_owner_product_id": required_string(
            mapping.get("capability_owner_product_id"),
            f"{item['id']}.capability_owner_product_id",
        ),
        "required_product_id": optional_string(
            mapping.get("required_product_id"), f"{item['id']}.required_product_id"
        ),
        "entity_scope": required_string(mapping.get("entity_scope"), f"{item['id']}.entity_scope"),
        "offer_scope": item["scope"],
        "immediate_source_id": item["source_refs"][0],
        "immediate_source_refs": item["source_refs"],
        "upstream_source_refs": upstream_refs,
        "transformation_note": "Immediate snapshot/derivative preserves the registered canonical upstream lineage.",
        "evidence_location": required_string(evidence, f"{item['id']}.evidence_location"),
        "packet_status": item["status"],
    }


def validate_fact_ownership(
    mapping: dict[str, Any],
    entities: dict[str, str],
    fact_id: str,
) -> None:
    entity_scope = required_string(mapping.get("entity_scope"), f"{fact_id}.entity_scope")
    subject = required_string(mapping.get("subject_product_id"), f"{fact_id}.subject_product_id")
    owner = required_string(
        mapping.get("capability_owner_product_id"),
        f"{fact_id}.capability_owner_product_id",
    )
    required_product = optional_string(
        mapping.get("required_product_id"), f"{fact_id}.required_product_id"
    )
    product_id = entities["product_id"]
    tank_dock_id = entities["tank_dock_product_id"]
    offer_id = entities["offer_id"]
    if entity_scope == "PRODUCT":
        expected = (product_id, product_id, None)
        actual = (subject, owner, required_product)
        if actual != expected:
            raise FlowError(
                f"{fact_id} PRODUCT ownership must be subject={product_id}, owner={product_id}, required=null"
            )
    elif entity_scope == "TANK_DOCK":
        expected = (tank_dock_id, tank_dock_id, product_id)
        actual = (subject, owner, required_product)
        if actual != expected:
            raise FlowError(
                f"{fact_id} TANK_DOCK ownership must be subject/owner={tank_dock_id} and require {product_id}"
            )
    elif entity_scope == "OFFER":
        if subject != offer_id or owner not in {product_id, tank_dock_id, offer_id}:
            raise FlowError(
                f"{fact_id} OFFER ownership must use subject={offer_id} and a registered component owner"
            )
        if required_product not in {product_id, tank_dock_id}:
            raise FlowError(
                f"{fact_id} OFFER must explicitly require a registered product or dock component"
            )
    else:
        raise FlowError(f"unsupported entity_scope for {fact_id}: {entity_scope}")


def make_claim(
    claim_id: str,
    row: dict[str, str],
    overrides: dict[str, Any],
    canonical_source_revisions: dict[str, str],
    canonical_source_priorities: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    statement = required_string(overrides.get("statement", row.get("Claim")), f"claim {claim_id}")
    status = claim_status(row.get("Claim_Status", "Unknown"), overrides.get("status"))
    if not overrides.get("status") and (row.get("Fact_Status") or "").strip().lower() in {
        "conflict",
        "conflicted",
    }:
        status = "CONFLICT"
    if overrides.get("out_of_offer_scope") is True:
        status = "PROHIBITED"
    reasons = []
    for raw in (
        overrides.get("reason"),
        row.get("Conditions"),
        row.get("Prohibited_Use"),
    ):
        if isinstance(raw, str) and raw.strip() and raw.strip() not in reasons:
            reasons.append(raw.strip())
    if overrides.get("out_of_offer_scope") is True:
        reasons.insert(0, "水ステーション専用機能であり、本 Pilot の水箱版のみの範囲外")
    if not reasons:
        reasons.append("No external Claim approval record is attached")
    immediate_source_refs = [
        required_string(item, f"claim {claim_id}.source_refs")
        for item in ensure_list(overrides.get("source_refs"), f"claim {claim_id}.source_refs")
    ]
    if not immediate_source_refs:
        raise FlowError(f"claim {claim_id} requires an immediate source ref")
    upstream_source_refs = parse_upstream_refs(row.get("Source_ID"))
    for ref in parse_upstream_refs(overrides.get("upstream_source_refs", [])):
        if ref not in upstream_source_refs:
            upstream_source_refs.append(ref)
    if not upstream_source_refs:
        raise FlowError(f"claim {claim_id} requires canonical upstream source lineage")
    source_revision = overrides.get("source_revision") or canonical_source_revisions.get(
        upstream_source_refs[0]
    )
    source_market = required_string(row.get("Market") or "Unknown", f"claim {claim_id}.source_market")
    source_priority = overrides.get("source_priority") or canonical_source_priorities.get(
        upstream_source_refs[0]
    )
    if source_priority not in {"P1", "P2", "P3", "P4", "P5"}:
        raise FlowError(f"claim {claim_id} requires a Product Knowledge P1-P5 source priority")
    packet_claim = {
        "id": claim_id,
        "statement": statement,
        "status": status,
        "reason": " | ".join(reasons),
        "source_refs": immediate_source_refs,
    }
    proposal_claim = {
        "claim_id": claim_id,
        "statement": statement,
        "market": "JP",
        "source_market": source_market,
        "locale": "ja-JP",
        "offer_scope": "水箱版のみ",
        "source_id": upstream_source_refs[0],
        "source_revision_id": required_string(
            source_revision, f"claim {claim_id}.source_revision_id"
        ),
        "source_priority": source_priority,
        "immediate_source_refs": immediate_source_refs,
        "upstream_source_refs": upstream_source_refs,
        "transformation_note": (
            "Candidate wording is preserved from the frozen Claim Matrix; no external approval is inferred."
        ),
        "evidence_location": row.get("Evidence_Location") or None,
        "conditions": row.get("Conditions") or None,
        "prohibited_use": row.get("Prohibited_Use") or None,
        "source_fact_status": row.get("Fact_Status") or None,
        "proposed_claim_status": status,
        "external_claim_approval": False,
    }
    return packet_claim, proposal_claim


def risk_for_claim(claim: dict[str, Any]) -> tuple[str, list[str], str]:
    status = claim["proposed_claim_status"]
    text = claim["statement"].lower()
    risks = ["External Claim approval is absent"]
    action = "VERIFY_SOURCE"
    level = "MEDIUM"
    if status in {"PROHIBITED", "CONFLICT"}:
        level = "HIGH"
        action = "RESOLVE_CONFLICT" if status == "CONFLICT" else "REJECT_PROPOSAL"
        risks.append(f"Proposal status is {status}")
    if any(ch.isdigit() for ch in text) or any(
        token in text for token in ("world", "世界", "最小", "%", "matter", "certified", "pse", "telec")
    ):
        level = "HIGH"
        risks.append("Numeric, comparative, certification, or platform language requires bounded evidence")
    return level, risks, action


def build_review_queue(request: dict[str, Any], claims: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for index, claim in enumerate(claims, start=1):
        level, reasons, action = risk_for_claim(claim)
        proposal_status = {
            "PENDING": "PENDING_VERIFICATION",
            "UNKNOWN": "PENDING_VERIFICATION",
            "CONFLICT": "CONFLICT",
            "PROHIBITED": "PROHIBITED",
        }[claim["proposed_claim_status"]]
        items.append(
            {
                "decision_id": f"DEC-{index:03d}-{claim['claim_id']}",
                "item_type": "CLAIM",
                "item_id": claim["claim_id"],
                "proposed_text": claim["statement"],
                "proposal_status": proposal_status,
                "risk_level": level,
                "risk_reasons": reasons,
                "immediate_source_refs": claim["immediate_source_refs"],
                "upstream_source_refs": claim["upstream_source_refs"],
                "requested_action": action,
                "decision": "PENDING",
                "reviewer": None,
                "decided_at": None,
                "rationale": None,
                "decision_effect": {
                    "proposal_only": True,
                    "canonical_product_knowledge_write": False,
                    "external_claim_approval": False,
                },
            }
        )
    if not items:
        raise FlowError("Claim Human Review Queue cannot be empty")
    return {
        "contract_version": "1.0",
        "queue_id": f"CLAIM-QUEUE-{request['run_id']}",
        "run_id": request["run_id"],
        "project_id": request["scope"]["project_id"],
        "product_truth_proposal_ref": "product-truth-proposal.json",
        "generated_at": request["generated_at"],
        "gate": TERMINAL_GATE,
        "review_scope": "PRODUCT_TRUTH_PROPOSAL_ONLY",
        "protections": {
            "canonical_product_knowledge_write": False,
            "external_claim_approval": False,
            "external_publish": False,
        },
        "status": "OPEN",
        "items": items,
    }


def build_conflict_report(
    request: dict[str, Any],
    rows: list[dict[str, str]],
    conflict_source_id: str,
) -> dict[str, Any]:
    issues = []
    for row in rows:
        upstream_refs = parse_upstream_refs(row.get("Source_ID"))
        evidence_pointers = [] if upstream_refs else [
            required_string(row.get("Source_ID"), f"issue {row.get('Issue_ID')}.evidence_pointer")
        ]
        issues.append(
            {
                "issue_id": row.get("Issue_ID"),
                "type": row.get("Type"),
                "priority": row.get("Priority"),
                "topic": row.get("Topic"),
                "observed_evidence": row.get("Observed_Evidence"),
                "impact": row.get("Impact"),
                "required_resolution": row.get("Required_Resolution"),
                "suggested_owner": row.get("Suggested_Owner"),
                "status": row.get("Status"),
                "immediate_source_refs": [conflict_source_id],
                "upstream_source_refs": upstream_refs,
                "evidence_pointers": evidence_pointers,
            }
        )
    for item in ensure_list(request.get("additional_findings", []), "additional_findings"):
        if not isinstance(item, dict):
            raise FlowError("additional_findings entries must be objects")
        normalized = dict(item)
        ambiguous_refs = ensure_list(normalized.pop("source_refs", []), "additional finding source_refs")
        immediate_refs = [
            required_string(ref, "additional finding immediate source ref")
            for ref in ensure_list(
                normalized.pop("immediate_source_refs", []),
                "additional finding immediate_source_refs",
            )
        ]
        upstream_refs = parse_upstream_refs(normalized.pop("upstream_source_refs", []))
        evidence_pointers = [
            required_string(ref, "additional finding evidence pointer")
            for ref in ensure_list(
                normalized.pop("evidence_pointers", []),
                "additional finding evidence_pointers",
            )
        ]
        for raw_ref in ambiguous_refs:
            ref = required_string(raw_ref, "additional finding source ref")
            if CANONICAL_SOURCE_ID.fullmatch(ref):
                if ref not in upstream_refs:
                    upstream_refs.append(ref)
            elif ref not in immediate_refs:
                immediate_refs.append(ref)
        if not immediate_refs:
            immediate_refs.append(conflict_source_id)
        normalized["immediate_source_refs"] = immediate_refs
        normalized["upstream_source_refs"] = upstream_refs
        normalized["evidence_pointers"] = evidence_pointers
        issues.append(normalized)
    conflicts = [item for item in issues if str(item.get("type", "")).lower() in {"conflict", "data_quality"}]
    missing = [item for item in issues if str(item.get("type", "")).lower() in {"gap", "missing"}]
    return {
        "report_version": "1.0",
        "report_id": f"CONFLICT-MISSING-{request['run_id']}",
        "run_id": request["run_id"],
        "generated_at": request["generated_at"],
        "scope": request["scope"],
        "source_snapshot_ref": "source-snapshot.json",
        "counts": {
            "total": len(issues),
            "conflict_or_data_quality": len(conflicts),
            "missing_or_gap": len(missing),
            "p0": sum(1 for item in issues if item.get("priority") == "P0"),
        },
        "issues": issues,
        "resolution_policy": "No conflict is silently merged; missing values remain unconfirmed.",
    }


def product_truth_packet(
    request: dict[str, Any],
    packet_sources: list[dict[str, Any]],
    facts_index: dict[str, dict[str, str]],
    claims_index: dict[str, dict[str, str]],
    canonical_source_revisions: dict[str, str],
    canonical_source_priorities: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    selections = request.get("selection")
    if not isinstance(selections, dict):
        raise FlowError("selection must be an object")
    sections: dict[str, list[dict[str, Any]]] = {name: [] for name in FACT_SECTIONS}
    pk_facts: list[dict[str, Any]] = []
    item_ids: set[str] = set()
    for mapping in ensure_list(selections.get("facts", []), "selection.facts"):
        if not isinstance(mapping, dict):
            raise FlowError("selection.facts entries must be objects")
        section = required_string(mapping.get("section"), "fact mapping.section")
        if section not in FACT_SECTIONS:
            raise FlowError(f"unsupported Product Truth fact section: {section}")
        fid = required_string(mapping.get("fact_id"), "fact mapping.fact_id")
        if fid in item_ids:
            raise FlowError(f"duplicate Product Truth item id: {fid}")
        item_ids.add(fid)
        row = facts_index.get(fid)
        if row is None and not mapping.get("inline", False):
            raise FlowError(f"selected fact is missing from source CSV: {fid}")
        validate_fact_ownership(mapping, request["entity_registry"], fid)
        item = make_fact_item(mapping, row)
        if item["scope"] != "水箱版のみ":
            raise FlowError(f"fact {fid} exceeds water-tank-only scope")
        sections[section].append(item)
        pk_facts.append(
            make_pk_fact(
                item,
                mapping,
                row,
                section,
                canonical_source_revisions,
                canonical_source_priorities,
            )
        )

    claim_overrides = selections.get("claim_overrides", {})
    if not isinstance(claim_overrides, dict):
        raise FlowError("selection.claim_overrides must be an object")
    unapproved_claims = []
    proposal_claims = []
    for claim_id in ensure_list(selections.get("claim_ids", []), "selection.claim_ids"):
        claim_id = required_string(claim_id, "selection.claim_ids")
        row = claims_index.get(claim_id)
        if row is None:
            raise FlowError(f"selected claim is missing from source CSV: {claim_id}")
        override = claim_overrides.get(claim_id, {})
        if not isinstance(override, dict):
            raise FlowError(f"claim override must be an object: {claim_id}")
        packet_claim, proposal_claim = make_claim(
            claim_id,
            row,
            override,
            canonical_source_revisions,
            canonical_source_priorities,
        )
        unapproved_claims.append(packet_claim)
        proposal_claims.append(proposal_claim)

    product = request.get("product")
    if not isinstance(product, dict):
        raise FlowError("product must be an object")
    product_refs = [
        required_string(item, "product.source_refs")
        for item in ensure_list(product.get("source_refs"), "product.source_refs")
    ]
    forbidden_claims = [
        {
            "id": f"FORBID-{claim['id']}",
            "statement": claim["statement"],
            "status": "PROHIBITED",
            "source_refs": claim["source_refs"],
        }
        for claim in unapproved_claims
        if claim["status"] == "PROHIBITED"
    ]
    unknowns = []
    for item in ensure_list(request.get("unknown_tbd", []), "unknown_tbd"):
        if not isinstance(item, dict):
            raise FlowError("unknown_tbd entries must be objects")
        unknowns.append(
            {
                "id": required_string(item.get("id"), "unknown_tbd.id"),
                "question": required_string(item.get("question"), "unknown_tbd.question"),
                "owner": optional_string(item.get("owner"), "unknown_tbd.owner"),
                "deadline": optional_string(item.get("deadline"), "unknown_tbd.deadline"),
                "blocks": [
                    required_string(block, "unknown_tbd.blocks")
                    for block in ensure_list(item.get("blocks"), "unknown_tbd.blocks")
                ],
            }
        )
    packet = {
        "schema_version": "1.0",
        "packet_id": f"PTP-{request['run_id']}",
        "revision": 1,
        "generated_at": request["generated_at"],
        "market": "JP",
        "product": {
            "name": required_string(product.get("name"), "product.name"),
            "official_name_ja": optional_string(product.get("official_name_ja"), "product.official_name_ja"),
            "category": optional_string(product.get("category"), "product.category"),
            "status": fact_status(product.get("raw_status", "Unverified"), product.get("status")),
            "source_refs": product_refs,
        },
        "sku_offers": sections["sku_offers"],
        "specifications": sections["specifications"],
        "approved_claims": [],
        "unapproved_claims": unapproved_claims,
        "compatibility": sections["compatibility"],
        "installation": sections["installation"],
        "target_users": [],
        "user_scenarios": [],
        "pricing": sections["pricing"],
        "bundles": sections["bundles"],
        "available_assets": [],
        "forbidden_claims": forbidden_claims,
        "unknown_tbd": unknowns,
        "sources": packet_sources,
    }
    proposal = {
        "proposal_version": "1.0",
        "proposal_id": f"PK-CHANGE-{request['run_id']}",
        "run_id": request["run_id"],
        "generated_at": request["generated_at"],
        "scope": request["scope"],
        "source_snapshot_ref": "source-snapshot.json",
        "target": {
            "knowledge_layer": "product-knowledge",
            "mode": "PROPOSAL_ONLY",
            "canonical_write": False,
        },
        "facts": pk_facts,
        "claims": proposal_claims,
        "approved_claim_count": 0,
        "review_status": "PENDING_HUMAN_REVIEW",
    }
    return packet, proposal, proposal_claims


def validate_packet_with_upstream(
    packet_path: Path,
    owner_root: Path,
) -> None:
    validator_path = owner_root / "overlays/switchbot-jp/scripts/validate_product_truth_packet.py"
    if not validator_path.is_file():
        raise FlowError(f"upstream Product Truth validator is missing: {validator_path}")
    result = subprocess.run(
        [sys.executable, str(validator_path), str(packet_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        message = (result.stdout + "\n" + result.stderr).strip()
        raise FlowError(f"upstream Product Truth validator failed: {message}")


def render_review(
    request: dict[str, Any],
    packet: dict[str, Any],
    report: dict[str, Any],
    queue: dict[str, Any],
    source_snapshot: dict[str, Any],
) -> str:
    def e(value: Any) -> str:
        return html.escape("" if value is None else str(value), quote=True)

    fact_rows = []
    for section in ("sku_offers", "specifications", "compatibility", "installation", "pricing", "bundles"):
        for item in packet[section]:
            fact_rows.append(
                f"<tr><td>{e(section)}</td><td>{e(item['id'])}</td><td>{e(item['label'])}</td>"
                f"<td>{e(item['value'])}</td><td><span class='status'>{e(item['status'])}</span></td>"
                f"<td>{e(', '.join(item['source_refs']))}</td></tr>"
            )
    claim_rows = []
    for item in queue["items"]:
        claim_rows.append(
            f"<tr><td>{e(item['item_id'])}</td><td>{e(item['proposed_text'])}</td>"
            f"<td><span class='status'>{e(item['proposal_status'])}</span></td>"
            f"<td>{e(item['risk_level'])}</td><td>{e(item['decision'])}</td></tr>"
        )
    issue_rows = []
    for item in report["issues"]:
        issue_rows.append(
            f"<tr><td>{e(item.get('issue_id'))}</td><td>{e(item.get('type'))}</td>"
            f"<td>{e(item.get('priority'))}</td><td>{e(item.get('topic'))}</td>"
            f"<td>{e(item.get('required_resolution'))}</td></tr>"
        )
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>S30 mini Product Truth Proposal Review</title>
<style>
:root {{ color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
body {{ margin: 0; background: #f4f6f8; color: #17202a; }}
header {{ background: #8b1e1e; color: white; padding: 22px 28px; }}
main {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
.banner {{ border: 3px solid #8b1e1e; background: #fff3f3; color: #761717; padding: 16px; font-weight: 800; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(230px,1fr)); gap: 12px; margin: 18px 0; }}
.card {{ background: white; border: 1px solid #dce1e6; border-radius: 10px; padding: 15px; overflow-wrap: anywhere; }}
table {{ width: 100%; max-width: 100%; table-layout: fixed; border-collapse: collapse; background: white; margin: 12px 0 28px; }}
th, td {{ border: 1px solid #dce1e6; padding: 9px; text-align: left; vertical-align: top; overflow-wrap: anywhere; word-break: break-word; }}
th {{ background: #eef2f5; position: sticky; top: 0; }}
.status {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 700; }}
.gate {{ color: #8b1e1e; font-weight: 800; }}
@media (max-width: 640px) {{
  main {{ padding: 12px; }}
  header {{ padding: 18px 16px; }}
  table {{ font-size: 11px; }}
  th, td {{ padding: 6px 4px; }}
}}
</style>
</head>
<body>
<header><h1>Product Truth Proposal Review</h1><div>S30 mini · JP · ja-JP · Amazon.co.jp · 水箱版のみ</div></header>
<main>
<div class="banner">INTERNAL REVIEW / NOT APPROVED / NOT PDP</div>
<div class="grid">
  <div class="card"><strong>Run</strong><br>{e(request['run_id'])}</div>
  <div class="card"><strong>Source</strong><br>{e(source_snapshot['acquisition']['adapter_status'])} → {e(source_snapshot['acquisition']['effective_adapter'])}</div>
  <div class="card"><strong>Approved Claims</strong><br>0</div>
  <div class="card"><strong>Stop Gate</strong><br><span class="gate">{TERMINAL_GATE}</span></div>
</div>
<p>本画面は Product Truth の提案レビュー専用です。正規 Product Knowledge の更新、外部 Claim の承認、Amazon コンテンツ生成、公開を行いません。</p>
<h2>Product facts</h2>
<table><thead><tr><th>Section</th><th>ID</th><th>Field</th><th>Proposal</th><th>Status</th><th>Sources</th></tr></thead><tbody>{''.join(fact_rows)}</tbody></table>
<h2>Claim human review queue</h2>
<table><thead><tr><th>ID</th><th>Candidate expression</th><th>Status</th><th>Risk</th><th>Decision</th></tr></thead><tbody>{''.join(claim_rows)}</tbody></table>
<h2>Conflict / Missing</h2>
<table><thead><tr><th>ID</th><th>Type</th><th>Priority</th><th>Topic</th><th>Required resolution</th></tr></thead><tbody>{''.join(issue_rows)}</tbody></table>
<footer><strong>STOP:</strong> {TERMINAL_GATE}</footer>
</main></body></html>"""


def artifact_record(path: Path, media_type: str) -> dict[str, Any]:
    return {
        "path": path.name,
        "sha256": sha256_file(path),
        "status": "GENERATED",
        "validation_status": "PASS",
        "media_type": media_type,
        "contains_raw_source_body": False,
        "storage": "PRIVATE_RUNTIME_OUTSIDE_GIT",
    }


def quality_check(
    check_id: str,
    validator: str,
    evidence: str,
    subject: Any,
    checked_at: str,
) -> dict[str, Any]:
    subject_bytes = subject.read_bytes() if isinstance(subject, Path) else canonical_bytes(subject)
    return {
        "check_id": check_id,
        "status": "PASS",
        "validator": validator,
        "evidence": evidence,
        "checked_subject_sha256": sha256_bytes(subject_bytes),
        "checked_at": checked_at,
    }


def build_manifest(
    request: dict[str, Any],
    source_snapshot: dict[str, Any],
    output_dir: Path,
    schema_path: Path,
    owner_commit: str,
    warnings: list[str],
    execution: dict[str, Any],
    quality_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    outputs = {
        key: artifact_record(output_dir / filename, "text/html" if filename.endswith(".html") else "application/json")
        for key, filename in OUTPUT_NAMES.items()
    }
    fallback_used = source_snapshot["acquisition"]["fallback_used"]
    workspace_dirty = execution["workspace_dirty"]
    final_state = "P0_1_PARTIAL" if workspace_dirty else "P0_1_READY_FOR_REVIEW"
    blockers = (
        ["Workspace contains uncommitted changes; rerun the Pilot from the reviewed clean commit."]
        if workspace_dirty
        else []
    )
    if source_snapshot["acquisition"]["adapter_status"] == "BLOCKED":
        gateway_basis = (
            "The runner consumed an orchestrator-captured BLOCKED result and did not call or verify "
            "the Gateway repository."
        )
    elif source_snapshot["acquisition"]["effective_adapter"] == "FEISHU_MCP":
        gateway_basis = (
            "The runner consumed a frozen connector response supplied by the orchestrator; it did not "
            "invoke or verify the Gateway repository/runtime itself."
        )
    else:
        gateway_basis = "Feishu MCP was not requested; the Gateway repository/runtime was not used."
    return {
        "contract_version": "1.0",
        "run_id": request["run_id"],
        "flow_id": "product-onboarding",
        "flow_version": FLOW_VERSION,
        "started_at": request["generated_at"],
        "completed_at": request["generated_at"],
        "execution": execution,
        "scope": request["scope"],
        "source_access": {
            "requested_adapter": source_snapshot["acquisition"]["requested_adapter"],
            "feishu_mcp_status": (
                source_snapshot["acquisition"]["adapter_status"]
                if source_snapshot["acquisition"]["requested_adapter"] == "FEISHU_MCP"
                else "NOT_REQUESTED"
            ),
            "effective_adapter": source_snapshot["acquisition"]["effective_adapter"],
            "confirmed_fallback_used": fallback_used,
            "input_confirmation_present": bool(
                source_snapshot["acquisition"].get("input_confirmation")
            ),
            "source_snapshot_id": source_snapshot["snapshot_id"],
            "source_snapshot_ref": "source-snapshot.json",
        },
        "locked_dependencies": [
            {
                "component": "jp-commerce-creative-flow",
                "lock_ref": "skills-lock.json#components/jp-commerce-creative-flow",
                "verification_status": "PASS",
                "verification_basis": "Owner commit, external schema path, $id and SHA-256 were verified at runtime.",
            },
            {
                "component": "feishu-read-gateway-mcp",
                "lock_ref": "skills-lock.json#components/feishu-read-gateway-mcp",
                "verification_status": "NOT_USED",
                "verification_basis": gateway_basis,
            },
            {
                "component": "product-knowledge",
                "lock_ref": "skills-lock.json#components/product-knowledge",
                "verification_status": "NOT_USED",
                "verification_basis": "Only the locked candidate contract is targeted; no installed Skill code or canonical data was executed or written.",
            },
            {
                "component": "project-memory-manager",
                "lock_ref": "skills-lock.json#components/project-memory-manager",
                "verification_status": "NOT_USED",
                "verification_basis": "Project Memory is outside the P0-1 execution path and was not written.",
            },
        ],
        "product_truth_schema": {
            "reference_ref": "contracts/product-truth-schema-reference.json",
            "resolved_path": str(schema_path),
            "owner_repo_commit": owner_commit,
            "schema_id": "https://github.com/laixiaohong/jp-commerce-creative-flow/overlays/switchbot-jp/schemas/product-truth-packet.schema.json",
            "sha256": "881b594f9be3caf170e0b2365980e1c217b5d3b0d556849a7456916f87d70753",
            "validation_status": "PASS",
        },
        "outputs": outputs,
        "quality_checks": quality_checks,
        "governance": {
            "proposal_only": True,
            "canonical_product_knowledge_written": False,
            "project_memory_written": False,
            "amazon_content_generated": False,
            "production_environment_modified": False,
            "external_publish_attempted": False,
            "raw_sensitive_sources_committed": False,
        },
        "blockers": blockers,
        "warnings": warnings,
        "current_gate": TERMINAL_GATE,
        "human_review_required": True,
        "final_state": final_state,
        "manifest_path": "run-manifest.json",
    }


def check_source_refs(packet: dict[str, Any]) -> None:
    source_ids = {item["id"] for item in packet["sources"]}
    if len(source_ids) != len(packet["sources"]):
        raise FlowError("duplicate Product Truth source id")
    refs: list[tuple[str, Iterable[str]]] = [("product", packet["product"]["source_refs"])]
    for section in FACT_SECTIONS | {"target_users", "user_scenarios", "forbidden_claims", "unapproved_claims"}:
        for item in packet[section]:
            refs.append((f"{section}.{item['id']}", item["source_refs"]))
    for label, values in refs:
        missing = sorted(set(values) - source_ids)
        if missing:
            raise FlowError(f"{label} references unknown sources: {', '.join(missing)}")


def validate_pk_proposal(proposal: dict[str, Any]) -> None:
    if proposal.get("approved_claim_count") != 0:
        raise FlowError("Product Knowledge proposal cannot contain approved claims")
    required_fact_fields = {
        "source_id",
        "source_revision_id",
        "product_id",
        "market",
        "information_type",
        "field",
        "value",
        "conditions",
        "evidence_location",
        "source_priority",
        "proposed_review_status",
        "subject_product_id",
        "capability_owner_product_id",
        "required_product_id",
        "entity_scope",
        "immediate_source_refs",
        "upstream_source_refs",
    }
    for fact in proposal.get("facts", []):
        missing = required_fact_fields - set(fact)
        if missing:
            raise FlowError(
                f"Product Knowledge fact {fact.get('proposal_fact_id')} misses candidate fields: {sorted(missing)}"
            )
        if fact["market"] != "JP" or fact["proposed_review_status"] != "pending_verification":
            raise FlowError("Product Knowledge facts must remain JP pending_verification proposals")
        if fact["source_id"] != fact["upstream_source_refs"][0]:
            raise FlowError("candidate source_id must identify the canonical upstream source")
        if fact["conditions"] is not None and not isinstance(fact["conditions"], str):
            raise FlowError("candidate conditions must follow the Product Knowledge string contract")
        if fact["source_priority"] not in {"P1", "P2", "P3", "P4", "P5"}:
            raise FlowError("candidate source_priority must follow Product Knowledge P1-P5 policy")
    for claim in proposal.get("claims", []):
        if claim.get("external_claim_approval") is not False:
            raise FlowError("a Claim proposal cannot infer external approval")
        if not claim.get("immediate_source_refs") or not claim.get("upstream_source_refs"):
            raise FlowError(f"Claim {claim.get('claim_id')} has incomplete source lineage")
        if claim.get("source_id") != claim["upstream_source_refs"][0]:
            raise FlowError("Claim source_id must identify the canonical upstream source")
        if claim.get("source_priority") not in {"P1", "P2", "P3", "P4", "P5"}:
            raise FlowError("Claim source_priority must follow Product Knowledge P1-P5 policy")


def validate_proposal_ownership(proposal: dict[str, Any], entities: dict[str, str]) -> None:
    for fact in proposal["facts"]:
        validate_fact_ownership(
            {
                "entity_scope": fact["entity_scope"],
                "subject_product_id": fact["subject_product_id"],
                "capability_owner_product_id": fact["capability_owner_product_id"],
                "required_product_id": fact["required_product_id"],
            },
            entities,
            fact["proposal_fact_id"],
        )


def validate_cross_output_lineage(
    source_snapshot: dict[str, Any],
    packet: dict[str, Any],
    proposal: dict[str, Any],
    conflict_report: dict[str, Any],
    review_queue: dict[str, Any],
) -> None:
    sources = {source["source_id"]: source for source in source_snapshot["sources"]}

    def check(
        label: str,
        immediate_refs: Any,
        upstream_refs: Any,
        allow_immediate_only: bool = False,
    ) -> None:
        immediate = ensure_list(immediate_refs, f"{label}.immediate_source_refs")
        upstream = ensure_list(upstream_refs, f"{label}.upstream_source_refs")
        if not immediate:
            raise FlowError(f"{label} requires an immediate source")
        unknown_immediate = sorted(set(immediate) - set(sources))
        unknown_upstream = sorted(set(upstream) - set(sources))
        if unknown_immediate or unknown_upstream:
            raise FlowError(
                f"{label} has dangling lineage; immediate={unknown_immediate}, upstream={unknown_upstream}"
            )
        if not upstream:
            if allow_immediate_only:
                return
            raise FlowError(f"{label} requires canonical upstream lineage")
        for ref in upstream:
            if not CANONICAL_SOURCE_ID.fullmatch(ref):
                raise FlowError(f"{label} upstream ref is not canonical: {ref}")
        covered: set[str] = set()
        for ref in immediate:
            covered.update(sources[ref].get("derived_from", []))
            if CANONICAL_SOURCE_ID.fullmatch(ref):
                covered.add(ref)
        missing_relation = sorted(set(upstream) - covered)
        if missing_relation:
            raise FlowError(
                f"{label} immediate sources do not derive from upstream refs: {missing_relation}"
            )

    for fact in proposal["facts"]:
        check(
            f"fact {fact['proposal_fact_id']}",
            fact["immediate_source_refs"],
            fact["upstream_source_refs"],
        )
    for claim in proposal["claims"]:
        check(
            f"claim {claim['claim_id']}",
            claim["immediate_source_refs"],
            claim["upstream_source_refs"],
        )
    for issue in conflict_report["issues"]:
        check(
            f"issue {issue.get('issue_id')}",
            issue.get("immediate_source_refs"),
            issue.get("upstream_source_refs"),
            bool(issue.get("evidence_pointers")),
        )
    for decision in review_queue["items"]:
        check(
            f"review {decision['decision_id']}",
            decision["immediate_source_refs"],
            decision["upstream_source_refs"],
        )
    packet_source_ids = {source["id"] for source in packet["sources"]}
    for ref in packet["product"]["source_refs"]:
        if ref not in packet_source_ids or ref not in sources:
            raise FlowError(f"product identity has an unregistered immediate source: {ref}")


def validate_claim_boundary(packet: dict[str, Any], queue: dict[str, Any]) -> None:
    if packet["approved_claims"]:
        raise FlowError("approved_claims must remain empty in P0-1")
    if any(item["decision"] != "PENDING" for item in queue["items"]):
        raise FlowError("all Claim decisions must remain PENDING at the human review gate")
    packet_claim_ids = {item["id"] for item in packet["unapproved_claims"]}
    queue_claim_ids = {item["item_id"] for item in queue["items"]}
    if packet_claim_ids != queue_claim_ids:
        raise FlowError("Claim queue and Product Truth proposal Claim IDs diverge")


def validate_review_html(path: Path, packet: dict[str, Any], queue: dict[str, Any]) -> None:
    content = path.read_text(encoding="utf-8")
    required_markers = {
        "INTERNAL REVIEW / NOT APPROVED / NOT PDP",
        TERMINAL_GATE,
        "Approved Claims</strong><br>0",
    }
    missing = sorted(marker for marker in required_markers if marker not in content)
    if missing:
        raise FlowError(f"review HTML misses safety markers: {missing}")
    if any(token in path.name.lower() for token in DISALLOWED_OUTPUT_TOKENS):
        raise FlowError("review HTML has an out-of-scope filename")
    for claim in queue["items"]:
        if html.escape(claim["item_id"], quote=True) not in content:
            raise FlowError(f"review HTML omits Claim {claim['item_id']}")
    if len(packet["approved_claims"]) != 0:
        raise FlowError("review HTML cannot represent an approved P0-1 Claim")


def validate_output_boundary(output_dir: Path, request_path: Path) -> None:
    files = {path.name for path in output_dir.iterdir() if path.is_file()}
    directories = {path.name for path in output_dir.iterdir() if path.is_dir()}
    allowed_files = set(OUTPUT_NAMES.values()) | {"run-manifest.json", request_path.name}
    unexpected = sorted(files - allowed_files)
    if directories - {"inputs"}:
        unexpected.extend(sorted(directories - {"inputs"}))
    disallowed = sorted(
        name
        for name in files
        if any(token in name.lower() for token in DISALLOWED_OUTPUT_TOKENS)
    )
    if unexpected or disallowed:
        raise FlowError(
            f"unexpected or out-of-scope runtime artifacts: unexpected={unexpected}, disallowed={disallowed}"
        )


def run(
    request_path: Path,
    output_dir: Path,
    repo_root: Path,
    explicit_schema: Path | None,
) -> dict[str, Any]:
    assert_private_runtime(output_dir, repo_root)
    if request_path.parent.resolve() != output_dir.resolve() or request_path.name != "request.json":
        raise FlowError("request.json must be frozen at the root of its private run directory")
    request = load_json(request_path)
    check_request(request)
    if acquisition_is_blocked(request):
        raise FlowError("primary source adapter is BLOCKED and no confirmed fallback is available")

    raw_sources = ensure_list(request.get("sources"), "sources")
    if any(not isinstance(source, dict) for source in raw_sources):
        raise FlowError("sources entries must be objects")
    validate_adapter_policy(request, raw_sources)
    tables = request.get("tables")
    if not isinstance(tables, dict):
        raise FlowError("tables must be an object")
    table_paths = {
        name: Path(required_string(tables.get(name), f"tables.{name}")).expanduser().resolve()
        for name in ("facts", "claims", "conflicts", "source_index")
    }
    source_paths: list[Path] = []
    for source in raw_sources:
        path = Path(required_string(source.get("path"), "source.path")).expanduser().resolve()
        assert_runtime_input(path, output_dir, f"source {source.get('source_id')}")
        source_paths.append(path)
    for name, path in table_paths.items():
        assert_runtime_input(path, output_dir, f"table {name}")
    input_paths = sorted(set(source_paths + list(table_paths.values())), key=str)
    secure_runtime(output_dir, request_path, input_paths)

    reference = load_json(repo_root / "contracts/product-truth-schema-reference.json")
    owner_root, schema_path, owner_commit = resolve_schema_owner(repo_root, reference, explicit_schema)

    snapshot_sources: list[dict[str, Any]] = []
    packet_sources = []
    for source in raw_sources:
        snapshot_source, packet_source = normalize_source(source, request["generated_at"])
        snapshot_sources.append(snapshot_source)
        packet_sources.append(packet_source)
    if not snapshot_sources:
        raise FlowError("at least one source is required")
    source_index_rows, _ = read_csv_index(table_paths["source_index"], "Source_ID")
    snapshot_sources.extend(
        pointer_source(row, table_paths["source_index"], request["generated_at"])
        for row in source_index_rows
    )
    validate_snapshot_lineage(snapshot_sources)
    source_snapshot = build_source_snapshot(request, snapshot_sources)
    validate_json(source_snapshot, repo_root / "contracts/source-snapshot.schema.json", "Source Snapshot")
    canonical_revisions = canonical_revision_map(snapshot_sources)

    fact_rows, fact_index = read_csv_index(table_paths["facts"], "Fact_ID")
    claim_rows, claim_index = read_csv_index(table_paths["claims"], "Claim_ID")
    conflict_rows, _ = read_csv_index(table_paths["conflicts"], "Issue_ID")
    del fact_rows, claim_rows
    conflict_source_ids = [
        source["source_id"]
        for source in raw_sources
        if Path(source["path"]).expanduser().resolve() == table_paths["conflicts"]
    ]
    if len(conflict_source_ids) != 1:
        raise FlowError("the frozen conflict register must have exactly one immediate source registration")

    packet, pk_proposal, proposal_claims = product_truth_packet(
        request,
        packet_sources,
        fact_index,
        claim_index,
        canonical_revisions,
        request["product_knowledge_source_priorities"],
    )
    check_source_refs(packet)
    validate_json(packet, schema_path, "Product Truth Proposal")
    conflict_report = build_conflict_report(request, conflict_rows, conflict_source_ids[0])
    review_queue = build_review_queue(request, proposal_claims)
    validate_json(review_queue, repo_root / "contracts/review-decision.schema.json", "Review Decision")
    validate_pk_proposal(pk_proposal)
    validate_proposal_ownership(pk_proposal, request["entity_registry"])
    validate_claim_boundary(packet, review_queue)
    validate_cross_output_lineage(
        source_snapshot, packet, pk_proposal, conflict_report, review_queue
    )

    write_json(output_dir / OUTPUT_NAMES["source_snapshot"], source_snapshot)
    write_json(output_dir / OUTPUT_NAMES["product_knowledge_change_proposal"], pk_proposal)
    write_json(output_dir / OUTPUT_NAMES["product_truth_proposal"], packet)
    write_json(output_dir / OUTPUT_NAMES["conflict_missing_report"], conflict_report)
    write_json(output_dir / OUTPUT_NAMES["claim_human_review_queue"], review_queue)
    html_path = output_dir / OUTPUT_NAMES["product_truth_review_html"]
    html_path.write_text(
        render_review(request, packet, conflict_report, review_queue, source_snapshot),
        encoding="utf-8",
    )
    html_path.chmod(0o600)
    validate_packet_with_upstream(output_dir / OUTPUT_NAMES["product_truth_proposal"], owner_root)
    validate_review_html(html_path, packet, review_queue)
    validate_output_boundary(output_dir, request_path)

    warnings = []
    if source_snapshot["acquisition"]["adapter_status"] == "BLOCKED":
        warnings.append(
            "Feishu MCP was BLOCKED in this run; an explicitly confirmed local fallback was used."
        )
    warnings.extend(
        [
            "All claims are unapproved proposals; external use remains blocked.",
            "Open conflicts and missing data are carried to human review without silent resolution.",
        ]
    )

    workspace_commit, workspace_dirty = git_provenance(repo_root)
    runner_path = repo_root / "flows/product-onboarding/scripts/run_product_onboarding.py"
    execution = {
        "request_ref": "request.json",
        "request_sha256": sha256_file(request_path),
        "runner_path": "flows/product-onboarding/scripts/run_product_onboarding.py",
        "runner_sha256": sha256_file(runner_path),
        "workspace_repo": "masayukihub/marketing-ai-workspace",
        "workspace_commit": workspace_commit,
        "workspace_dirty": workspace_dirty,
        "inputs_sha256": {
            str(path.relative_to(output_dir)): sha256_file(path) for path in input_paths
        },
    }
    checked_at = request["generated_at"]
    quality_checks = [
        quality_check(
            "CONTRACT_DRIFT",
            "resolve_schema_owner+Draft202012Validator+upstream_validator",
            "Locked owner commit, schema dialect, $id and SHA matched; upstream validator passed.",
            {
                "owner_commit": owner_commit,
                "schema_path": str(schema_path),
                "schema_sha256": sha256_file(schema_path),
            },
            checked_at,
        ),
        quality_check(
            "SOURCE_TRACEABILITY",
            "validate_snapshot_lineage+validate_cross_output_lineage",
            "Immediate and canonical upstream refs resolve across snapshot, facts, Claims, conflicts and queue.",
            source_snapshot,
            checked_at,
        ),
        quality_check(
            "PRODUCT_KNOWLEDGE_CANDIDATE_CONTRACT",
            "validate_pk_proposal",
            "Atomic candidates carry source, revision, market, conditions, evidence and pending review state.",
            pk_proposal,
            checked_at,
        ),
        quality_check(
            "CAPABILITY_OWNERSHIP",
            "validate_proposal_ownership",
            "Product, tank-dock and offer facts retain registered ownership and dependency relationships.",
            pk_proposal["facts"],
            checked_at,
        ),
        quality_check(
            "CLAIM_BOUNDARY",
            "validate_claim_boundary",
            "approved_claims is empty; every candidate remains in the PENDING human decision queue.",
            {"claims": packet["unapproved_claims"], "queue": review_queue["items"]},
            checked_at,
        ),
        quality_check(
            "REVIEW_HTML",
            "validate_review_html",
            "Review artifact carries the safety banner, zero approved Claims, all queue IDs and stop gate.",
            html_path,
            checked_at,
        ),
        quality_check(
            "PRIVATE_RUNTIME",
            "assert_private_runtime+assert_runtime_input+secure_runtime",
            "Request, frozen inputs and outputs are outside Git with restricted runtime permissions.",
            {"runtime": str(output_dir), "inputs": sorted(execution["inputs_sha256"])},
            checked_at,
        ),
        quality_check(
            "OUTPUT_BOUNDARY",
            "validate_output_boundary",
            "Only the P0-1 request, inputs and bounded proposal/review artifacts are present.",
            sorted(
                ["inputs", request_path.name, "run-manifest.json", *OUTPUT_NAMES.values()]
            ),
            checked_at,
        ),
    ]
    manifest = build_manifest(
        request,
        source_snapshot,
        output_dir,
        schema_path,
        owner_commit,
        warnings,
        execution,
        quality_checks,
    )
    validate_json(manifest, repo_root / "contracts/run-manifest.schema.json", "Run Manifest")
    write_json(output_dir / "run-manifest.json", manifest)
    validate_output_boundary(output_dir, request_path)
    if manifest["final_state"] not in ALLOWED_FINAL_STATES:
        raise FlowError("invalid final state")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--product-truth-schema", type=Path)
    args = parser.parse_args()
    try:
        manifest = run(
            args.request.resolve(),
            args.output_dir.resolve(),
            args.repo_root.resolve(),
            args.product_truth_schema.resolve() if args.product_truth_schema else None,
        )
    except FlowError as exc:
        print(f"P0_1_BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"final_state": manifest["final_state"], "current_gate": manifest["current_gate"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
