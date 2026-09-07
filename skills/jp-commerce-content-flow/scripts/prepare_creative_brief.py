#!/usr/bin/env python3
"""Compile a narrow production packet; does not generate images or approve facts.

Usage: python prepare_creative_brief.py brief.json
Required strings: asset_id, placement, shopper_task, primary_message,
desired_takeaway, proof_object, production_mode, evidence_mode.
Required objects: canvas {width, height, mobile_width},
composition {scene, camera, light, product_placement, negative_space},
sources {product: [refs], proof: [refs], ui: [refs], scene: [refs]}.
Required lists: must_show, must_not_show, locks (strings; locks may be empty).
Optional copy_layer is a list of approved strings for programmatic typesetting.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MODES = {"SOURCE_COMPOSITE", "GENERATIVE_SCENE", "PROOF_COMPOSITE", "UI_COMPOSITE", "DESIGN_LAYOUT"}
EVIDENCE_MODES = {"SOURCE_FAITHFUL", "CREATIVE_MOCK", "PROOF_VISUAL"}


def compile_brief(brief: dict) -> dict:
    def text(key, source=None):
        value = (brief if source is None else source).get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing nonempty string: {key}")
        return value.strip()

    def strings(value, label, required=False):
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            raise ValueError(f"{label} must be a list of nonempty strings")
        if required and not value:
            raise ValueError(f"Missing {label}")
        return [v.strip() for v in value]

    if not isinstance(brief, dict):
        raise ValueError("Brief must be a JSON object")
    mode = text("production_mode")
    evidence_mode = text("evidence_mode")
    if mode not in MODES or evidence_mode not in EVIDENCE_MODES:
        raise ValueError("Unsupported production_mode or evidence_mode")
    canvas = brief.get("canvas", {})
    composition = brief.get("composition", {})
    sources = brief.get("sources", {})
    if not all(isinstance(value, dict) for value in (canvas, composition, sources)):
        raise ValueError("canvas, composition and sources must be objects")
    dimensions = {}
    for key in ("width", "height", "mobile_width"):
        value = canvas.get(key)
        if type(value) is not int or value <= 0:
            raise ValueError(f"canvas.{key} must be a positive integer")
        dimensions[key] = value
    shot = {key: text(key, composition) for key in
            ("scene", "camera", "light", "product_placement", "negative_space")}
    refs = {key: strings(sources.get(key, []), f"sources.{key}") for key in ("product", "proof", "ui", "scene")}
    if not refs["product"]:
        raise ValueError("Official product identity source required; do not invent product appearance")
    if (mode == "PROOF_COMPOSITE" or evidence_mode == "PROOF_VISUAL") and not refs["proof"]:
        raise ValueError("Proof source required; return to evidence planning")
    if mode == "UI_COMPOSITE" and not refs["ui"]:
        raise ValueError("Real UI source required")
    packet = {key: text(key) for key in ("asset_id", "placement", "shopper_task",
              "primary_message", "desired_takeaway", "proof_object")}
    packet.update({
        "production_mode": mode, "evidence_mode": evidence_mode,
        "canvas": dimensions, "composition": shot, "sources": refs,
        "must_show": strings(brief.get("must_show"), "must_show", True),
        "must_not_show": strings(brief.get("must_not_show"), "must_not_show", True),
        "locks": strings(brief.get("locks"), "locks"),
        "copy_layer": strings(brief.get("copy_layer", []), "copy_layer"),
        "validation_scope": "FIELD_AND_SOURCE_POINTER_CHECK_ONLY",
        "status": "BRIEF_PREPARED_NOT_RENDERED",
    })
    # Explicit field selection keeps project state, research and product facts out
    # of the scene request. The caller still must review the authored scene fields.
    packet["scene_request"] = None
    if mode == "GENERATIVE_SCENE":
        packet["scene_request"] = {
            "prompt": "\n".join([
                "Create only the environment layer.",
                f"Environment/action: {shot['scene']}",
                f"Camera/perspective: {shot['camera']}",
                f"Lighting/materials: {shot['light']}",
                f"Reserved negative space: {shot['negative_space']}",
                "Leave product insertion to later official-source compositing.",
                "Do not generate any product, logo, text, UI, technical diagram or evidence.",
                "Asset-specific prohibitions: " + "; ".join(packet["must_not_show"]),
            ]),
            "reference_sources": refs["scene"],
        }
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("brief", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(compile_brief(json.loads(args.brief.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f"BRIEF_INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
