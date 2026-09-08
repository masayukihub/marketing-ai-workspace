from __future__ import annotations

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from consolidate_codex_skill_surface import (  # noqa: E402
    apply_moves,
    build_plan,
    build_restore_plan,
    journal_for_moves,
    load_surface,
    path_present,
    user_entry_check,
)


SURFACE_PATH = ROOT / "runtime/skill-surface.yaml"
EXPECTED_USER_ENTRIES = {
    "jp-commerce-insights",
    "jp-commerce-content-flow",
    "switchbot-japan-campaign",
    "switchbot-japan-edm",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_surface_has_exactly_four_chinese_user_entries():
    surface = load_surface(SURFACE_PATH)
    assert {item["skill_id"] for item in surface["user_entries"]} == EXPECTED_USER_ENTRIES
    assert all(any("\u4e00" <= char <= "\u9fff" for char in item["display_name"]) for item in surface["user_entries"])


def test_every_internalized_entry_routes_to_one_user_entry():
    surface = load_surface(SURFACE_PATH)
    names = [item["directory_name"] for item in surface["internalized_entries"]]
    assert len(names) == len(set(names))
    assert all(item["canonical_entry"] in EXPECTED_USER_ENTRIES for item in surface["internalized_entries"])
    assert "amazon-voc-browser-scraper" in names
    assert "amazon-review-scraper" in names
    assert "japan-listing-demo" in names


def test_primary_entry_ui_metadata_is_chinese_and_invokable():
    for skill_id in EXPECTED_USER_ENTRIES:
        metadata = load_yaml(ROOT / f"skills/{skill_id}/agents/openai.yaml")
        interface = metadata["interface"]
        assert any("\u4e00" <= char <= "\u9fff" for char in interface["display_name"])
        assert any("\u4e00" <= char <= "\u9fff" for char in interface["short_description"])
        assert any("\u4e00" <= char <= "\u9fff" for char in interface["default_prompt"])
        assert 25 <= len(interface["short_description"]) <= 64
        assert f"${skill_id}" in interface["default_prompt"]
        assert metadata["policy"]["allow_implicit_invocation"] is True


def test_surface_move_is_reversible_and_preserves_symlink(tmp_path: Path):
    surface = load_surface(SURFACE_PATH)
    codex_home = tmp_path / "codex"
    project_root = tmp_path / "workspace"
    for item in surface["user_entries"]:
        (codex_home / "skills" / item["skill_id"]).mkdir(parents=True)

    global_source = codex_home / "skills/ecommerce-product-selection"
    global_source.mkdir()
    (global_source / "SKILL.md").write_text("runtime\n", encoding="utf-8")

    target_runtime = tmp_path / "source-runtime"
    target_runtime.mkdir()
    project_source = project_root / ".agents/skills/japan-listing-demo"
    project_source.parent.mkdir(parents=True)
    project_source.symlink_to(target_runtime, target_is_directory=True)

    plan = build_plan(surface, codex_home, project_root)
    selected = [row for row in plan if row["action"] == "MOVE"]
    assert {(row["scope"], row["directory_name"]) for row in selected} == {
        ("codex_global", "ecommerce-product-selection"),
        ("project", "japan-listing-demo"),
    }
    assert user_entry_check(surface, codex_home) == []
    assert apply_moves(plan) == 2
    assert path_present(codex_home / "internal-skills/ecommerce-product-selection")
    moved_link = project_root / ".agents/internal-skills/japan-listing-demo"
    assert moved_link.is_symlink()
    assert moved_link.resolve() == target_runtime.resolve()

    restore_plan = build_restore_plan(
        surface,
        codex_home,
        project_root,
        journal_for_moves(plan),
    )
    assert apply_moves(restore_plan) == 2
    assert path_present(global_source)
    assert project_source.is_symlink()


def test_restore_plan_only_contains_entries_recorded_by_apply_journal(tmp_path: Path):
    surface = load_surface(SURFACE_PATH)
    codex_home = tmp_path / "codex"
    discovery = codex_home / "skills/ecommerce-product-selection"
    discovery.mkdir(parents=True)
    preexisting_internal = codex_home / "internal-skills/amazon-keyword-miner"
    preexisting_internal.mkdir(parents=True)

    forward = build_plan(surface, codex_home, project_root=None)
    moved_rows = [row for row in forward if row["action"] == "MOVE"]
    assert [row["directory_name"] for row in moved_rows] == ["ecommerce-product-selection"]
    apply_moves(forward)

    journal = journal_for_moves(forward)
    restore = build_restore_plan(surface, codex_home, project_root=None, journal=journal)
    assert [row["directory_name"] for row in restore] == ["ecommerce-product-selection"]
    assert restore[0]["status"] == "READY_TO_RESTORE"
    assert all(row["directory_name"] != "amazon-keyword-miner" for row in restore)


def test_feature_branch_cannot_apply_surface_change():
    text = (ROOT / "scripts/consolidate_codex_skill_surface.py").read_text(encoding="utf-8")
    assert "SURFACE_APPLY_REQUIRES_MAIN_BRANCH" in text
    assert "SURFACE_APPLY_REQUIRES_CLEAN_WORKTREE" in text
    assert "SURFACE_APPLY_REQUIRES_SYNCED_GLOBAL_RUNTIME" in text
    assert ".unlink(" not in text
    assert "rmtree(" not in text


def test_surface_records_runtime_drift_without_promoting_it():
    surface = load_surface(SURFACE_PATH)
    drift = surface["known_capability_drift"]
    assert drift == [{
        "capability": "visual_reference_inbox_executable",
        "repository_status": "SCHEMA_ONLY_RUNTIME_NOT_REGISTERED",
        "legacy_global_status": "CLAIMED_BY_UNVERIFIED_MIRROR",
        "decision": "DO_NOT_SYNC_AS_WORKING_FEATURE",
        "fallback": "BLOCKED_RUNTIME_MISSING",
    }]


def test_surface_user_entries_match_operator_routing():
    surface = load_surface(SURFACE_PATH)
    routing = load_yaml(ROOT / "operator/task-routing.yaml")
    expected_labels = {item["skill_id"]: item["display_name"] for item in surface["user_entries"]}
    actual_labels = {key: value["label"] for key, value in routing["user_entries"].items()}
    assert actual_labels == expected_labels


def test_exact_legacy_alias_precedes_generic_keywords():
    routing = load_yaml(ROOT / "operator/task-routing.yaml")
    assert routing["routing_precedence"] == [
        "continuation_existing_project",
        "exact_legacy_alias",
        "semantic_route",
    ]
    aliases = routing["legacy_aliases"]
    assert aliases["Amazon Listing Asset Capture"] == {
        "primary_entry": "$jp-commerce-insights",
        "mode": "ASSET_CAPTURE",
    }
    assert aliases["Amazon Japan PDP Generator"]["primary_entry"] == "$jp-commerce-content-flow"
    assert aliases["Japan Listing Demo"]["mode"] == "RESUME"
    surface = load_surface(SURFACE_PATH)
    for item in surface["internalized_entries"]:
        assert item["directory_name"] in aliases
        assert item["declared_skill_name"] in aliases


def test_surface_contracts_do_not_contain_machine_absolute_paths():
    paths = [
        SURFACE_PATH,
        ROOT / "skills/jp-commerce-insights/references/internal-components.md",
        ROOT / "skills/jp-commerce-content-flow/references/internal-components.md",
    ]
    forbidden = ("/" + "Users" + "/", "/" + "home" + "/")
    assert all(not any(prefix in path.read_text(encoding="utf-8") for prefix in forbidden) for path in paths)
