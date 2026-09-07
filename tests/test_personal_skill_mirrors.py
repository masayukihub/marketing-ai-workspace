"""Synthetic, offline tests. No user catalog or external service is modified."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_personal_skill_mirrors import audit
from runtime_contract import RuntimeContractError, repository_file_hashes, tree_hash


class PersonalMirrorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "repo"
        self.source = self.workspace / "skills/demo"
        self.source.mkdir(parents=True)
        (self.source / "SKILL.md").write_text("---\nname: demo\ndescription: Demo task\n---\nKeep facts locked.\n")
        (self.source / "agents").mkdir()
        (self.source / "agents/openai.yaml").write_text(
            "interface:\n  display_name: Demo\n  default_prompt: Use $demo\n"
            "policy:\n  allow_implicit_invocation: true\n")
        subprocess.run(["git", "init", "-q", str(self.workspace)], check=True)
        subprocess.run(["git", "-C", str(self.workspace), "add", "skills"], check=True)
        self.lock_path = self.workspace / "lock.json"
        self.refresh_lock()
        self.catalog = self.root / "personal"
        self.catalog.mkdir()
        self.target = self.catalog / "skill-example-id"

    def refresh_lock(self):
        hashes = repository_file_hashes(self.workspace, "skills/demo")
        self.lock_path.write_text(json.dumps({
            "lock_version": "1.0", "runtime_authority": "repository", "skills": [{
                "name": "demo", "repository_path": "skills/demo", "user_visible": True,
                "repository_tree_hash": tree_hash(hashes), "required_runtime_files": ["SKILL.md"],
            }],
        }))

    def install(self):
        shutil.copytree(self.source, self.target)

    def result(self):
        return audit(self.workspace, self.lock_path, self.catalog)

    def status(self):
        return self.result()["skills"][0]["status"]

    def test_missing(self):
        self.assertEqual(self.status(), "PERSONAL_ENTRY_MISSING")

    def test_resolve_by_frontmatter_and_no_writes(self):
        self.install()
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.target.rglob("*") if p.is_file()}
        result = self.result()
        self.assertEqual(result["status"], "PERSONAL_ENTRIES_IN_SYNC")
        self.assertFalse(result["runtime_execution_verified"])
        self.assertFalse(result["writes_performed"])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})

    def test_instruction_drift(self):
        self.install()
        with (self.target / "SKILL.md").open("a") as handle:
            handle.write("Changed instruction.\n")
        self.assertEqual(self.status(), "PERSONAL_ENTRY_DRIFT")

    def test_extra_script_not_ignored(self):
        self.install()
        (self.target / "extra.py").write_text("print('unexpected')\n")
        self.assertEqual(self.status(), "PERSONAL_ENTRY_DRIFT")

    def test_duplicate_and_disabled_entries(self):
        self.install()
        duplicate = self.catalog / "another-directory"
        shutil.copytree(self.target, duplicate)
        self.assertEqual(self.status(), "PERSONAL_ENTRY_AMBIGUOUS")
        shutil.rmtree(duplicate)
        (self.catalog / "uninstalled").mkdir()
        self.target.rename(self.catalog / "uninstalled" / self.target.name)
        self.assertEqual(self.status(), "PERSONAL_ENTRY_DISABLED")

    def add_ui(self):
        metadata = self.target / "agents/openai.yaml"
        metadata.write_text(
            "interface:\n  display_name: Demo\n  default_prompt: Use $demo\n"
            "  icon_small: assets/icon.svg\n  icon_large: ./assets/icon.svg\n"
            "policy:\n  allow_implicit_invocation: true\n  products: [chatgpt, codex, api, atlas]\n")
        (self.target / "assets").mkdir()
        (self.target / "assets/icon.svg").write_text("<svg/>\n")
        return metadata

    def test_catalog_ui_exceptions_are_explicit(self):
        self.install()
        self.add_ui()
        self.assertEqual(self.status(), "PERSONAL_ENTRY_IN_SYNC")
        self.assertEqual(self.result()["skills"][0]["catalog_ui_assets"], ["assets/icon.svg"])

    def test_policy_and_prompt_changes_still_fail(self):
        self.install()
        metadata = self.add_ui()
        original = metadata.read_text()
        metadata.write_text(original.replace("invocation: true", "invocation: false"))
        self.assertEqual(self.status(), "PERSONAL_ENTRY_DRIFT")
        metadata.write_text(original.replace("Use $demo", "Publish automatically"))
        self.assertEqual(self.status(), "PERSONAL_ENTRY_DRIFT")

    def test_unexpected_product_list_is_blocked(self):
        self.install()
        metadata = self.add_ui()
        metadata.write_text(metadata.read_text().replace("api, atlas", "api, unknown"))
        with self.assertRaises(RuntimeContractError):
            self.result()

    def test_missing_icon_is_blocked(self):
        self.install()
        self.add_ui()
        (self.target / "assets/icon.svg").unlink()
        with self.assertRaises(RuntimeContractError):
            self.result()

    def test_symlinks_are_blocked(self):
        self.install()
        (self.target / "linked.md").symlink_to(self.source / "SKILL.md")
        with self.assertRaises(RuntimeContractError):
            self.result()

    def test_duplicate_metadata_keys_are_blocked(self):
        self.install()
        (self.target / "SKILL.md").write_text("---\nname: demo\nname: other\n---\n")
        with self.assertRaises(RuntimeContractError):
            self.result()

    def test_repository_drift_is_not_normalized_away(self):
        self.install()
        (self.source / "SKILL.md").write_text("changed source\n")
        self.assertEqual(self.status(), "REPOSITORY_LOCK_MISMATCH")

    def test_unknown_selection_is_blocked(self):
        with self.assertRaises(RuntimeContractError):
            audit(self.workspace, self.lock_path, self.catalog, {"unknown"})

    def test_source_symlink_is_blocked(self):
        self.install()
        (self.source / "linked.md").symlink_to(self.target / "SKILL.md")
        with self.assertRaises(RuntimeContractError):
            self.result()

    def test_dependency_change_is_not_ui_only(self):
        self.install()
        metadata = self.add_ui()
        with metadata.open("a") as handle:
            handle.write("dependencies:\n  tools: []\n")
        self.assertEqual(self.status(), "PERSONAL_ENTRY_DRIFT")

    def test_extra_asset_is_not_allowed_by_icon_exception(self):
        self.install()
        self.add_ui()
        (self.target / "assets/unregistered.svg").write_text("<svg/>\n")
        self.assertEqual(self.status(), "PERSONAL_ENTRY_DRIFT")

    def test_disabled_and_active_duplicate_is_ambiguous(self):
        self.install()
        shutil.copytree(self.target, self.catalog / "uninstalled/old-demo")
        self.assertEqual(self.status(), "PERSONAL_ENTRY_AMBIGUOUS")

    def test_cli_is_read_only_and_nonzero_when_missing(self):
        result = subprocess.run([
            sys.executable, str(ROOT / "scripts/audit_personal_skill_mirrors.py"),
            "--workspace", str(self.workspace), "--lock", str(self.lock_path),
            "--personal-skills-root", str(self.catalog),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stdout)["writes_performed"])


if __name__ == "__main__":
    unittest.main()
