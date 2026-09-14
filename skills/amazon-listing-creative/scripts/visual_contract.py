#!/usr/bin/env python3
"""Read-only checks of declared production intent and image-review evidence.

This module never views pixels, renders, accesses a URL, changes a Spec, or
approves production. EVIDENCE_RECORDED describes consistent review records bound
to local file bytes; it does not establish the truth of those observations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

VISUAL_TYPES = {"official_packshot", "commercial_scene", "mechanism_visual", "information_graphic"}
CHECKS = {"integration", "visual_proof", "reference_match"}
SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
MAX_FILE_BYTES = 100 * 1024 * 1024


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _choice(value: Any, options: set[str], label: str) -> str:
    if not isinstance(value, str) or value not in options:
        raise ValueError(f"{label} must be one of {', '.join(sorted(options))}")
    return value


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _ids(value: Any, label: str) -> list[str]:
    values = [_text(item, label) for item in _list(value, label)]
    if len(set(values)) != len(values):
        raise ValueError(f"{label} contains duplicate IDs")
    return values


def _records(value: Any, label: str) -> dict[str, dict[str, Any]]:
    result = {}
    for record in _list(value, label):
        record = _object(record, label)
        key = _text(record.get("id"), f"{label}.id")
        if key in result:
            raise ValueError(f"Duplicate {label} ID: {key}")
        result[key] = record
    return result


def _safe_file(root: Path, value: Any) -> Path:
    value = _text(value, "file")
    rel = Path(value)
    if (rel.is_absolute() or ":" in value or "\\" in value or
            any(ord(char) < 32 for char in value) or ".." in rel.parts):
        raise ValueError("UNSAFE_FILE_PATH: use a local path relative to output-dir")
    file = (root / rel).resolve()
    if not file.is_relative_to(root) or file == root:
        raise ValueError("UNSAFE_FILE_PATH: resolved file must remain inside output-dir")
    return file


def input_error(detail: str) -> dict[str, Any]:
    """Use the same non-approval boundary for malformed input and valid records."""
    result = _result()
    result.update(status="INVALID_INPUT", issues=[{"id": "contract", "code": "INVALID_INPUT", "detail": detail}])
    return result


def _result() -> dict[str, Any]:
    return {
        "checker_version": "1.0",
        "status": "NEEDS_REVISION",
        "anchor_evidence": {"required": [], "recorded": []},
        "issues": [],
        "unchanged": ["Spec", "Claims", "assets", "approvals", "production permissions", "project state"],
        "not_verified": [
            "actual pixel viewing or truth of review observations", "aesthetic quality",
            "product accuracy or geometry authority", "asset rights", "claim approval",
            "human approval", "whole-set review", "browser QA", "Seller Central rendering",
            "publication readiness",
        ],
        "meaning": "EVIDENCE_RECORDED means review-record coverage and file-hash consistency only. "
                   "It is not a visual-quality verdict, human approval, or permission for batch production or publication.",
    }


def check(contract: Any, root: Path) -> dict[str, Any]:
    """Validate declared records and local hash bindings without modifying files."""
    result = _result()
    issues = result["issues"]

    def issue(owner: str, code: str, detail: str) -> None:
        issues.append({"id": owner, "code": code, "detail": detail})

    def binding(owner: str, record: dict[str, Any], kind: str) -> bool:
        file = _safe_file(root, record.get("file"))
        digest = record.get("sha256")
        if digest is None or digest == "":
            issue(owner, "MISSING_SHA256", f"{kind} requires the reviewed file's SHA256")
            return False
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ValueError(f"{owner}: sha256 must contain exactly 64 hexadecimal characters")
        if not file.is_file():
            issue(owner, "MISSING_FILE", f"{kind}: {record['file']}")
            return False
        if file.stat().st_size > MAX_FILE_BYTES:
            issue(owner, "FILE_TOO_LARGE", f"{kind}: maximum {MAX_FILE_BYTES} bytes")
            return False
        actual = hashlib.sha256(file.read_bytes()).hexdigest()
        if actual != digest.lower():
            issue(owner, "HASH_MISMATCH", f"{kind}: review applies to different bytes; inspect the current file again")
            return False
        return True

    try:
        root = Path(root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("output-dir must be a directory")
        contract = _object(contract, "contract")
        if contract.get("schema_version") != "1.0":
            raise ValueError("schema_version must be '1.0'")
        references = _records(contract.get("references"), "references")
        assets = _records(contract.get("assets"), "assets")
        if not assets:
            raise ValueError("assets must contain at least one declared target")
        anchors = _ids(contract.get("anchor_asset_ids"), "anchor_asset_ids")
        reviews = _list(contract.get("anchor_reviews"), "anchor_reviews")
        result["anchor_evidence"]["required"] = anchors

        for key, ref in references.items():
            url = urlsplit(_text(ref.get("url"), f"{key}.url"))
            if url.scheme not in {"http", "https"} or not url.hostname:
                raise ValueError(f"{key}.url must be an HTTP(S) source URL; URLs are never fetched")
            level = _choice(ref.get("evidence_level"), {"PIXELS_VIEWED", "DOM_ONLY", "UNAVAILABLE"}, f"{key}.evidence_level")
            observation = ref.get("observations")
            if not isinstance(observation, str):
                raise ValueError(f"{key}.observations must be a string")
            if level == "PIXELS_VIEWED" and not observation.strip():
                issue(key, "REFERENCE_OBSERVATION_MISSING", "Record concrete observations from actual pixel viewing")

        for key, asset in assets.items():
            kind = _choice(asset.get("visual_type"), VISUAL_TYPES, f"{key}.visual_type")
            method = _choice(asset.get("production_method"), {"official_composite", "approved_cg", "information_graphic"}, f"{key}.production_method")
            body = _choice(asset.get("product_body_source"), {"official_asset", "approved_cad", "none"}, f"{key}.product_body_source (AI product bodies are not allowed)")
            view = _choice(asset.get("geometry_view"), {"exterior", "cutaway", "transparent", "exploded"}, f"{key}.geometry_view")
            proof = _object(asset.get("visual_proof"), f"{key}.visual_proof")
            for field in ("object", "action", "visible_result"):
                _text(proof.get(field), f"{key}.visual_proof.{field}")
            if kind != "information_graphic" and method == "information_graphic":
                issue(key, "PRODUCTION_TYPE_MISMATCH", f"{kind} cannot be satisfied by information_graphic production")
            if kind != "information_graphic" and body == "none":
                issue(key, "PRODUCT_BODY_SOURCE_MISSING", f"{kind} requires an official or approved product body")
            for ref_id in _ids(asset.get("reference_ids"), f"{key}.reference_ids"):
                if ref_id not in references:
                    raise ValueError(f"{key}: unknown styling reference {ref_id}")
                if references[ref_id]["evidence_level"] != "PIXELS_VIEWED":
                    issue(key, "STYLING_REFERENCE_NOT_VIEWED", f"{ref_id}: DOM-only or unavailable evidence cannot establish visual appearance")
            geometry = asset.get("geometry_evidence")
            if geometry is None and (view != "exterior" or body == "approved_cad"):
                issue(key, "GEOMETRY_EVIDENCE_MISSING", f"{view}/{body} requires a bound authorized geometry source; a packshot alone is insufficient")
            elif geometry is not None:
                geometry = _object(geometry, f"{key}.geometry_evidence")
                _choice(geometry.get("source_type"), {"approved_cad", "approved_geometry_reference"}, f"{key}.geometry_evidence.source_type")
                binding(key, geometry, "geometry evidence")

        if not anchors:
            issue("contract", "ANCHORS_MISSING", "Select a small representative set for actual per-image inspection")
        for key in anchors:
            if key not in assets:
                raise ValueError(f"Unknown anchor asset ID: {key}")
        represented = {assets[key]["visual_type"] for key in anchors}
        for kind in sorted({a["visual_type"] for a in assets.values()} - represented):
            issue("contract", "VISUAL_TYPE_UNREPRESENTED", f"Select an anchor for {kind}; an information graphic cannot represent a scene or mechanism")

        seen_reviews: set[str] = set()
        for review in reviews:
            review = _object(review, "anchor_reviews item")
            key = _text(review.get("asset_id"), "anchor_reviews.asset_id")
            if key not in assets:
                raise ValueError(f"Review refers to unknown asset ID: {key}")
            if key in seen_reviews:
                raise ValueError(f"Duplicate review for {key}; supply one current review per asset")
            seen_reviews.add(key)
            before = len(issues)
            bound = binding(key, review, "anchor review")
            observed = _choice(review.get("observed_visual_type"), VISUAL_TYPES, f"{key}.observed_visual_type")
            _choice(review.get("reviewer_type"), {"model", "human"}, f"{key}.reviewer_type")
            if observed != assets[key]["visual_type"]:
                issue(key, "OBSERVED_TYPE_MISMATCH", f"Requested {assets[key]['visual_type']}; reviewer observed {observed}")
            checks = _object(review.get("checks"), f"{key}.checks")
            for name in sorted(CHECKS):
                entry = checks.get(name)
                if entry is None:
                    issue(key, "CHECK_NOT_RECORDED", f"{name}: actual image observation is required")
                    continue
                entry = _object(entry, f"{key}.checks.{name}")
                status = _choice(entry.get("status"), {"PASS", "REVISE", "NOT_CHECKED"}, f"{key}.checks.{name}.status")
                observation = entry.get("observation")
                if status != "PASS":
                    issue(key, "REVIEW_NEEDS_REVISION", f"{name}: {status}")
                if not isinstance(observation, str) or not observation.strip():
                    issue(key, "REVIEW_OBSERVATION_MISSING", f"{name}: add a concrete per-image observation")
            if bound and len(issues) == before:
                result["anchor_evidence"]["recorded"].append(key)
        for key in anchors:
            if key not in seen_reviews:
                issue(key, "ANCHOR_REVIEW_MISSING", "Inspect this exact output and record its hash, type and observations")
        result["status"] = "NEEDS_REVISION" if issues else "EVIDENCE_RECORDED"
        return result
    except (OSError, ValueError, RuntimeError) as exc:
        return input_error(str(exc))


def check_file(contract_file: Path, output_dir: Path) -> dict[str, Any]:
    try:
        raw = contract_file.read_bytes()
        result = check(json.loads(raw), output_dir)
        result["input_contract_sha256"] = hashlib.sha256(raw).hexdigest()
        return result
    except (OSError, ValueError) as exc:
        return input_error(str(exc))


def exit_code(result: dict[str, Any]) -> int:
    return {"EVIDENCE_RECORDED": 0, "NEEDS_REVISION": 1, "INVALID_INPUT": 2}[result["status"]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    checking = sub.add_parser("check")
    checking.add_argument("--contract", type=Path, required=True)
    checking.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = check_file(args.contract, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
