#!/usr/bin/env python3
"""Evidence-bounded strategy assessment; no fetching, approval or channel execution."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date


QUESTIONS = {
    "why_now": "Why Now", "primary_audience": "Primary Audience",
    "core_problem": "Core Problem", "old_vs_new": "Old Way vs New Way",
    "category": "Category", "positioning": "Positioning", "core_value": "Core Value",
    "rtb": "RTB", "objection": "Objection", "message_hierarchy": "Message Hierarchy",
    "launch_story": "Launch Story", "channel_role": "Channel Role",
    "launch_sequence": "Launch Sequence", "success_metric": "Success Metric",
}
CONFIDENCE = ["Unknown", "Low", "Medium", "High"]
ORIGINS = {"Source Idea", "Synthesized Insight", "New Hypothesis"}
KINDS = {"product_truth", "approved_claim", "market", "voc", "competitor", "test", "decision", "theory"}
CORE = tuple(list(QUESTIONS)[:10])
CHOICES = {"primary_audience", "positioning", "core_value"}
GATES = {
    "A Problem": ["core_problem", "old_vs_new"],
    "B Audience": ["primary_audience"],
    "C Value": ["category", "positioning", "core_value"],
    "D Proof": ["rtb"], "E Objection": ["objection"],
    "F Channel": ["channel_role", "launch_sequence"],
}
# Edges describe decision dependencies, not file hierarchy.
DEPENDENCIES = {
    "core_problem": ["primary_audience"],
    "positioning": ["primary_audience", "core_problem", "old_vs_new", "category"],
    "core_value": ["primary_audience", "core_problem", "old_vs_new"],
    "message_hierarchy": ["positioning", "core_value", "rtb", "objection"],
    "launch_story": ["why_now", "message_hierarchy"],
    "channel_role": ["primary_audience", "message_hierarchy"],
    "launch_sequence": ["channel_role", "launch_story"],
}
UNKNOWN = {"", "unknown", "unverified", "tbd", "need_confirmation", "未确认", "待确认", "不明确"}


def meaningful(value):
    return isinstance(value, str) and value.strip().lower() not in UNKNOWN


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def iso_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def unique_records(items, label):
    if not isinstance(items, list):
        raise ValueError(f"{label} must be an array")
    records = {}
    for item in items:
        if not isinstance(item, dict) or not meaningful(item.get("id")):
            raise ValueError(f"{label} requires object IDs")
        if item["id"] in records:
            raise ValueError(f"duplicate {label} ID: {item['id']}")
        records[item["id"]] = item
    return records


def route_request(task, changed_questions=(), has_accepted_baseline=False):
    """A local edit never implicitly reopens all GTM questions."""
    if task not in {"new_gtm", "strategy_change", "resume", "local_revision", "campaign_only"}:
        raise ValueError("unsupported task")
    if set(changed_questions) - QUESTIONS.keys():
        raise ValueError("unknown changed question")
    if task in {"new_gtm", "strategy_change"} or changed_questions:
        return "ASSESS_GTM"
    return "INHERIT_ACCEPTED_BASELINE" if has_accepted_baseline else "LEGACY_SCOPED_REVIEW"


def evidence_issues(evidence, question_id, data, today):
    """Validate explicit source assessments, not their semantic truth."""
    issues = []
    eid = evidence["id"]
    if evidence.get("kind") not in KINDS or evidence.get("kind") in {"theory", "decision"}:
        issues.append(f"{eid}: 方法论/内部决策/未知来源类型不是市场或产品验证证据")
    if evidence.get("status") != "verified" or not meaningful(evidence.get("ref")):
        issues.append(f"{eid}: 来源未核验或无引用")
    if evidence.get("market") != data["market"] or evidence.get("scope_ref") != data["scope_ref"]:
        issues.append(f"{eid}: 市场或产品/Offer范围不匹配")
    start, end = iso_date(evidence.get("as_of")), iso_date(evidence.get("valid_until"))
    if not start or not end or not start <= today <= end:
        issues.append(f"{eid}: 来源有效期未知、过期或未来日期")
    supports = evidence.get("supports", {})
    if not isinstance(supports, dict) or not meaningful(supports.get(question_id)):
        issues.append(f"{eid}: 未记录该来源如何支持当前结论")
    if not meaningful(evidence.get("assessed_by")):
        issues.append(f"{eid}: 缺少证据评估责任人")
    if evidence.get("conflicts_with", []):
        issues.append(f"{eid}: 存在未解决来源冲突")
    return issues


def assess(data, *, as_of=None):
    data = copy.deepcopy(data)
    for field in ("project_id", "market", "scope_ref", "strategy_version"):
        if not meaningful(data.get(field)):
            raise ValueError(f"missing {field}")
    if data.get("schema_version") != "1.0":
        raise ValueError("unsupported schema_version")
    today = iso_date(as_of) if as_of is not None else date.today()
    if today is None:
        raise ValueError("invalid assessment date")
    supplied = unique_records(data.get("answers", []), "answer")
    if supplied.keys() - QUESTIONS.keys():
        raise ValueError("unknown answer ID")
    evidence = unique_records(data.get("evidence", []), "evidence")
    rows = []
    for qid, label in QUESTIONS.items():
        item = copy.deepcopy(supplied.get(qid, {}))
        item.update(id=qid, question=label)
        requested = item.get("confidence", "Unknown")
        if requested not in CONFIDENCE:
            raise ValueError(f"{qid}: invalid confidence")
        for key in ("gaps", "evidence_ids", "principle_ids", "candidates"):
            item.setdefault(key, [])
            if not isinstance(item[key], list):
                raise ValueError(f"{qid}: {key} must be an array")
        item.setdefault("conclusion", "Unknown")
        item.setdefault("origin", "New Hypothesis")
        item.setdefault("classification", "HYPOTHESIS")
        if item["origin"] not in ORIGINS:
            raise ValueError(f"{qid}: invalid origin")
        if item["classification"] not in {"FACT", "DECISION", "HYPOTHESIS", "RECOMMENDATION", "DATA_GAP", "RISK"}:
            raise ValueError(f"{qid}: invalid classification")
        for key, default in (("owner", "Unassigned"), ("deadline", "TBD"),
                             ("priority", "P1"),
                             ("decision_affected", qid), ("validation_method", "待定义验证方法"),
                             ("evidence_needed", "待补决策相关证据")):
            if not meaningful(item.get(key)):
                item[key] = default
        gaps = list(item["gaps"])
        usable = []
        for eid in item["evidence_ids"]:
            if eid not in evidence:
                gaps.append(f"{eid}: 来源ID不存在")
                continue
            source = evidence[eid]
            issues = evidence_issues(source, qid, data, today)
            gaps.extend(issues)
            if not issues:
                usable.append(source)
        contradictions = [e["id"] for e in evidence.values()
                          if qid in e.get("contradicts", [])]
        source_conflicts = [e["id"] for e in evidence.values() if e.get("conflicts_with") and (
            e["id"] in item["evidence_ids"] or qid in e.get("supports", {}))]
        if contradictions:
            gaps.append("未解决反证：" + ", ".join(contradictions))
        if not usable:
            gaps.append("无可用的项目证据；理论、标题或内部共识不能替代验证")
        rank = min(CONFIDENCE.index(requested), 2 if usable else 1)
        distinct_sources = {e["ref"]: e for e in usable}
        groups = {e.get("independence_key") for e in distinct_sources.values() if meaningful(e.get("independence_key"))}
        if item["classification"] == "FACT" and item.get("fact_domain") not in {
                "product", "market", "consumer", "competitor", "test"}:
            gaps.append("FACT需标明fact_domain；不能把市场观察混作产品事实")
            rank = min(rank, 1)
        canonical_fact = item["classification"] == "FACT" and item.get("fact_domain") == "product" and any(
            e["kind"] in {"product_truth", "approved_claim"} and meaningful(e.get("approval_ref")) for e in usable)
        if len(groups) >= 2 or canonical_fact:
            rank = CONFIDENCE.index(requested)
        elif rank == 2:
            gaps.append("单一或独立性未确认的证据，仅可条件性进入")
        if contradictions or source_conflicts or item.get("conflict") or item.get("prohibited") or item.get("hard_blocker"):
            rank = min(rank, 1)
            gaps.append("冲突、禁止主张或硬性阻塞未解除")
        if (qid == "rtb" or item.get("requires_product_truth") or item.get("fact_domain") == "product") and not any(
                e["kind"] in {"product_truth", "approved_claim"} and meaningful(e.get("approval_ref")) for e in usable):
            rank = min(rank, 1)
            gaps.append("产品事实/RTB缺少准确范围的已批准事实或Claim来源")
        if not meaningful(item["conclusion"]):
            rank = 0
            gaps.append("当前结论未确认")
        if item["classification"] == "FACT" and item.get("fact_domain") not in {
                "product", "market", "consumer", "competitor", "test"}:
            rank = min(rank, 1)
        if qid in CORE:
            for key in ("selection_reason", "disconfirming_evidence"):
                if not meaningful(item.get(key)):
                    gaps.append(f"缺少{key}")
                    rank = min(rank, 1)
        if qid in CHOICES:
            candidates = unique_records(item["candidates"], "candidate")
            selected = [c for c in candidates.values() if c.get("status") == "preferred"]
            alternatives = [c for c in candidates.values() if c.get("status") in {"deferred", "rejected"}]
            if len(selected) != 1 or not alternatives or any(
                    not meaningful(c.get("description")) or not meaningful(c.get("reason")) for c in candidates.values()):
                gaps.append("候选比较未完成：需要一个首选和有理由的暂不选/放弃项")
                rank = min(rank, 1)
            if not meaningful(item.get("stop_doing")):
                gaps.append("未记录资源取舍/停止项")
                rank = min(rank, 1)
            if qid == "primary_audience" and not meaningful(item.get("core_scene")):
                gaps.append("缺少核心场景及触发事件")
                rank = min(rank, 1)
        if qid == "positioning" and data["market"] == "JP" and not meaningful(item.get("conclusion_ja")):
            gaps.append("缺少日本市场定位逻辑（日文；不是直译口号）")
            rank = min(rank, 1)
        # Open caveats may support a conditional answer, never a settled High.
        if gaps:
            rank = min(rank, 2)
        item.update(requested_confidence=requested, confidence=CONFIDENCE[rank],
                    gaps=list(dict.fromkeys(gaps)), usable_evidence_ids=[e["id"] for e in usable])
        rows.append(item)
    by_id = {r["id"]: r for r in rows}
    for qid, deps in DEPENDENCIES.items():
        blocked = [dep for dep in deps if CONFIDENCE.index(by_id[dep]["confidence"]) < 2]
        if blocked:
            row = by_id[qid]
            row["confidence"] = CONFIDENCE[min(CONFIDENCE.index(row["confidence"]), 1)]
            row["gaps"].append("前置决策未成立：" + ", ".join(blocked))
    for item in rows:
        item["can_enter_one_pager"] = {"High": "可以", "Medium": "部分"}.get(item["confidence"], "暂不")
    gates = []
    for name, ids in GATES.items():
        ranks = [CONFIDENCE.index(by_id[q]["confidence"]) for q in ids]
        gates.append({"gate": name, "question_ids": ids,
                      "status": "Red" if min(ranks) < 2 else "Green" if min(ranks) == 3 else "Yellow"})
    blockers = [qid for qid in CORE if CONFIDENCE.index(by_id[qid]["confidence"]) < 2]
    context = data.get("context", {})
    context_gaps = []
    state_date = iso_date(context.get("state_as_of"))
    threshold = context.get("threshold_days", 7)
    if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold < 1:
        raise ValueError("context.threshold_days must be a positive integer from Resolver")
    if (context.get("effective_freshness_status") != "current" or not state_date
            or not 0 <= (today - state_date).days <= threshold):
        context_gaps.append("PROJECT_STATE_STALE_OR_UNKNOWN：只允许来源刷新及Review准备")
    if not meaningful(context.get("product_truth_ref")):
        context_gaps.append("PRODUCT_TRUTH_REFERENCE_MISSING")
    context_gaps.extend(context.get("blocking_items", []))
    hard = any(r.get("hard_blocker") or r.get("prohibited") for r in rows)
    readiness = "Red" if blockers or context_gaps or hard else "Green" if all(
        by_id[q]["confidence"] == "High" for q in CORE) else "Yellow"
    return {
        "schema_version": "1.0", "project_id": data["project_id"], "market": data["market"],
        "scope_ref": data["scope_ref"], "strategy_version": data["strategy_version"],
        "assessment_date": today.isoformat(), "input_sha256": digest(data),
        "context": context, "evidence": list(evidence.values()), "answers": rows,
        "gates": gates, "strategy_readiness": readiness,
        "blocking_questions": blockers, "context_gaps": context_gaps,
        "approval_status": "proposed", "stop_gate": "STRATEGY_SCOPE_GATE",
        "channel_plan": "DEFERRED", "publication_status": "NOT_AUTHORIZED",
        "assessment_boundary": "结构校验只验证已提供的来源评估；不证明正文已读取、语义支持成立或审批真实。人审不可替代。",
    }


def changed_questions(previous, current):
    if previous["project_id"] != current["project_id"]:
        raise ValueError("cannot compare different projects")
    old = {r["id"]: r for r in previous["answers"]}
    new = {r["id"]: r for r in current["answers"]}
    fields = ("conclusion", "conclusion_ja", "core_scene", "confidence", "can_enter_one_pager",
              "usable_evidence_ids", "gaps", "candidates", "stop_doing", "selection_reason",
              "disconfirming_evidence", "classification", "fact_domain", "origin", "principle_ids")
    changed = {qid for qid in QUESTIONS if any(old.get(qid, {}).get(k) != new.get(qid, {}).get(k) for k in fields)}
    if any(previous.get(k) != current.get(k) for k in ("market", "scope_ref", "context", "evidence")):
        changed.update(CORE)
    while True:
        expanded = changed | {qid for qid, deps in DEPENDENCIES.items() if changed.intersection(deps)}
        if expanded == changed:
            return sorted(changed)
        changed = expanded


def impact_report(previous, current, briefs):
    changed = changed_questions(previous, current)
    if changed and previous["strategy_version"] == current["strategy_version"]:
        raise ValueError("changed strategy must use a new version; approved baseline is immutable")
    affected = []
    for brief in briefs:
        if brief.get("project_id") != current["project_id"]:
            continue
        ref = brief.get("gtm_decision_pack", {})
        deps = brief.get("decision_ids", list(CORE))
        affected.append({"brief_id": brief["brief_id"], "status": "REVIEW_REQUIRED" if (
            set(deps).intersection(changed) or ref.get("sha256") != digest(current)) else "UNCHANGED",
            "affected_decisions": sorted(set(deps).intersection(changed)),
            "reason": "旧版本与批准对象保留；只标记影响，不修改Brief正文或批准记录"})
    return {"changed_questions": changed, "briefs": affected, "baseline_modified": False}
