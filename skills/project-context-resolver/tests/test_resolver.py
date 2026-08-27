from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills/project-context-resolver/scripts/resolve_project_context.py"
SPEC = importlib.util.spec_from_file_location("project_context_resolver", SCRIPT)
resolver = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(resolver)
AS_OF = date(2026, 8, 27)


def test_a_continue_s30_resolves_manifest_blocker_and_next_action():
    context = resolver.build_context(ROOT, "继续 S30 mini", as_of=AS_OF)

    assert context["project"]["project_id"] == "s30-mini"
    assert context["current_stage"]["gate_status"]["overall"] == "blocked"
    assert context["blocking_items"]
    assert context["next_valid_actions"][0]["action_id"] == "S30-P0-SOURCE-AUDIT"
    assert context["next_valid_actions"][0]["execution"] == "executable"
    assert "TASK_TYPE_DEFAULTED_TO_GTM_FOR_PROJECT_CONTINUATION" in context["warnings"]


def test_b_continue_s30_amazon_loads_only_amazon_context():
    context = resolver.build_context(ROOT, "继续 S30 mini Amazon", as_of=AS_OF)
    kinds = {item["kind"] for item in context["required_sources"]}

    assert context["task_type"] == "Amazon"
    assert kinds == {
        "manifest", "project_memory", "decisions", "product_truth",
        "approved_claims", "visual_context", "visual_profile", "visual_freeze", "assets",
    }
    assert "jp-commerce-content-flow" in context["relevant_skills"]["primary"]
    assert "amazon-japan-pdp-generator" in context["relevant_skills"]["optional"]
    assert "influencer-marketing" not in context["relevant_skills"]["primary"]
    assert "switchbot-campaign-review" not in context["relevant_skills"]["primary"]


def test_c_lock_ultra_max_context_has_no_s30_contamination():
    context = resolver.build_context(ROOT, "继续 Lock Ultra Max", as_of=AS_OF)
    serialized = yaml.safe_dump(context, allow_unicode=True)

    assert context["project"]["project_id"] == "lock-ultra-max"
    assert "s30-mini" not in serialized.casefold()
    assert "S30 mini" not in serialized


def test_d_formal_manifest_status_wins_on_accepted_decision_conflict(tmp_path: Path):
    project_dir = tmp_path / "projects/decision-conflict"
    memory_dir = tmp_path / "memory"
    project_dir.mkdir(parents=True)
    memory_dir.mkdir()
    (memory_dir / "PROJECT.md").write_text("# Context\n", encoding="utf-8")
    (memory_dir / "DECISIONS.md").write_text(
        "# Decisions\n\n### DEC-0001\n\n- Decision: Approve launch\n- Status: Accepted\n",
        encoding="utf-8",
    )
    manifest = {
        "manifest_version": "1.0",
        "project_id": "decision-conflict",
        "project_name": "Decision Conflict",
        "aliases": ["Conflict Project"],
        "manifest_updated_at": "2026-08-27T12:00:00+08:00",
        "state_as_of": "2026-08-27",
        "freshness_status": "current",
        "freshness_sources": ["../../memory/PROJECT.md", "../../memory/DECISIONS.md"],
        "market": "Japan",
        "status": "active",
        "lifecycle_stage": "validation",
        "sources": {
            "product_truth": None,
            "project_memory": "../../memory/PROJECT.md",
            "decisions": "../../memory/DECISIONS.md",
            "approved_claims": None,
            "visual_context": None,
            "visual_profile": None,
            "visual_freeze": None,
            "assets": None,
        },
        "current_phase": "gate_review",
        "gate_status": {"overall": "blocked", "product_truth": "blocked"},
        "approved": [],
        "blocking_items": [
            {
                "blocker_id": "TEST-BLOCKER",
                "summary": "Formal status remains blocked.",
                "status": "blocked",
                "source": "../../memory/PROJECT.md",
            }
        ],
        "latest_decision": {
            "status": "accepted",
            "decision_id": "DEC-0001",
            "summary": "Approve launch",
            "source": "../../memory/DECISIONS.md",
            "target_gate": "overall",
            "expected_status": "approved",
        },
        "next_actions": {
            "p0": [
                {
                    "action_id": "TEST-P0-RECONCILE",
                    "action": "Reconcile the formal status.",
                    "status": "ready_for_review",
                    "execution_class": "human_review_preparation",
                    "requires_human_approval": True,
                    "source": "../../memory/DECISIONS.md",
                }
            ],
            "p1": [],
            "p2": [],
        },
        "skills": {"primary": ["project-context-resolver"], "optional": []},
        "last_updated": "2026-08-27",
    }
    (project_dir / "project.yaml").write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    context = resolver.build_context(tmp_path, "继续 Conflict Project", as_of=AS_OF)

    assert context["current_stage"]["gate_status"]["overall"] == "blocked"
    assert any(item.startswith("FORMAL_STATUS_DECISION_CONFLICT") for item in context["warnings"])
    assert context["next_valid_actions"][0]["execution"] == "human_review_required"


