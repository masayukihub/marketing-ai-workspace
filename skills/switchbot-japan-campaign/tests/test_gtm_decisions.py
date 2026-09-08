"""Synthetic behavioral tests. No fixture represents a SwitchBot product or approval."""

import copy
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from gtm_decisions import CHOICES, CORE, QUESTIONS, assess, digest, impact_report, route_request
from gtm_strategy import approval_issues, brief_handoff, read_main_record, write_review

TODAY = date(2026, 9, 8)


def fixture():
    sources = [{"id": f"E{n}", "kind": "product_truth" if n == 1 else "voc",
                "ref": f"https://example.invalid/synthetic/{n}", "status": "verified",
                "market": "JP", "scope_ref": "synthetic-product-v1", "as_of": "2026-09-07",
                "valid_until": "2026-09-14", "assessed_by": "Synthetic Analyst",
                "independence_key": f"synthetic-study-{n}", "approval_ref": "synthetic-truth-review",
                "supports": {q: "Synthetic fixture support, not real research" for q in QUESTIONS}}
               for n in (1, 2)]
    answers = []
    for qid in QUESTIONS:
        a = dict(id=qid, conclusion=f"synthetic {qid}", conclusion_ja="日本市場での検証用の仮説",
                 confidence="High", evidence_ids=["E1", "E2"], classification="RECOMMENDATION",
                 origin="Synthesized Insight", principle_ids=["A01"], selection_reason="Synthetic comparison",
                 disconfirming_evidence="Synthetic contrary behavior", stop_doing="Do not target alternative B",
                 core_scene="Synthetic trigger in a synthetic home", gaps=[])
        if qid in CHOICES:
            a["candidates"] = [dict(id="A", description="Synthetic A", status="preferred", reason="Synthetic support"),
                               dict(id="B", description="Synthetic B", status="deferred", reason="Insufficient fit")]
        answers.append(a)
    return dict(schema_version="1.0", project_id="synthetic-demo", market="JP", scope_ref="synthetic-product-v1",
                strategy_version="candidate-1", evidence=sources, answers=answers,
                context=dict(effective_freshness_status="current", state_as_of="2026-09-07", threshold_days=7,
                             product_truth_ref="synthetic-truth-pointer", blocking_items=[]))


def run(data=None):
    return assess(data or fixture(), as_of=TODAY.isoformat())


def answer(pack, qid):
    return next(a for a in pack["answers"] if a["id"] == qid)


def approval(pack):
    return dict(project_id=pack["project_id"], market=pack["market"], scope_ref=pack["scope_ref"],
                strategy_version=pack["strategy_version"], pack_sha256=digest(pack), gate="STRATEGY_SCOPE_GATE",
                status="accepted", decision_id="SYNTHETIC-ONLY", reviewer="Synthetic Reviewer",
                source="synthetic-decision.json", approved_at="2026-09-08", valid_until="2026-09-14")


def brief(pack, channel="Amazon"):
    return dict(brief_id=f"SYNTHETIC-{channel}", project_id=pack["project_id"], channel=channel,
                decision_ids=list(CORE), gtm_decision_pack=dict(project_id=pack["project_id"],
                    strategy_version=pack["strategy_version"], sha256=digest(pack), path="pack.json"))


def test_high_without_sources_cannot_enter_one_pager():
    data = fixture()
    data["evidence"] = []
    pack = run(data)
    assert pack["strategy_readiness"] == "Red"
    assert all(a["can_enter_one_pager"] == "暂不" for a in pack["answers"])


@pytest.mark.parametrize("qid", CORE)
def test_any_unknown_core_dependency_blocks(qid):
    data = fixture()
    answer(data, qid)["conclusion"] = "Unknown"
    pack = run(data)
    assert pack["strategy_readiness"] == "Red"
    assert qid in pack["blocking_questions"]
    assert pack["channel_plan"] == "DEFERRED"


@pytest.mark.parametrize("change", [dict(market="CN"), dict(scope_ref="different-variant"),
    dict(valid_until="2026-09-01"), dict(as_of="2026-09-10"), dict(status="indexed_only"),
    dict(kind="theory"), dict(kind="decision"), dict(supports={}), dict(assessed_by=""),
    dict(conflicts_with=["E-CONFLICT"]), dict(ref="")])
