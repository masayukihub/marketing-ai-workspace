#!/usr/bin/env python3
"""Read-only scope routing and artifact coverage audit; NOT a renderer or approval gate.

Consumes the existing PRODUCT_PAGE_SPEC. It never changes product facts, approvals,
assets or project state. Pillow is optional for routing, required for image checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:
    Image = None

SCOPES = {"full": ["gallery", "aplus"], "gallery": ["gallery"], "aplus": ["aplus"], "concept": ["concept"]}


def route(scope: str, intent: str) -> dict[str, Any]:
    if scope not in SCOPES:
        raise ValueError("Unknown scope")
    if intent not in {"create", "plan", "resume", "revise", "explore", "deep_dive"}:
        raise ValueError("Unknown intent")
    if (scope == "concept") != (intent in {"explore", "deep_dive"}):
        raise ValueError("Nine-grid/exploration is an explicit concept subtask, not a full-page deliverable")
    concept = scope == "concept"
    return {
        "entry": "amazon-listing-creative" if concept else "jp-commerce-content-flow",
        "mode": ({"explore": "CREATIVE_EXPLORE", "deep_dive": "DIRECTION_DEEP_DIVE"}[intent] if concept else
                 {"create": "FULL_FLOW", "plan": "PLAN_ONLY", "resume": "RESUME", "revise": "LOCAL_REVISION"}[intent]),
        "required_outputs": SCOPES[scope],
        "scope": scope,
        "preserve_existing_gallery": scope == "aplus" or intent in {"resume", "revise"},
        "execute": False,
        "stop_at": "NEXT_MATERIAL_HUMAN_GATE",
        "publication_approval": "UNCHANGED",
    }


def _nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(_nonempty(v) for v in value.values())
    if isinstance(value, list):
        return any(_nonempty(v) for v in value)
    return False


def audit(spec: dict[str, Any], root: Path, scope: str) -> dict[str, Any]:
    if scope not in {"full", "gallery", "aplus"}:
        raise ValueError("Audit requires full, gallery or aplus scope")
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("output-dir must be a directory")
    issues: list[dict[str, str]] = []
    artifacts: list[dict[str, Any]] = []
    expected_ids: dict[str, list[str]] = {family: [] for family in SCOPES[scope]}
    seen_ids: set[str] = set()

    def issue(owner: str, code: str, detail: str) -> None:
        issues.append({"id": owner, "code": code, "detail": detail})

    def identity(record: Any, family: str, fallback: str) -> str:
        if not isinstance(record, dict):
            issue(fallback, "INVALID_RECORD", "Expected an object in frozen Spec")
            return fallback
        value = record.get("id")
        if not isinstance(value, str) or not value.strip():
            issue(fallback, "MISSING_ID", "Stable ID is required; do not invent an approved ID")
            return fallback
        if value in seen_ids:
            issue(value, "DUPLICATE_ID", "IDs must be unique across requested families/modules/units/slides")
        seen_ids.add(value)
        return value

    def raster(owner: str, viewport: str, value: Any) -> None:
        row: dict[str, Any] = {"id": owner, "viewport": viewport, "path": value, "status": "MISSING"}
        artifacts.append(row)
        if not isinstance(value, str) or not value.strip():
            issue(owner, "MISSING_OUTPUT_PATH", viewport)
            return
        rel = Path(value)
        if rel.is_absolute() or ":" in value or "\\" in value or ".." in rel.parts:
            issue(owner, "UNSAFE_OUTPUT_PATH", "Only local paths relative to output-dir are allowed")
            return
        file = (root / rel).resolve()
        if not file.is_relative_to(root):
            issue(owner, "UNSAFE_OUTPUT_PATH", "Resolved path escapes output-dir")
            return
        if not file.is_file():
            issue(owner, "MISSING_IMAGE", f"{viewport}: {value}")
            return
        if file.stat().st_size > 100 * 1024 * 1024:
            issue(owner, "IMAGE_TOO_LARGE_TO_AUDIT", value)
            return
        if Image is None:
            row["status"] = "PRESENT_UNVERIFIED"
            issue(owner, "DECODER_UNAVAILABLE", "Run with the existing verified Pillow environment")
            return
        try:
            with Image.open(file) as im:
                fmt = im.format
                if fmt not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Expected a raster composite, not a prompt, SVG or unsupported format")
                im.verify()
            with Image.open(file) as im:
                im.load()
                row["width"], row["height"] = im.size
            row.update(status="DECODED", format=fmt, sha256=hashlib.sha256(file.read_bytes()).hexdigest())
        except Exception as exc:
            row["status"] = "INVALID_IMAGE"
            issue(owner, "INVALID_IMAGE", f"{viewport}: {type(exc).__name__}")

    def outputs(record: dict[str, Any]) -> dict[str, Any]:
        value = record.get("outputs", {})
        return value if isinstance(value, dict) else {}

    for family, key in [("gallery", "product_images"), ("aplus", "aplus_modules")]:
        if family not in expected_ids:
            continue
        records = spec.get(key)
        if not isinstance(records, list) or not records:
            issue(family, "REQUIRED_SCOPE_EMPTY", f"Frozen Spec has no {key}; Gallery cannot satisfy A+/EBC scope")
            continue
        for index, record in enumerate(records, 1):
            owner = identity(record, family, f"{family}-unmapped-{index}")
            expected_ids[family].append(owner)
            if not isinstance(record, dict):
                continue
            out = outputs(record)
            if family == "gallery":
                raster(owner, "desktop", out.get("jpeg") or out.get("png") or out.get("webp"))
                continue
            units = record.get("units")
            if not isinstance(units, list) or not units:
                issue(owner, "APLUS_UNITS_EMPTY", "An A+ module needs its approved content units")
            else:
                for ui, unit in enumerate(units, 1):
                    identity(unit, family, f"{owner}-unmapped-unit-{ui}")
            # Native text/table modules are not pretend raster images. Binding still
            # requires separate renderer/browser evidence; this auditor does not supply it.
            if record.get("delivery_kind") == "native":
                if not isinstance(record.get("native_content"), (dict, list)) or not _nonempty(record["native_content"]):
                    issue(owner, "NATIVE_CONTENT_MISSING", "Expected nonempty native text/table fields")
                if not _nonempty(record.get("preview_binding")):
                    issue(owner, "NATIVE_BINDING_MISSING", "Identify the real preview component; not a PNG placeholder")
                continue
            marker = " ".join(str(record.get(k, "")) for k in ("interaction", "module_type", "template_id")).lower()
            slides = record.get("slides")
            if "carousel" in marker or slides is not None:
                if not isinstance(slides, list) or not slides:
                    issue(owner, "CAROUSEL_SLIDES_UNMAPPED", "Map every slide; one module JPG is not an entire carousel")
                    continue
                for si, slide in enumerate(slides, 1):
                    sid = identity(slide, family, f"{owner}-unmapped-slide-{si}")
                    if not isinstance(slide, dict):
                        continue
                    so = outputs(slide)
                    raster(sid, "desktop", so.get("jpeg") or so.get("png") or so.get("webp"))
                    raster(sid, "mobile", so.get("mobile_jpeg") or so.get("mobile_png") or so.get("mobile_webp"))
                continue
            raster(owner, "desktop", out.get("jpeg") or out.get("png") or out.get("webp"))
            mobile = out.get("mobile_jpeg") or out.get("mobile_png") or out.get("mobile_webp")
            sequence = record.get("sequence")
            # Only this path fallback is evidenced in render_v4.mjs. It is NOT an
            # Amazon platform size rule and does not infer a center-crop strategy.
            if mobile is None and type(sequence) is int and sequence > 0:
                mobile = f"design/aplus/mobile/aplus_{sequence:02d}.jpg"
            raster(owner, "mobile", mobile)

    bad_ids = list(dict.fromkeys(item["id"] for item in issues))
    summary = {}
    for family, ids in expected_ids.items():
        summary[family] = {"expected": len(ids), "ids": ids}
    return {
        "audit_version": "1.0",
        "status": "ARTIFACTS_PRESENT" if not issues else "ARTIFACTS_INCOMPLETE",
        "scope": scope,
        "summary": summary,
        "raster_files_expected": len(artifacts),
        "raster_files_decoded": sum(a["status"] == "DECODED" for a in artifacts),
        "artifacts": artifacts,
        "issues": issues,
        "resume_queue": bad_ids,
        "resume_policy": "Inspect each issue; only rerender missing/invalid unlocked outputs after existing gates. Do not regenerate completed Gallery.",
        "publish_gate_in_spec": spec.get("publish_gate", {}).get("status", "UNKNOWN") if isinstance(spec.get("publish_gate", {}), dict) else "UNKNOWN",
        "unchanged": ["Spec", "Story", "Claims", "Asset rights", "approvals", "existing outputs"],
        "not_verified": ["product accuracy", "placeholder provenance", "claim approval", "channel dimensions", "native text mounting", "preview assembly", "desktop/mobile browser QA", "Seller Central rendering", "publication readiness"],
        "meaning": "ARTIFACTS_PRESENT is file/structure coverage only, never delivery or publication approval.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    routing = sub.add_parser("route")
    routing.add_argument("--scope", choices=SCOPES, required=True)
    routing.add_argument("--intent", choices=["create", "plan", "resume", "revise", "explore", "deep_dive"], required=True)
    checking = sub.add_parser("audit")
    checking.add_argument("--scope", choices=["full", "gallery", "aplus"], required=True)
    checking.add_argument("--spec", type=Path, required=True)
    checking.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "route":
            result = route(args.scope, args.intent)
        else:
            raw = args.spec.read_bytes()
            spec = json.loads(raw)
            if not isinstance(spec, dict):
                raise ValueError("Spec root must be an object")
            result = audit(spec, args.output_dir, args.scope)
            result["input_spec_sha256"] = hashlib.sha256(raw).hexdigest()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("status") == "ARTIFACTS_INCOMPLETE" else 0
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "AUDIT_INPUT_ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
