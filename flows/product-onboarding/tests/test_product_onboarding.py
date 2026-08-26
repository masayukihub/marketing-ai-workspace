from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "flows/product-onboarding/scripts/run_product_onboarding.py"
GENERATED_AT = "2026-08-25T10:00:00+08:00"
CANONICAL_SOURCE_ID = "SRC-001"
IMMEDIATE_RAW_SOURCE_ID = "RAW-SYNTHETIC-SHEET"
FACT_SOURCE_ID = "DERIVED-SYNTHETIC-FACTS"
CLAIM_SOURCE_ID = "DERIVED-SYNTHETIC-CLAIMS"
CONFLICT_SOURCE_ID = "DERIVED-SYNTHETIC-CONFLICTS"


def load_runner():
    spec = importlib.util.spec_from_file_location("product_onboarding", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_runner()


def owner_root() -> Path:
    configured = os.environ.get("JP_COMMERCE_CREATIVE_FLOW_DIR")
    if configured:
        return Path(configured).resolve()
    for parent in [REPO_ROOT, *REPO_ROOT.parents]:
        candidate = parent / "jp-commerce-creative-flow"
        if candidate.is_dir():
            return candidate.resolve()
    raise AssertionError("jp-commerce-creative-flow checkout is required for contract tests")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_request(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_request(path: Path, payload: dict[str, Any]) -> None:
    write_json(path, payload)


def confirmed_input(reason: str) -> dict[str, Any]:
    return {
        "confirmed": True,
        "confirmed_by": "synthetic-test-owner",
        "confirmed_at": GENERATED_AT,
        "reason": reason,
    }


def source_definition(
    *,
    source_id: str,
    title: str,
    path: Path,
    raw_resource_type: str,
    normalized_source_type: str,
    mapping_rule: str,
    payload_shape: str,
    authority: str,
    packet_source_status: str,
    derived_from: list[str],
    original_uri: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "title": title,
        "path": str(path),
        "authority": authority,
        "original_uri": original_uri,
        "source_revision": "fixture-revision-1",
        "source_updated_at": GENERATED_AT,
        "extraction_status": "READ_SUCCESS",
        "allowed_use": "INTERNAL_FACT_PROPOSAL_ONLY",
        "raw_resource_type": raw_resource_type,
        "normalized_source_type": normalized_source_type,
        "mapping_rule": mapping_rule,
        "payload_shape": payload_shape,
        "packet_source_status": packet_source_status,
        "token": token,
        "derived_from": derived_from,
    }


def synthetic_request(
    tmp_path: Path,
    *,
    adapter: str = "LOCAL_FILE",
    blocked_primary: bool = False,
) -> Path:
    """Freeze one complete run envelope below a private runtime directory."""

    if adapter not in {"FEISHU_MCP", "LOCAL_FILE", "MANUAL_SNAPSHOT"}:
        raise AssertionError(f"unsupported synthetic adapter: {adapter}")
    if blocked_primary and adapter != "LOCAL_FILE":
        raise AssertionError("the blocked-primary case exercises local fallback")

    runtime = tmp_path / "private-runtime"
    inputs = runtime / "inputs"
    inputs.mkdir(parents=True)
    raw = inputs / "source-payload.json"
    if adapter == "FEISHU_MCP":
        write_json(
            raw,
            {
                "resource_type": "sheets",
                "content": {
                    "sheets": [{
                        "sheet_id": "sheet-1",
                        "range": "A1:B4",
                        "values": [
                            ["field", "value"],
                            ["name", "SYNTHETIC_PRODUCT_CANDIDATE"],
                            ["offer", "SYNTHETIC_TANK_OFFER"],
                            ["owner", "SYNTHETIC_TANK_DOCK"],
                        ],
                    }]
                },
            },
        )
        primary_source = source_definition(
            source_id=IMMEDIATE_RAW_SOURCE_ID,
            title="Synthetic Feishu connector response",
            path=raw,
            raw_resource_type="sheets",
            normalized_source_type="feishu_sheet",
            mapping_rule="sheets_collection_to_feishu_sheet",
            payload_shape="content.sheets[].values",
            authority="CANONICAL_SOURCE",
            packet_source_status="VERIFIED_READ",
            derived_from=[CANONICAL_SOURCE_ID],
            original_uri="https://example.invalid/feishu-sheet",
            token="synthetic-token",
        )
    elif adapter == "MANUAL_SNAPSHOT":
        write_json(
            raw,
            {
                "snapshot_type": "manual_fact_bundle",
                "facts": [{"field": "name", "value": "SYNTHETIC_PRODUCT_CANDIDATE"}],
                "confirmed_at": GENERATED_AT,
            },
        )
        primary_source = source_definition(
            source_id=IMMEDIATE_RAW_SOURCE_ID,
            title="Confirmed synthetic manual snapshot",
            path=raw,
            raw_resource_type="manual_snapshot",
            normalized_source_type="human_decision",
            mapping_rule="manual_snapshot_to_human_decision",
            payload_shape="manual_fact_bundle",
            authority="USER_PROVIDED",
            packet_source_status="PARTIAL",
            derived_from=[CANONICAL_SOURCE_ID],
        )
    else:
        # Saved Sheet export: deliberately not a Gateway/MCP response.
        write_json(
            raw,
            {
                "annotated_csv": (
                    "field,value\n"
                    "name,SYNTHETIC_PRODUCT_CANDIDATE\n"
                    "offer,SYNTHETIC_TANK_OFFER\n"
                    "owner,SYNTHETIC_TANK_DOCK\n"
                ),
                "actual_range": "sheet-1!A1:B4",
                "revision": "fixture-revision-1",
            },
        )
        primary_source = source_definition(
            source_id=IMMEDIATE_RAW_SOURCE_ID,
            title="Confirmed synthetic Feishu Sheet export",
            path=raw,
            raw_resource_type="feishu_sheet_export",
            normalized_source_type="feishu_sheet",
            mapping_rule="annotated_csv_export_to_feishu_sheet",
            payload_shape="annotated_csv",
            authority="CONFIRMED_FALLBACK" if blocked_primary else "CONFIRMED_LOCAL_INPUT",
            packet_source_status="PARTIAL",
            derived_from=[CANONICAL_SOURCE_ID],
            original_uri="https://example.invalid/feishu-sheet",
            token="synthetic-token",
        )

    facts = inputs / "facts.csv"
    write_csv(
        facts,
        ["Fact_ID", "Entity", "Field", "Value", "Unit", "Market", "Status", "Source_ID", "Evidence_Location", "Version"],
        [
            {
                "Fact_ID": "FACT-OFFER", "Entity": "S30 mini water-tank offer",
                "Field": "Offer", "Value": "SYNTHETIC_TANK_OFFER", "Unit": "",
                "Market": "JP", "Status": "Working", "Source_ID": CANONICAL_SOURCE_ID,
                "Evidence_Location": "sheet-1 row 3", "Version": "fixture-revision-1",
            },
            {
                "Fact_ID": "FACT-SIZE", "Entity": "S30 mini",
                "Field": "Robot dimensions", "Value": "SYNTHETIC_DIMENSION_PLACEHOLDER", "Unit": "",
                "Market": "Global", "Status": "Working", "Source_ID": CANONICAL_SOURCE_ID,
                "Evidence_Location": "sheet-1 row 2", "Version": "fixture-revision-1",
            },
            {
                "Fact_ID": "FACT-TANK-DOCK", "Entity": "S30 mini tank dock",
                "Field": "Tank dock capability", "Value": "SYNTHETIC_TANK_DOCK_CAPABILITY", "Unit": "",
                "Market": "JP", "Status": "Working", "Source_ID": CANONICAL_SOURCE_ID,
                "Evidence_Location": "sheet-1 row 4", "Version": "fixture-revision-1",
            },
        ],
    )
    claims = inputs / "claims.csv"
    write_csv(
        claims,
        ["Claim_ID", "Claim", "Market", "Claim_Status", "Fact_Status", "Source_ID", "Evidence_Location", "Conditions", "Prohibited_Use", "Version"],
        [
            {
                "Claim_ID": "CLM-SIZE", "Claim": "SYNTHETIC_SIZE_CLAIM_REQUIRES_REVIEW",
                "Market": "JP", "Claim_Status": "Conditional", "Fact_Status": "Confirmed",
                "Source_ID": CANONICAL_SOURCE_ID, "Evidence_Location": "sheet-1 row 2",
                "Conditions": "Exact dimensions and naming approval required",
                "Prohibited_Use": "No smallest claim", "Version": "fixture-revision-1",
            },
            {
                "Claim_ID": "CLM-WATER-STATION", "Claim": "SYNTHETIC_OTHER_OFFER_CAPABILITY",
                "Market": "JP", "Claim_Status": "Conditional", "Fact_Status": "Working",
                "Source_ID": CANONICAL_SOURCE_ID, "Evidence_Location": "sheet-1 row 4",
                "Conditions": "Water-station bundle only",
                "Prohibited_Use": "Do not attribute to tank dock", "Version": "fixture-revision-1",
            },
        ],
    )
    conflicts = inputs / "conflicts.csv"
    write_csv(
        conflicts,
        ["Issue_ID", "Type", "Priority", "Topic", "Observed_Evidence", "Impact", "Required_Resolution", "Suggested_Owner", "Status", "Source_ID"],
        [{
            "Issue_ID": "ISS-SYNTHETIC", "Type": "Gap", "Priority": "P0",
            "Topic": "Claim approval", "Observed_Evidence": "No approval record",
            "Impact": "External copy blocked", "Required_Resolution": "Human review",
            "Suggested_Owner": "PMM", "Status": "Open", "Source_ID": CANONICAL_SOURCE_ID,
        }],
    )
    source_index = inputs / "source_index.csv"
    write_csv(
        source_index,
        ["Source_ID", "Type", "Title", "URL", "Verification_Status", "Updated_At"],
        [{
            "Source_ID": CANONICAL_SOURCE_ID, "Type": "Feishu Sheet",
            "Title": "Synthetic canonical product source",
            "URL": "https://example.invalid/feishu-sheet",
            "Verification_Status": "Pending Verification", "Updated_At": GENERATED_AT,
        }],
    )

    derivative_sources = [
        source_definition(
            source_id=FACT_SOURCE_ID, title="Synthetic Product Knowledge fact candidates",
            path=facts, raw_resource_type="derived_artifact",
            normalized_source_type="product_knowledge",
            mapping_rule="derived_artifact_to_product_knowledge", payload_shape="file_bytes",
            authority="DERIVED_ARTIFACT", packet_source_status="PARTIAL",
            derived_from=[CANONICAL_SOURCE_ID],
        ),
        source_definition(
            source_id=CLAIM_SOURCE_ID, title="Synthetic Product Knowledge claim candidates",
            path=claims, raw_resource_type="derived_artifact",
            normalized_source_type="product_knowledge",
            mapping_rule="derived_artifact_to_product_knowledge", payload_shape="file_bytes",
            authority="DERIVED_ARTIFACT", packet_source_status="PARTIAL",
            derived_from=[CANONICAL_SOURCE_ID],
        ),
        source_definition(
            source_id=CONFLICT_SOURCE_ID, title="Synthetic conflict and missing register",
            path=conflicts, raw_resource_type="derived_artifact",
            normalized_source_type="product_knowledge",
            mapping_rule="derived_artifact_to_product_knowledge", payload_shape="file_bytes",
            authority="DERIVED_ARTIFACT", packet_source_status="PARTIAL",
            derived_from=[CANONICAL_SOURCE_ID],
        ),
    ]

    requested_adapter = "FEISHU_MCP" if blocked_primary else adapter
    input_confirmation = (
        confirmed_input(f"Synthetic {adapter} input is explicitly accepted for this test run")
        if adapter in {"LOCAL_FILE", "MANUAL_SNAPSHOT"} else None
    )
    fallback_confirmation = (
        confirmed_input("Feishu access is blocked; this frozen local export is approved as fallback")
        if blocked_primary else None
    )
    request: dict[str, Any] = {
        "request_version": "1.0",
        "run_id": "S30-SYNTHETIC-001",
        "generated_at": GENERATED_AT,
        "scope": {
            "project_id": "s30-mini", "product_id": "s30-mini", "market": "JP",
            "locale": "ja-JP", "channel": "Amazon.co.jp", "offer": "水箱版のみ",
        },
        "entity_registry": {
            "product_id": "s30-mini", "tank_dock_product_id": "s30-mini-tank-dock",
            "offer_id": "s30-mini-water-tank-offer",
        },
        "product_knowledge_source_priorities": {CANONICAL_SOURCE_ID: "P1"},
        "acquisition": {
            "requested_adapter": requested_adapter,
            "adapter_status": "BLOCKED" if blocked_primary else "SUCCESS",
            "attempted_at": GENERATED_AT,
            "blocked_code": "MISSING_SCOPE" if blocked_primary else None,
            "blocked_reason": "Connector lacks required scope" if blocked_primary else None,
            "effective_adapter": adapter,
            "input_confirmation": input_confirmation,
            "fallback_confirmation": fallback_confirmation,
        },
        "product": {
            "name": "SYNTHETIC S30 MINI PRODUCT CANDIDATE", "official_name_ja": None,
            "category": "SYNTHETIC_CATEGORY", "status": "CONDITIONAL",
            "source_refs": [IMMEDIATE_RAW_SOURCE_ID],
        },
        "sources": [primary_source, *derivative_sources],
        "tables": {
            "facts": str(facts), "claims": str(claims), "conflicts": str(conflicts),
            "source_index": str(source_index), "fact_source_id": FACT_SOURCE_ID,
            "claim_source_id": CLAIM_SOURCE_ID, "conflict_source_id": CONFLICT_SOURCE_ID,
        },
        "selection": {
            "facts": [
                {
                    "fact_id": "FACT-OFFER", "section": "sku_offers", "label": "水箱版オファー",
                    "status": "CONDITIONAL", "scope": "水箱版のみ",
                    "conditions": ["Formal SKU and BOM remain pending"],
                    "source_refs": [FACT_SOURCE_ID],
                    "subject_product_id": "s30-mini-water-tank-offer",
                    "capability_owner_product_id": "s30-mini-water-tank-offer",
                    "required_product_id": "s30-mini-tank-dock", "entity_scope": "OFFER",
                },
                {
                    "fact_id": "FACT-SIZE", "section": "specifications", "label": "本体サイズ",
                    "status": "CONDITIONAL", "scope": "水箱版のみ",
                    "conditions": ["Global engineering input; JP applicability requires review"],
                    "source_refs": [FACT_SOURCE_ID], "subject_product_id": "s30-mini",
                    "capability_owner_product_id": "s30-mini", "required_product_id": None,
                    "entity_scope": "PRODUCT",
                },
                {
                    "fact_id": "FACT-TANK-DOCK", "section": "specifications", "label": "水箱ドック機能",
                    "status": "CONDITIONAL", "scope": "水箱版のみ",
                    "conditions": ["Requires S30 mini robot; human review remains open"],
                    "source_refs": [FACT_SOURCE_ID], "subject_product_id": "s30-mini-tank-dock",
                    "capability_owner_product_id": "s30-mini-tank-dock",
                    "required_product_id": "s30-mini", "entity_scope": "TANK_DOCK",
                },
            ],
            "claim_ids": ["CLM-SIZE", "CLM-WATER-STATION"],
            "claim_overrides": {
                "CLM-SIZE": {"source_refs": [CLAIM_SOURCE_ID]},
                "CLM-WATER-STATION": {
                    "source_refs": [CLAIM_SOURCE_ID], "out_of_offer_scope": True,
                },
            },
        },
        "unknown_tbd": [{
            "id": "TBD-SKU", "question": "What is the final JP SKU?",
            "owner": None, "deadline": None, "blocks": ["External PDP"],
        }],
        "additional_findings": [],
    }
    request_path = runtime / "request.json"
    save_request(request_path, request)
    return request_path


def run_synthetic(request_path: Path) -> dict[str, Any]:
    # The implementation correctly records a dirty checkout as PARTIAL.  Unit
    # tests exercise the clean, review-ready branch independently of whatever
    # uncommitted implementation work exists in the developer worktree.
    commit = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        env=RUNNER.isolated_git_env(),
    ).stdout.strip()
    original = RUNNER.git_provenance
    RUNNER.git_provenance = lambda _repo_root: (commit, False)
    try:
        return RUNNER.run(request_path, request_path.parent, REPO_ROOT, None)
    finally:
        RUNNER.git_provenance = original


def selected_fact(payload: dict[str, Any], fact_id: str) -> dict[str, Any]:
    return next(item for item in payload["selection"]["facts"] if item["fact_id"] == fact_id)


def test_contracts_are_valid_json_schemas() -> None:
    for name in ("source-snapshot.schema.json", "review-decision.schema.json", "run-manifest.schema.json"):
        schema = json.loads((REPO_ROOT / "contracts" / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_ready_manifest_contract_rejects_dirty_workspace(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path)
    manifest = run_synthetic(request)
    assert manifest["final_state"] == "P0_1_READY_FOR_REVIEW"
    manifest["execution"]["workspace_dirty"] = True
    schema = json.loads(
        (REPO_ROOT / "contracts/run-manifest.schema.json").read_text(encoding="utf-8")
    )
    errors = list(Draft202012Validator(schema).iter_errors(manifest))
    assert any(
        list(error.absolute_path)[-2:] == ["execution", "workspace_dirty"]
        or "False was expected" in error.message
        for error in errors
    )


def test_locked_external_schema_reference_matches_owner() -> None:
    reference = json.loads((REPO_ROOT / "contracts/product-truth-schema-reference.json").read_text(encoding="utf-8"))
    owner = owner_root()
    schema_path = owner / reference["schema"]["path"]
    assert RUNNER.sha256_file(schema_path) == reference["schema"]["sha256"]
    assert json.loads(schema_path.read_text(encoding="utf-8"))["$id"] == reference["schema"]["$id"]
    commit = subprocess.run(
        ["git", "-C", str(owner), "rev-parse", "HEAD"], check=True,
        capture_output=True, text=True, env=RUNNER.isolated_git_env(),
    ).stdout.strip()
    assert commit == reference["ownership"]["locked_commit"]


def test_external_owner_resolution_ignores_inherited_git_hook_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_git_dir = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--absolute-git-dir"],
        check=True,
        capture_output=True,
        text=True,
        env=RUNNER.isolated_git_env(),
    ).stdout.strip()
    monkeypatch.setenv("GIT_DIR", current_git_dir)
    reference = json.loads(
        (REPO_ROOT / "contracts/product-truth-schema-reference.json").read_text(
            encoding="utf-8"
        )
    )
    resolved_owner, schema_path, commit = RUNNER.resolve_schema_owner(
        REPO_ROOT, reference, None
    )
    assert resolved_owner == owner_root()
    assert schema_path == resolved_owner / reference["schema"]["path"]
    assert commit == reference["ownership"]["locked_commit"]


def test_ready_package_is_traceable_deterministic_and_bounded(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path)
    runtime = request.parent
    first_manifest = run_synthetic(request)
    expected_outputs = set(RUNNER.OUTPUT_NAMES.values()) | {"run-manifest.json"}
    first_bytes = {name: (runtime / name).read_bytes() for name in expected_outputs}
    second_manifest = run_synthetic(request)
    assert first_manifest == second_manifest
    assert first_bytes == {name: (runtime / name).read_bytes() for name in expected_outputs}
    assert {path.name for path in runtime.iterdir()} == expected_outputs | {"request.json", "inputs"}
    assert first_manifest["final_state"] == "P0_1_READY_FOR_REVIEW"
    assert first_manifest["current_gate"] == "PRODUCT_TRUTH_HUMAN_REVIEW_GATE"
    assert set(first_manifest["execution"]["inputs_sha256"]) == {
        f"inputs/{path.name}" for path in (runtime / "inputs").iterdir()
    }

    packet = json.loads((runtime / "product-truth-proposal.json").read_text(encoding="utf-8"))
    assert packet["approved_claims"] == []
    assert not ({"locale", "channel", "gate", "proposal_status"} & set(packet))
    out_of_scope = next(item for item in packet["unapproved_claims"] if item["id"] == "CLM-WATER-STATION")
    assert out_of_scope["status"] == "PROHIBITED"
    queue = json.loads((runtime / "claim-human-review-queue.json").read_text(encoding="utf-8"))
    assert all(item["decision"] == "PENDING" for item in queue["items"])
    assert all(item["decision_effect"]["external_claim_approval"] is False for item in queue["items"])
    review_html = (runtime / "product-truth-review.html").read_text(encoding="utf-8")
    assert "INTERNAL REVIEW / NOT APPROVED / NOT PDP" in review_html
    assert "PRODUCT_TRUTH_HUMAN_REVIEW_GATE" in review_html


def test_every_request_and_input_is_frozen_below_private_runtime(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path)
    payload = read_request(request)
    assert request.parent.name == "private-runtime"
    for source in payload["sources"]:
        assert Path(source["path"]).resolve().is_relative_to((request.parent / "inputs").resolve())
    for key in ("facts", "claims", "conflicts", "source_index"):
        assert Path(payload["tables"][key]).resolve().is_relative_to((request.parent / "inputs").resolve())


def test_source_or_table_outside_runtime_inputs_is_blocked(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path)
    payload = read_request(request)
    escaped = tmp_path / "not-frozen.csv"
    escaped.write_text("Fact_ID\nFACT-ESCAPED\n", encoding="utf-8")
    payload["tables"]["facts"] = str(escaped)
    save_request(request, payload)
    with pytest.raises(RUNNER.FlowError, match="private inputs directory|frozen under"):
        run_synthetic(request)


def test_blocked_feishu_preserved_when_confirmed_fallback_is_used(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path, adapter="LOCAL_FILE", blocked_primary=True)
    manifest = run_synthetic(request)
    snapshot = json.loads((request.parent / "source-snapshot.json").read_text(encoding="utf-8"))
    assert snapshot["status"] == "PARTIAL"
    assert snapshot["acquisition"]["adapter_status"] == "BLOCKED"
    assert snapshot["acquisition"]["fallback_used"] is True
    assert snapshot["acquisition"]["input_confirmation"]["confirmed"] is True
    assert snapshot["errors"][0]["code"] == "MISSING_SCOPE"
    assert manifest["source_access"]["feishu_mcp_status"] == "BLOCKED"
    assert manifest["source_access"]["confirmed_fallback_used"] is True
    assert manifest["source_access"]["input_confirmation_present"] is True
    assert manifest["final_state"] == "P0_1_READY_FOR_REVIEW"


def test_successful_feishu_mcp_handoff_uses_actual_connector_payload(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path, adapter="FEISHU_MCP")
    manifest = run_synthetic(request)
    snapshot = json.loads((request.parent / "source-snapshot.json").read_text(encoding="utf-8"))
    primary = next(item for item in snapshot["sources"] if item["source_id"] == IMMEDIATE_RAW_SOURCE_ID)
    assert snapshot["status"] == "COMPLETE"
    assert primary["adapter_mapping"]["raw_resource_type"] == "sheets"
    assert primary["adapter_mapping"]["payload_shape"] == "content.sheets[].values"
    assert snapshot["acquisition"]["input_confirmation"] is None
    assert manifest["source_access"]["feishu_mcp_status"] == "SUCCESS"
    assert manifest["source_access"]["effective_adapter"] == "FEISHU_MCP"
    assert manifest["source_access"]["confirmed_fallback_used"] is False
    gateway = next(
        item for item in manifest["locked_dependencies"]
        if item["component"] == "feishu-read-gateway-mcp"
    )
    assert gateway["verification_status"] == "NOT_USED"
    assert "frozen connector response" in gateway["verification_basis"]
    assert "BLOCKED result" not in gateway["verification_basis"]


def test_confirmed_local_file_uses_honest_annotated_export_shape(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path, adapter="LOCAL_FILE")
    manifest = run_synthetic(request)
    snapshot = json.loads((request.parent / "source-snapshot.json").read_text(encoding="utf-8"))
    primary = next(item for item in snapshot["sources"] if item["source_id"] == IMMEDIATE_RAW_SOURCE_ID)
    assert primary["adapter_mapping"] == {
        "raw_resource_type": "feishu_sheet_export",
        "normalized_source_type": "feishu_sheet",
        "mapping_rule": "annotated_csv_export_to_feishu_sheet",
        "payload_shape": "annotated_csv",
        "payload_ref": str((request.parent / "inputs/source-payload.json").resolve()),
    }
    assert snapshot["acquisition"]["input_confirmation"]["confirmed"] is True
    assert manifest["source_access"]["feishu_mcp_status"] == "NOT_REQUESTED"


def test_confirmed_manual_snapshot_handoff_is_supported_without_feishu_claim(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path, adapter="MANUAL_SNAPSHOT")
    manifest = run_synthetic(request)
    packet = json.loads((request.parent / "product-truth-proposal.json").read_text(encoding="utf-8"))
    snapshot = json.loads((request.parent / "source-snapshot.json").read_text(encoding="utf-8"))
    primary = next(item for item in snapshot["sources"] if item["source_id"] == IMMEDIATE_RAW_SOURCE_ID)
    assert manifest["source_access"]["feishu_mcp_status"] == "NOT_REQUESTED"
    assert manifest["source_access"]["effective_adapter"] == "MANUAL_SNAPSHOT"
    assert manifest["source_access"]["input_confirmation_present"] is True
    assert primary["authority"] == "USER_PROVIDED"
    assert primary["adapter_mapping"]["raw_resource_type"] == "manual_snapshot"
    packet_source = next(item for item in packet["sources"] if item["id"] == IMMEDIATE_RAW_SOURCE_ID)
    assert packet_source["source_type"] == "human_decision"
    assert packet_source["status"] == "PARTIAL"


def test_manual_snapshot_cannot_spoof_verified_feishu_read(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path, adapter="MANUAL_SNAPSHOT")
    payload = read_request(request)
    raw = request.parent / "inputs/source-payload.json"
    write_json(raw, {
        "resource_type": "sheets",
        "content": {"sheets": [{"sheet_id": "sheet-1", "values": [["a", "b"]]}]},
    })
    payload["sources"][0].update({
        "authority": "CANONICAL_SOURCE", "raw_resource_type": "sheets",
        "normalized_source_type": "feishu_sheet",
        "mapping_rule": "sheets_collection_to_feishu_sheet",
        "payload_shape": "content.sheets[].values", "packet_source_status": "VERIFIED_READ",
    })
    save_request(request, payload)
    with pytest.raises(RUNNER.FlowError, match="cannot impersonate|MANUAL_SNAPSHOT"):
        run_synthetic(request)


def test_adapter_declared_payload_shape_mismatch_is_blocked(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path, adapter="LOCAL_FILE")
    payload = read_request(request)
    write_json(Path(payload["sources"][0]["path"]), {
        "resource_type": "sheets",
        "content": {"sheets": [{"sheet_id": "sheet-1", "values": [["a", "b"]]}]},
    })
    with pytest.raises(RUNNER.FlowError, match="annotated Feishu Sheet export shape"):
        run_synthetic(request)


def test_blocked_feishu_without_fallback_fails_closed(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path, adapter="LOCAL_FILE", blocked_primary=True)
    payload = read_request(request)
    payload["acquisition"].update({
        "effective_adapter": None, "input_confirmation": None, "fallback_confirmation": None,
    })
    save_request(request, payload)
    with pytest.raises(RUNNER.FlowError, match="no confirmed fallback"):
        run_synthetic(request)


def test_missing_canonical_pointer_breaks_source_lineage(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path)
    payload = read_request(request)
    payload["sources"][1]["derived_from"] = ["SRC-999"]
    save_request(request, payload)
    with pytest.raises(RUNNER.FlowError, match="unregistered upstream lineage|SRC-999"):
        run_synthetic(request)


def test_project_priority_p0_cannot_impersonate_product_knowledge_source_priority(
    tmp_path: Path,
) -> None:
    request = synthetic_request(tmp_path)
    payload = read_request(request)
    payload["product_knowledge_source_priorities"][CANONICAL_SOURCE_ID] = "P0"
    save_request(request, payload)
    with pytest.raises(RUNNER.FlowError, match="Product Knowledge source priority|P1-P5"):
        run_synthetic(request)


def test_dangling_fact_upstream_reference_is_blocked(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path)
    payload = read_request(request)
    selected_fact(payload, "FACT-SIZE")["upstream_source_refs"] = ["SRC-999"]
    save_request(request, payload)
    with pytest.raises(RUNNER.FlowError, match="unknown|unregistered|SRC-999"):
        run_synthetic(request)


def test_tank_dock_capability_owner_and_required_product_are_preserved(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path)
    run_synthetic(request)
    proposal = json.loads((request.parent / "product-knowledge-change-proposal.json").read_text(encoding="utf-8"))
    tank_fact = next(item for item in proposal["facts"] if item["proposal_fact_id"] == "FACT-TANK-DOCK")
    assert tank_fact["entity_scope"] == "TANK_DOCK"
    assert tank_fact["subject_product_id"] == "s30-mini-tank-dock"
    assert tank_fact["capability_owner_product_id"] == "s30-mini-tank-dock"
    assert tank_fact["required_product_id"] == "s30-mini"
    assert tank_fact["immediate_source_refs"] == [FACT_SOURCE_ID]
    assert tank_fact["upstream_source_refs"] == [CANONICAL_SOURCE_ID]


def test_tank_dock_capability_cannot_be_owned_by_robot(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path)
    payload = read_request(request)
    selected_fact(payload, "FACT-TANK-DOCK")["capability_owner_product_id"] = "s30-mini"
    save_request(request, payload)
    with pytest.raises(RUNNER.FlowError, match="TANK_DOCK|capability owner|ownership"):
        run_synthetic(request)


def test_global_fact_is_not_silently_promoted_to_confirmed_jp_fact(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path)
    run_synthetic(request)
    proposal = json.loads((request.parent / "product-knowledge-change-proposal.json").read_text(encoding="utf-8"))
    size_fact = next(item for item in proposal["facts"] if item["proposal_fact_id"] == "FACT-SIZE")
    assert size_fact["source_market"] == "Global"
    assert size_fact["market"] == "JP"
    assert size_fact["market_applicability"] == "needs_jp_verification"
    assert size_fact["packet_status"] != "CONFIRMED"

    negative = synthetic_request(tmp_path / "negative")
    payload = read_request(negative)
    selected_fact(payload, "FACT-SIZE")["status"] = "CONFIRMED"
    save_request(negative, payload)
    with pytest.raises(RUNNER.FlowError, match="Global/non-JP fact|silently confirmed"):
        run_synthetic(negative)


def test_missing_price_with_currency_unit_remains_json_null() -> None:
    item = RUNNER.make_fact_item(
        {
            "fact_id": "FACT-PRICE-UNKNOWN",
            "label": "Amazon.co.jp price",
            "value": None,
            "status": "UNKNOWN",
            "scope": "水箱版のみ",
            "conditions": ["No approved current price is available"],
            "source_refs": [FACT_SOURCE_ID],
        },
        {"Unit": "JPY", "Status": "Unverified"},
    )
    assert item["value"] is None


def test_runtime_inside_repository_is_blocked(tmp_path: Path) -> None:
    request = synthetic_request(tmp_path)
    with pytest.raises(RUNNER.FlowError, match="outside the Git repository"):
        RUNNER.run(request, REPO_ROOT / ".private-test-runtime", REPO_ROOT, None)


def test_runtime_inside_another_git_repository_or_installed_skill_is_blocked(
    tmp_path: Path,
) -> None:
    other_repo = tmp_path / "other-repo"
    (other_repo / ".git").mkdir(parents=True)
    with pytest.raises(RUNNER.FlowError, match="any Git repository"):
        RUNNER.assert_private_runtime(other_repo / "private-runtime", REPO_ROOT)
    with pytest.raises(RUNNER.FlowError, match="installed Skill|canonical knowledge"):
        RUNNER.assert_private_runtime(
            Path.home() / ".codex/skills/product-knowledge/runtime", REPO_ROOT
        )


def test_gateway_and_local_sheet_mapping_contracts_are_explicit() -> None:
    schema = json.loads((REPO_ROOT / "contracts/source-snapshot.schema.json").read_text(encoding="utf-8"))
    mapping_schema = schema["$defs"]["adapter_mapping"]
    gateway = {
        "raw_resource_type": "sheets", "normalized_source_type": "feishu_sheet",
        "mapping_rule": "sheets_collection_to_feishu_sheet",
        "payload_shape": "content.sheets[].values",
        "payload_ref": "/private/runtime/inputs/feishu-response.json",
    }
    local_export = {
        "raw_resource_type": "feishu_sheet_export", "normalized_source_type": "feishu_sheet",
        "mapping_rule": "annotated_csv_export_to_feishu_sheet", "payload_shape": "annotated_csv",
        "payload_ref": "/private/runtime/inputs/saved-export.json",
    }
    Draft202012Validator(mapping_schema).validate(gateway)
    Draft202012Validator(mapping_schema).validate(local_export)
    invalid = dict(local_export, mapping_rule="sheets_collection_to_feishu_sheet")
    assert list(Draft202012Validator(mapping_schema).iter_errors(invalid))


def test_manual_snapshot_mapping_contract_cannot_claim_feishu_shape() -> None:
    schema = json.loads((REPO_ROOT / "contracts/source-snapshot.schema.json").read_text(encoding="utf-8"))
    mapping_schema = schema["$defs"]["adapter_mapping"]
    invalid = {
        "raw_resource_type": "manual_snapshot", "normalized_source_type": "feishu_sheet",
        "mapping_rule": "sheets_collection_to_feishu_sheet",
        "payload_shape": "content.sheets[].values",
        "payload_ref": "/private/runtime/inputs/manual.json",
    }
    assert list(Draft202012Validator(mapping_schema).iter_errors(invalid))