def test_unusable_evidence_does_not_prove_japan_strategy(change):
    data = fixture()
    for e in data["evidence"]:
        e.update(change)
    pack = run(data)
    assert pack["strategy_readiness"] == "Red"
    assert answer(pack, "primary_audience")["can_enter_one_pager"] == "暂不"


def test_single_source_caps_high_and_duplicate_sources_do_not_add_independence():
    data = fixture()
    data["evidence"][1]["ref"] = data["evidence"][0]["ref"]
    pack = run(data)
    assert answer(pack, "primary_audience")["confidence"] == "Medium"
    assert answer(pack, "primary_audience")["gaps"]


def test_conflicting_evidence_cannot_be_hidden_by_omitting_its_reference():
    data = fixture()
    e = copy.deepcopy(data["evidence"][1])
    e.update(id="E3", contradicts=["core_problem"])
    data["evidence"].append(e)
    pack = run(data)
    assert answer(pack, "core_problem")["can_enter_one_pager"] == "暂不"
    assert answer(pack, "message_hierarchy")["can_enter_one_pager"] == "暂不"


def test_one_conflicted_source_is_not_overridden_by_one_good_source():
    data = fixture()
    data["evidence"][1]["conflicts_with"] = ["E1"]
    assert answer(run(data), "core_problem")["can_enter_one_pager"] == "暂不"


def test_caller_eligibility_override_is_ignored():
    data = fixture()
    answer(data, "core_problem").update(confidence="Unknown", can_enter_one_pager="可以", can_enter="yes")
    assert answer(run(data), "core_problem")["can_enter_one_pager"] == "暂不"


@pytest.mark.parametrize("change", [dict(candidates=[]), dict(stop_doing=""), dict(core_scene=""),
                                   dict(selection_reason=""), dict(disconfirming_evidence="")])
def test_choice_requires_reason_alternative_scene_and_falsifier(change):
    data = fixture()
    answer(data, "primary_audience").update(change)
    assert run(data)["strategy_readiness"] == "Red"


def test_product_claims_need_approved_truth_not_two_reviews():
    data = fixture()
    for e in data["evidence"]:
        e["kind"] = "voc"
    assert answer(run(data), "rtb")["can_enter_one_pager"] == "暂不"


def test_market_fact_uses_market_evidence_without_product_approval():
    data = fixture()
    for n, original in enumerate(copy.deepcopy(data["evidence"]), 3):
        original.update(id=f"M{n}", kind="market", ref=f"https://example.invalid/market/{n}",
                        independence_key=f"market-{n}", approval_ref=None)
        data["evidence"].append(original)
    answer(data, "why_now").update(classification="FACT", fact_domain="market", evidence_ids=["M3", "M4"])
    assert answer(run(data), "why_now")["confidence"] == "High"
    answer(data, "why_now")["fact_domain"] = "product"
    assert answer(run(data), "why_now")["confidence"] == "Low"
    answer(data, "why_now").pop("fact_domain")
    assert answer(run(data), "why_now")["confidence"] == "Low"


def test_full_evidence_is_not_approval_and_downstream_questions_do_not_deadlock():
    data = fixture()
    for qid in ("channel_role", "launch_sequence"):
        answer(data, qid).update(conclusion="Unknown", confidence="Unknown", evidence_ids=[])
    pack = run(data)
    assert pack["strategy_readiness"] == "Green"
    assert pack["approval_status"] == "proposed"
    assert pack["publication_status"] == "NOT_AUTHORIZED"
    assert pack["channel_plan"] == "DEFERRED"


@pytest.mark.parametrize("state", ["stale", "unknown"])
def test_stale_context_never_becomes_current_from_recent_output(state):
    data = fixture()
    data["context"]["effective_freshness_status"] = state
    assert run(data)["strategy_readiness"] == "Red"
    data["context"].update(effective_freshness_status="current", state_as_of="2026-08-20")
    assert run(data)["strategy_readiness"] == "Red"


def test_freshness_does_not_approve_missing_truth_or_clear_other_gates():
    data = fixture()
    data["context"]["product_truth_ref"] = None
    assert run(data)["strategy_readiness"] == "Red"
    data = fixture()
    data["context"]["blocking_items"] = ["COMMERCIAL_UNCONFIRMED"]
    assert run(data)["context_gaps"] == ["COMMERCIAL_UNCONFIRMED"]