def test_human_review_package_starts_blank(tmp_path: Path):
    context = resolver.build_context(ROOT, "继续 Lock Ultra Max", explicit_task_type="GTM", as_of=AS_OF)
    context["next_valid_actions"] = [
        {
            "action_id": "TEST-APPROVAL",
            "action": "Approve a test action.",
            "requires_human_approval": True,
            "execution": "human_review_required",
        }
    ]
    target = resolver.write_human_review(context, tmp_path)

    assert target is not None
    text = target.read_text(encoding="utf-8")
    assert "Execution: `NOT_EXECUTED`" in text
    assert 'decision: ""' in text
    assert 'reviewer: ""' in text


def test_all_checked_in_manifests_validate():
    result = resolver.validate_all(ROOT)

    assert result["status"] == "PASS", result
    assert len(result["manifests"]) == 4


def test_machine_schemas_parse_as_yaml():
    for name in ("project-manifest.schema.yaml", "project-context-package.schema.yaml"):
        value = yaml.safe_load((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        assert value["type"] == "object"


def test_review_and_customer_review_route_to_distinct_task_types():
    review = resolver.build_context(ROOT, "继续 S30 mini Review", as_of=AS_OF)
    voc = resolver.build_context(ROOT, "继续 S30 mini customer review", as_of=AS_OF)

    assert review["task_type"] == "Review"
    assert voc["task_type"] == "VOC"


def test_accepted_decision_without_gate_expectation_does_not_create_false_conflict(tmp_path: Path):
    project_dir = tmp_path / "projects/no-state-conflict"
    memory_dir = tmp_path / "memory"
    project_dir.mkdir(parents=True)
    memory_dir.mkdir()
    (memory_dir / "PROJECT.md").write_text("# Context\n", encoding="utf-8")
    (memory_dir / "DECISIONS.md").write_text(
        "# Decisions\n\n### DEC-0002\n\n- Decision: Approve naming\n- Status: Accepted\n",
        encoding="utf-8",
    )
    source_manifest = yaml.safe_load((ROOT / "projects/s30-mini/project.yaml").read_text(encoding="utf-8"))
    source_manifest.update({
        "project_id": "no-state-conflict",
        "project_name": "No State Conflict",
        "aliases": ["No State Conflict"],
        "alias_notes": {},
        "sources": {
            **source_manifest["sources"],
            "project_memory": "../../memory/PROJECT.md",
            "decisions": "../../memory/DECISIONS.md",
            "visual_context": None,
            "visual_profile": None,
            "visual_freeze": None,
        },
        "manifest_updated_at": "2026-08-27T12:00:00+08:00",
        "state_as_of": "2026-08-27",
        "freshness_status": "current",
        "freshness_sources": ["../../memory/PROJECT.md", "../../memory/DECISIONS.md"],
        "blocking_items": [],
        "latest_decision": {
            "status": "accepted",
            "decision_id": "DEC-0002",
            "summary": "Approve naming",
            "source": "../../memory/DECISIONS.md",
        },
        "next_actions": {"p0": [], "p1": [], "p2": []},
    })
    (project_dir / "project.yaml").write_text(
        yaml.safe_dump(source_manifest, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    context = resolver.build_context(tmp_path, "继续 No State Conflict", as_of=AS_OF)

    assert not any(item.startswith("FORMAL_STATUS_DECISION_CONFLICT") for item in context["warnings"])


def test_task_type_matching_is_token_aware_and_preserves_explicit_routes():
    cases = {
        "继续 S30 mini project": "GTM",
        "S30 mini product page": "GTM",
        "help with S30 mini": "GTM",
        "继续 S30 mini PR": "PR",
        "S30 mini PR TIMES 新闻稿": "PR",
        "继续 S30 mini Amazon": "Amazon",
    }

    for request, expected in cases.items():
        task_type, _ = resolver.infer_task_type(request)
        assert task_type == expected, request


def test_s20_alias_routes_to_s30_without_approving_a_product_name():
    context = resolver.build_context(ROOT, "继续 S20 mini Amazon", as_of=AS_OF)

    assert context["project"]["project_id"] == "s30-mini"
    assert context["project"]["routing_alias"] == "S20 mini"
    assert "does not approve an external product name" in context["project"]["routing_alias_note"]
    assert any(item.startswith("PROJECT_ROUTING_ALIAS_ONLY:S20 mini") for item in context["warnings"])


def test_unknown_project_returns_bootstrap_route_without_writes():
    project_path = ROOT / "projects/ai-mindclip"
    product_index = ROOT / "skills/product-knowledge/outputs/product_index.json"
    before_product_index = product_index.read_bytes()
    before_projects = sorted(path.name for path in (ROOT / "projects").iterdir())

    result = resolver.build_context(ROOT, "继续 AI MindClip", as_of=AS_OF)

    assert result == {
        "resolution_status": "PROJECT_BOOTSTRAP_REQUIRED",
        "request": "继续 AI MindClip",
        "recommended_skill": "project-memory-manager",
        "auto_create": False,
        "allowed_action": "prepare_project_discovery_review",
        "warnings": ["PROJECT_NOT_FOUND:NO_MANIFEST_MATCH"],
    }
    assert not project_path.exists()
    assert product_index.read_bytes() == before_product_index
    assert sorted(path.name for path in (ROOT / "projects").iterdir()) == before_projects
    assert "relevant_skills" not in result


def test_active_project_becomes_stale_after_threshold_but_read_only_audit_remains_allowed():
    context = resolver.build_context(ROOT, "继续 S30 mini", as_of=date(2026, 8, 28))

    assert context["freshness"]["effective_status"] == "stale"
    assert context["freshness"]["age_days"] == 8
    assert any(item.startswith("PROJECT_STATE_STALE:") for item in context["warnings"])
    assert context["next_valid_actions"][0]["execution_class"] == "read_only_audit"
    assert context["next_valid_actions"][0]["execution"] == "read_only_allowed_with_unverified_state"


def test_unknown_freshness_blocks_state_dependent_execution():
    manifest = {
        "blocking_items": [],
        "next_actions": {
            "p0": [{
                "action_id": "TEST-STATEFUL",
                "action": "Execute from current state.",
                "status": "not_started",
                "execution_class": "state_dependent_execution",
                "requires_human_approval": False,
                "source": "STATUS.md",
            }],
            "p1": [],
            "p2": [],
        },
    }

    action = resolver.select_next_action(manifest, "unknown")[0]

    assert action["execution"] == "blocked_by_freshness"


def test_unverified_state_allows_only_safe_action_classes():
    expected = {
        "read_only_audit": "read_only_allowed_with_unverified_state",
        "source_refresh": "read_only_allowed_with_unverified_state",
        "human_review_preparation": "human_review_preparation_allowed",
    }
    for execution_class, execution in expected.items():
        manifest = {
            "blocking_items": [],
            "next_actions": {
                "p0": [{
                    "action_id": "TEST-SAFE",
                    "action": "Prepare a safe action.",
                    "status": "not_started",
                    "execution_class": execution_class,
                    "requires_human_approval": execution_class == "human_review_preparation",
                    "source": "STATUS.md",
                }],
                "p1": [],
                "p2": [],
            },
        }

        action = resolver.select_next_action(manifest, "stale")[0]

        assert action["execution"] == execution
