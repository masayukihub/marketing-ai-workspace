#!/usr/bin/env python3
"""Campaign PLAN internal runner. Writes new review artifacts, never formal state."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import date
from pathlib import Path

from gtm_decisions import CORE, QUESTIONS, assess, digest, impact_report, iso_date, meaningful


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def md(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers),
                      *["| " + " | ".join(md(v) for v in row) + " |" for row in rows]])


def approval_issues(pack, record, today, question_ids=CORE):
    issues = []
    exact = {"project_id": pack["project_id"], "market": pack["market"],
             "scope_ref": pack["scope_ref"], "strategy_version": pack["strategy_version"],
             "pack_sha256": digest(pack), "gate": "STRATEGY_SCOPE_GATE", "status": "accepted"}
    for key, value in exact.items():
        if record.get(key) != value:
            issues.append(f"APPROVAL_MISMATCH:{key}")
    if not all(meaningful(record.get(k)) for k in ("decision_id", "reviewer", "source")):
        issues.append("APPROVAL_EVIDENCE_MISSING")
    approved_at, until = iso_date(record.get("approved_at")), iso_date(record.get("valid_until"))
    if not approved_at or not until or not approved_at <= today <= until:
        issues.append("APPROVAL_EXPIRED_OR_UNVERIFIED")
    if pack["strategy_readiness"] == "Red":
        issues.append("STRATEGY_EVIDENCE_BLOCKED")
    state_date = iso_date(pack.get("context", {}).get("state_as_of"))
    if not state_date or not 0 <= (today - state_date).days <= pack.get("context", {}).get("threshold_days", 7):
        issues.append("PROJECT_STATE_STALE_OR_UNKNOWN")
    for evidence in pack["evidence"]:
        used = any(evidence["id"] in a["usable_evidence_ids"] for a in pack["answers"] if a["id"] in question_ids)
        if used and not (iso_date(evidence.get("valid_until")) and today <= iso_date(evidence["valid_until"])):
            issues.append("STRATEGY_EVIDENCE_EXPIRED:" + evidence["id"])
    return issues


def read_main_record(workspace, path, authority_ref):
    """Read the approval at a preflight-verified main commit, not a local draft."""
    if not authority_ref or len(authority_ref) != 40 or any(c not in "0123456789abcdef" for c in authority_ref):
        raise ValueError("full preflight-verified main SHA required")
    if Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError("approval path must be repository-relative")
    subprocess.run(["git", "merge-base", "--is-ancestor", authority_ref, "refs/remotes/origin/main"],
                   cwd=workspace, check=True, capture_output=True)
    raw = subprocess.check_output(["git", "show", f"{authority_ref}:{path}"], cwd=workspace, text=True)
    return json.loads(raw)


def brief_handoff(pack, brief, record, *, today):
    """Shared by Amazon, EDM, PR and KOL; no independent repositioning."""
    assertions = brief.get("strategy_assertions", {})
    deps = brief.get("decision_ids", [])
    issues = approval_issues(pack, record, today, set(CORE) | set(deps) | set(assertions))
    if not meaningful(brief.get("brief_id")):
        issues.append("BRIEF_ID_MISSING")
    if set(assertions) - set(deps):
        issues.append("BRIEF_UNDECLARED_DECISION")
    expected = {"project_id": pack["project_id"], "strategy_version": pack["strategy_version"], "sha256": digest(pack)}
    ref = brief.get("gtm_decision_pack", {})
    if brief.get("project_id") != pack["project_id"] or any(ref.get(k) != v for k, v in expected.items()):
        issues.append("BRIEF_STRATEGY_REFERENCE_MISMATCH")
    if not meaningful(ref.get("path")):
        issues.append("BRIEF_PACK_PATH_MISSING")
    by_id = {r["id"]: r for r in pack["answers"]}
    if not deps or set(deps) - QUESTIONS.keys():
        issues.append("BRIEF_DECISION_IDS_MISSING_OR_INVALID")
    for qid in deps:
        if qid in by_id and by_id[qid]["can_enter_one_pager"] == "暂不":
            issues.append("BRIEF_DEPENDS_ON_UNKNOWN:" + qid)
    for qid, value in assertions.items():
        if qid not in by_id or value != by_id[qid]["conclusion"]:
            issues.append("BRIEF_STRATEGY_DRIFT:" + qid)
    return {
        "brief_id": brief.get("brief_id"), "status": "BLOCKED" if issues else "STRATEGY_INHERITED",
        "issues": issues, "gtm_decision_pack": ref,
        "strategy_answers": {} if issues else {
            qid: {"conclusion": by_id[qid]["conclusion"], "conclusion_ja": by_id[qid].get("conclusion_ja"),
                  "core_scene": by_id[qid].get("core_scene"), "confidence": by_id[qid]["confidence"],
                  "limitations": by_id[qid]["gaps"], "evidence_ids": by_id[qid]["usable_evidence_ids"]}
            for qid in QUESTIONS if qid in set(CORE) | set(deps) | set(assertions)},
        "claim_approval": "NOT_GRANTED", "production_or_publication": "NOT_AUTHORIZED",
    }


def write_review(pack, output, previous=None, briefs=(), record=None, *, review_date=None):
    output = Path(output)
    review_date = review_date or date.today()
    eligible_ids = [a["id"] for a in pack["answers"] if a["can_enter_one_pager"] != "暂不"]
    if record is not None:
        issues = approval_issues(pack, record, review_date, set(CORE) | set(eligible_ids))
        if issues:
            raise ValueError("; ".join(issues))
    # Immutable runs: never overwrite a selected baseline or a prior review.
    if output.exists():
        raise ValueError("output directory already exists; use a new run/version")
    impact = impact_report(previous, pack, briefs) if previous else None
    output.mkdir(parents=True)
    rows = pack["answers"]
    map_text = "# GTM答案完整度地图\n\n" + table(
        ["问题", "当前结论", "证据强度", "是否能进One Pager", "缺口"],
        [[a["question"], a["conclusion"] if meaningful(a["conclusion"]) else "未确认", a["confidence"],
          a["can_enter_one_pager"], ("；".join(a["gaps"][:2]) or "—") + (
              f"；另{len(a['gaps']) - 2}项见补证表" if len(a["gaps"]) > 2 else "")] for a in rows])
    map_text += f"\n\n策略证据状态：{pack['strategy_readiness']}。进入资格不等于人工批准。\n"
    map_text += "\n" + "\n".join("- " + x for x in pack["context_gaps"])
    (output / "00_gtm_answer_completeness_map.md").write_text(map_text + "\n", encoding="utf-8")
    detail = ["# 策略决策依据与候选比较", "", "Source Idea / Synthesized Insight / New Hypothesis 与证据、审批状态分别记录。", ""]
    for a in rows:
        detail.extend([f"## {a['question']}", "", f"- 结论：{a['conclusion']}",
                       f"- 类型：{a['origin']} / {a['classification']}",
                       f"- 思想来源：{', '.join(a['principle_ids']) or '待补'}",
                       f"- 为什么选：{a.get('selection_reason') or '待确认'}",
                       f"- 反证条件：{a.get('disconfirming_evidence') or '待定义'}",
                       f"- 停止项：{a.get('stop_doing') or '待确认/不适用'}",
                       f"- 核心场景：{a.get('core_scene') or '待确认/不适用'}",
                       f"- 可用证据：{', '.join(a['usable_evidence_ids']) or '无'}",
                       f"- 完整缺口：{'；'.join(a['gaps']) or '—'}", ""])
        if a["candidates"]:
            detail.extend([table(["候选ID", "方案", "状态", "选择/不选理由"], [
                [c["id"], c.get("description", ""), c.get("status", ""), c.get("reason", "")]
                for c in a["candidates"]]), ""])
    detail.extend(["## 来源登记与支持关系", "", table(["ID", "来源", "市场/范围", "有效期", "支持理由"], [
        [e["id"], e.get("ref"), f"{e.get('market')} / {e.get('scope_ref')}",
         e.get("valid_until"), json.dumps(e.get("supports", {}), ensure_ascii=False)] for e in pack["evidence"]])])
    (output / "01_strategy_decisions.md").write_text("\n".join(detail) + "\n", encoding="utf-8")
    gate_text = "# Strategy Review Gate\n\n" + table(["诊断项", "状态"], [[g["gate"], g["status"]] for g in pack["gates"]])
    gate_text += "\n\nF Channel 仅展示下游缺口，不作为本轮策略评审的前置循环依赖。\n"
    approval_label = "accepted via exact external record; source pack remains proposed" if record is not None else "proposed"
    gate_text += f"\n- Strategy readiness: {pack['strategy_readiness']}\n- Approval: {approval_label}\n- Stop: STRATEGY_SCOPE_GATE\n- Channel Plan: Deferred\n"
    gate_text += "\n" + pack["assessment_boundary"] + "\n"
    (output / "02_strategy_review_gate.md").write_text(gate_text, encoding="utf-8")
    with (output / "03_validation_plan.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["question_id", "confidence", "gap", "evidence_needed", "validation_method", "owner", "priority", "deadline", "decision_affected"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for a in rows:
            if a["gaps"] or a["confidence"] in {"Unknown", "Low"}:
                writer.writerow(dict(question_id=a["id"], confidence=a["confidence"], gap="；".join(a["gaps"]),
                                     **{k: a[k] for k in fields[3:]}))
        for gap in pack["context_gaps"]:
            writer.writerow(dict(question_id="context", confidence="Unknown", gap=gap, evidence_needed="当前正式来源与范围",
                                 validation_method="按Context Package刷新来源并提交相应Owner审核", owner="Unassigned",
                                 priority="P0", deadline="TBD", decision_affected="STRATEGY_SCOPE_GATE"))
    (output / "04_gtm_decision_pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    approved = record is not None
    one = "# GTM One Pager — Deferred\n\n等待准确策略版本的 STRATEGY_SCOPE_GATE 人工接受记录；不生成渠道执行计划。\n"
    if approved:
        one = "# GTM One Pager — Strategy accepted only\n\n"
        for a in rows:
            if a["can_enter_one_pager"] != "暂不":
                one += f"## {a['question']}\n\n{a['conclusion']}\n\n"
                if a.get("conclusion_ja"):
                    one += a["conclusion_ja"] + "\n\n"
                one += f"证据：{a['confidence']}；限制：{'；'.join(a['gaps']) or '单源或适用范围见决策包'}\n\n"
        one += "## Unknowns / 未进入的结论\n\n"
        one += "\n".join(f"- {a['question']}：{'；'.join(a['gaps']) or '证据不足'}"
                         for a in rows if a["can_enter_one_pager"] == "暂不") or "无已登记未知项。"
        one += "\n\nClaim、商业、生产、发布仍需各自审批。\n"
    (output / "05_gtm_one_pager.md").write_text(one, encoding="utf-8")
    ref = {"project_id": pack["project_id"], "strategy_version": pack["strategy_version"],
           "path": "04_gtm_decision_pack.json", "sha256": digest(pack)}
    (output / "06_campaign_context_patch.proposed.json").write_text(json.dumps({
        "proposal_only": True, "base_path": "resolve relative to this proposal artifact",
        "gtm_decision_pack": ref, "approval_status": "accepted" if approved else "proposed",
        "decision_record_ref": record.get("source") if approved else None,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if impact is not None:
        (output / "07_brief_impact.json").write_text(json.dumps(impact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"first_artifact": str(output / "00_gtm_answer_completeness_map.md"), "pack_sha256": digest(pack),
            "strategy_readiness": pack["strategy_readiness"], "stop_gate": "STRATEGY_SCOPE_GATE"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("assess")
    run.add_argument("input")
    run.add_argument("--output-dir", required=True)
    run.add_argument("--as-of", help="Deterministic audit date only; normal runs use today")
    run.add_argument("--previous-pack")
    run.add_argument("--briefs", help="JSON array; report impact without modifying Briefs")
    check = commands.add_parser("check-brief")
    check.add_argument("--pack", required=True)
    check.add_argument("--brief", required=True)
    check.add_argument("--decision-record", required=True, help="JSON record path at verified main commit")
    check.add_argument("--authority-ref", required=True)
    check.add_argument("--workspace", required=True)
    accepted = commands.add_parser("render-accepted")
    accepted.add_argument("--pack", required=True)
    accepted.add_argument("--decision-record", required=True)
    accepted.add_argument("--authority-ref", required=True)
    accepted.add_argument("--workspace", required=True)
    accepted.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        if args.command == "assess":
            result = write_review(assess(load(args.input), as_of=args.as_of), args.output_dir,
                                  load(args.previous_pack) if args.previous_pack else None,
                                  load(args.briefs) if args.briefs else [])
        else:
            record = read_main_record(args.workspace, args.decision_record, args.authority_ref)
            pack = load(args.pack)
            if args.command == "check-brief":
                brief = load(args.brief)
                ref_path = brief.get("gtm_decision_pack", {}).get("path", "")
                if (Path(args.brief).resolve().parent / ref_path).resolve() != Path(args.pack).resolve():
                    raise ValueError("BRIEF_PACK_PATH_MISMATCH")
                result = brief_handoff(pack, brief, record, today=date.today())
            else:
                eligible = {a["id"] for a in pack["answers"] if a["can_enter_one_pager"] != "暂不"}
                issues = approval_issues(pack, record, date.today(), set(CORE) | eligible)
                if issues:
                    raise ValueError("; ".join(issues))
                result = write_review(pack, args.output_dir, record=record)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get("status") == "BLOCKED" else 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