def test_immutable_outputs_map_first_and_no_channels(tmp_path):
    pack = run()
    output = tmp_path / "run"
    result = write_review(pack, output)
    assert Path(result["first_artifact"]).name == sorted(p.name for p in output.iterdir())[0]
    assert "Deferred" in (output / "05_gtm_one_pager.md").read_text()
    assert len((output / "00_gtm_answer_completeness_map.md").read_text().split("| High |")) == 15
    assert not any("channel_plan" in p.name for p in output.iterdir())
    assert json.loads((output / "04_gtm_decision_pack.json").read_text())["approval_status"] == "proposed"
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(ValueError):
        write_review(pack, output)
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}


def test_all_four_briefs_inherit_identical_strategy_only():
    pack = run()
    results = [brief_handoff(pack, brief(pack, c), approval(pack), today=TODAY) for c in ("Amazon", "EDM", "PR", "KOL")]
    assert all(r["status"] == "STRATEGY_INHERITED" for r in results)
    assert all(r["strategy_answers"] == results[0]["strategy_answers"] for r in results)
    assert all(r["claim_approval"] == "NOT_GRANTED" for r in results)
    b = brief(pack)
    b["decision_ids"].append("launch_story")
    result = brief_handoff(pack, b, approval(pack), today=TODAY)
    assert result["strategy_answers"]["launch_story"]["conclusion"] == answer(pack, "launch_story")["conclusion"]


def test_brief_drift_wrong_version_and_visual_approval_are_blocked():
    pack = run()
    b = brief(pack)
    b["strategy_assertions"] = {"core_value": "A different value"}
    assert brief_handoff(pack, b, approval(pack), today=TODAY)["status"] == "BLOCKED"
    b = brief(pack)
    b["gtm_decision_pack"]["strategy_version"] = "old"
    assert brief_handoff(pack, b, approval(pack), today=TODAY)["status"] == "BLOCKED"
    record = approval(pack)
    record["gate"] = "VISUAL_DIRECTION_GATE"
    assert approval_issues(pack, record, TODAY)
    tampered = copy.deepcopy(pack)
    answer(tampered, "core_value")["conclusion"] = "Changed after approval"
    assert "APPROVAL_MISMATCH:pack_sha256" in approval_issues(tampered, approval(pack), TODAY)


def test_brief_requires_identity_and_assertions_must_declare_dependencies():
    pack = run()
    b = brief(pack)
    b.pop("brief_id")
    assert "BRIEF_ID_MISSING" in brief_handoff(pack, b, approval(pack), today=TODAY)["issues"]
    b = brief(pack)
    b["strategy_assertions"] = {"launch_story": answer(pack, "launch_story")["conclusion"]}
    assert "BRIEF_UNDECLARED_DECISION" in brief_handoff(pack, b, approval(pack), today=TODAY)["issues"]


def test_approval_and_sources_expire_without_reusing_cached_green():
    pack = run()
    assert approval_issues(pack, approval(pack), date(2026, 9, 16))


def test_acceptance_on_next_day_uses_review_date_not_assessment_date(tmp_path):
    pack = assess(fixture(), as_of="2026-09-07")
    record = approval(pack)  # Accepted September 8, a day after assessment.
    assert not approval_issues(pack, record, TODAY)
    output = tmp_path / "accepted"
    write_review(pack, output, record=record, review_date=TODAY)
    assert "Strategy accepted only" in (output / "05_gtm_one_pager.md").read_text()
    assert json.loads((output / "06_campaign_context_patch.proposed.json").read_text())["approval_status"] == "accepted"


def test_expired_noncore_evidence_blocks_only_outputs_using_it(tmp_path):
    data = fixture()
    e = copy.deepcopy(data["evidence"][1])
    e.update(id="STORY", ref="https://example.invalid/story", valid_until="2026-09-07")
    data["evidence"].append(e)
    answer(data, "launch_story")["evidence_ids"] = ["STORY"]
    pack = assess(data, as_of="2026-09-07")
    record = approval(pack)
    assert not approval_issues(pack, record, TODAY)  # CORE still usable.
    b = brief(pack)
    assert brief_handoff(pack, b, record, today=TODAY)["status"] == "STRATEGY_INHERITED"
    b["decision_ids"].append("launch_story")
    assert brief_handoff(pack, b, record, today=TODAY)["status"] == "BLOCKED"
    b["decision_ids"].remove("launch_story")
    b["strategy_assertions"] = {"launch_story": answer(pack, "launch_story")["conclusion"]}
    result = brief_handoff(pack, b, record, today=TODAY)
    assert "STRATEGY_EVIDENCE_EXPIRED:STORY" in result["issues"]
    assert result["status"] == "BLOCKED"
    with pytest.raises(ValueError, match="STRATEGY_EVIDENCE_EXPIRED:STORY"):
        write_review(pack, tmp_path / "expired-story", record=record, review_date=TODAY)
    assert not (tmp_path / "expired-story").exists()


def test_strategy_change_only_flags_briefs_and_preserves_approved_baseline():
    previous = run()
    original = copy.deepcopy(previous)
    data = fixture()
    answer(data, "primary_audience")["conclusion"] = "New audience hypothesis"
    current = run(data)
    with pytest.raises(ValueError):
        impact_report(previous, current, [brief(previous)])
    current["strategy_version"] = "candidate-2"
    result = impact_report(previous, current, [brief(previous)])
    assert "message_hierarchy" in result["changed_questions"]
    assert result["briefs"][0]["status"] == "REVIEW_REQUIRED"
    assert previous == original


@pytest.mark.parametrize("field", ["selection_reason", "disconfirming_evidence"])
def test_changed_reason_or_falsifier_requires_new_version_and_tracks_dependents(field):
    previous = run()
    current = copy.deepcopy(previous)
    answer(current, "primary_audience")[field] = "A different decision basis"
    with pytest.raises(ValueError):
        impact_report(previous, current, [brief(previous)])
    current["strategy_version"] = "candidate-2"
    report = impact_report(previous, current, [brief(previous)])
    assert "primary_audience" in report["changed_questions"]
    assert "message_hierarchy" in report["briefs"][0]["affected_decisions"]


def test_local_revision_and_legacy_resume_do_not_require_fourteen_new_answers():
    assert route_request("local_revision", has_accepted_baseline=True) == "INHERIT_ACCEPTED_BASELINE"
    assert route_request("resume") == "LEGACY_SCOPED_REVIEW"
    assert route_request("campaign_only") == "LEGACY_SCOPED_REVIEW"
    assert route_request("local_revision", ["positioning"], True) == "ASSESS_GTM"


def test_malformed_and_duplicate_records_fail_closed():
    data = fixture()
    data["answers"].append(data["answers"][0])
    with pytest.raises(ValueError):
        run(data)
    data = fixture()
    data["evidence"].append(data["evidence"][0])
    with pytest.raises(ValueError):
        run(data)


def test_cli_smoke_unknown_project_answers_are_not_fabricated(tmp_path):
    data = fixture()
    data["answers"] = []
    inp = tmp_path / "input.json"
    inp.write_text(json.dumps(data))
    out = tmp_path / "out"
    proc = subprocess.run([sys.executable, str(SCRIPTS / "gtm_strategy.py"), "assess", str(inp),
                           "--as-of", "2026-09-08", "--output-dir", str(out)], capture_output=True, text=True)
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["strategy_readiness"] == "Red"
    pack = json.loads((out / "04_gtm_decision_pack.json").read_text())
    assert len(pack["answers"]) == 14
    assert all(a["conclusion"] == "Unknown" and a["owner"] == "Unassigned" for a in pack["answers"])


def test_approval_record_is_read_from_main_not_local_edit(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()
    git("init", "-q", "-b", "main")
    record = tmp_path / "decision.json"
    record.write_text('{"status":"proposed"}')
    git("add", "decision.json")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
    sha = git("rev-parse", "HEAD")
    git("update-ref", "refs/remotes/origin/main", sha)
    record.write_text('{"status":"accepted"}')
    assert read_main_record(tmp_path, "decision.json", sha)["status"] == "proposed"
    with pytest.raises(ValueError):
        read_main_record(tmp_path, "../decision.json", sha)
