#!/usr/bin/env python3
"""Create and incrementally refresh local Project Memory from a Feishu catalog.

It never reads Feishu, downloads originals, or promotes product facts/Claims.
Run the workspace Knowledge Pack refresh separately when live discovery is needed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PRODUCTS = {
    "homerunpet": ("homerunpet-jp", "homerunPET Japan", "Product / Brand"),
    "ai mindclip": ("ai-mindclip-jp", "AI MindClip Japan", "Product"),
    "lock ultra": ("lock-ultra-jp", "Lock Ultra Japan", "Product"),
    "hub 3": ("hub-3-jp", "Hub 3 Japan", "Product"),
    "daily station": ("daily-station-jp", "Daily Station Japan", "Product"),
    "kata friends": ("kata-friends-jp", "KATA Friends Japan", "Product"),
    "robot vacuum": ("robot-vacuum-jp", "Robot Vacuum Japan", "Product / Family"),
    "weather station": ("weather-station-jp", "Weather Station Japan", "Product"),
    "circulator": ("circulator-jp", "Circulator Japan", "Product / Family"),
    "lighting": ("lighting-jp", "Lighting Japan", "Product / Family"),
    "curtain": ("curtain-jp", "Curtain Japan", "Product / Family"),
}
TITLE_PROJECTS = {
    r"\bs30\s*mini\b": ("s30-mini-jp", "S30 mini Japan", "Product"),
    r"\bhub\s*4\b": ("hub-4-jp", "Hub 4 Japan", "Product"),
    r"lock\s*ultra\s*max": ("lock-ultra-max-jp", "Lock Ultra Max Japan", "Product"),
    r"video\s*doorbell": ("video-doorbell-jp", "Video Doorbell Japan", "Product"),
    r"k10\+\s*pro": ("k10-pro-jp", "K10+ Pro Japan", "Product"),
    r"nanoleaf": ("nanoleaf-jp", "Nanoleaf Japan", "Brand / GTM"),
}
CAMPAIGNS = {
    "prime day": ("prime-day", "Prime Day", "Campaign"),
    "black friday": ("black-friday", "Black Friday", "Campaign"),
    "new life": ("new-life", "New Life Campaign", "Campaign"),
    "ces": ("ces", "CES", "Campaign / Event"),
    "ifa": ("ifa", "IFA", "Campaign / Event"),
}
IMPACTS = {
    "Critical": re.compile(r"\b(prd|product\s*definition|official\s*spec|pricing|price|positioning|final\s*(brief|plan|decision)|pvt|\bmp\b|launch\s*plan)\b|产品定义|正式规格|定价|価格|定位|最終|上市计划|発売計画", re.I),
    "High": re.compile(r"\b(gtm|market\s*research|consumer\s*research|competitor|campaign\s*plan|media\s*plan|amazon\s*(plan|strategy)|meeting)\b|市场调研|竞品|营销方案|媒体计划|会议纪要", re.I),
    "Medium": re.compile(r"\b(weekly|kol|pr\s*progress|draft|meeting)\b|周会|进度|草稿", re.I),
}


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path, fallback):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2))


def cell(value):
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def parse_date(value):
    try:
        return datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def impact(record):
    text = " ".join(str(record.get(k, "")) for k in ("title", "primary_category", "search_summary", "source_path"))
    for level, pattern in IMPACTS.items():
        if pattern.search(text):
            return level
    return "Low"


def candidates(record):
    matches = []
    product_text = record.get("products", "").lower()
    campaign_text = record.get("campaigns", "").lower()
    title = " ".join(str(record.get(k, "")) for k in ("title", "source_path")).lower()
    for needle, match in PRODUCTS.items():
        # Catalog product tags can originate from broad search recall. A tag is
        # therefore used only when it is the sole product assignment; otherwise
        # require an explicit product mention in title/path.
        if needle in title or product_text.strip() == needle:
            matches.append(match)
    for pattern, match in TITLE_PROJECTS.items():
        if re.search(pattern, title, re.I):
            matches.append(match)
    for needle, match in CAMPAIGNS.items():
        if needle in title or campaign_text.strip() == needle:
            matches.append(match)
    return list(dict.fromkeys(matches))


def version(record):
    stable = {key: record.get(key, "") for key in ("title", "updated_at", "canonical_url", "source_revision", "extract_hash", "source_path", "products", "campaigns")}
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def skills_for(project_type):
    base = ["project-memory-manager"]
    if "Product" in project_type or "Brand" in project_type:
        return base + ["product-knowledge", "product-marketing", "amazon-japan-pdp-generator", "amazon-listing-creative", "launch", "public-relations", "influencer-marketing"]
    return base + ["switchbot-campaign-review", "ads", "analytics", "public-relations", "influencer-marketing", "launch"]


def enrich(project, source_map, as_of):
    project["source_ids"] = sorted(set(project["source_ids"]), key=lambda source_id: (source_map[source_id].get("updated_at", ""), source_id), reverse=True)
    records = [source_map[source_id] for source_id in project["source_ids"]]
    dates = [parse_date(x.get("updated_at", "")) for x in records]
    recent30 = sum(bool(d and (as_of - d).days <= 30) for d in dates)
    recent90 = sum(bool(d and (as_of - d).days <= 90) for d in dates)
    major = sum(impact(x) in {"Critical", "High"} for x in records)
    # Use diminishing returns rather than flat caps so the ranking remains
    # useful for active projects with many catalog matches.
    score = min(35, round(math.log2(len(records) + 1) * 3.5)) + min(30, round(math.sqrt(recent30) * 3)) + min(20, round(math.sqrt(recent90) * 2)) + min(15, round(math.sqrt(major) * 1.5))
    project.update({
        "market": "Japan", "activity_score": score,
        "activity_status": "Active" if recent30 and score >= 20 else "Monitoring" if score >= 12 else "Dormant",
        "recent_30_count": recent30, "major_source_count": major,
        "confidence": "High" if len(records) >= 10 and major else "Medium" if len(records) >= 3 else "Low",
        "related_skills": skills_for(project["project_type"]),
    })
    return project


def context(project, changed, sync_at):
    sources = "\n".join("- `" + source_id + "`" for source_id in project["source_ids"][:20]) or "- Not Available"
    skill_list = "\n".join("- `" + name + "`" for name in project["related_skills"])
    review = "Review required before Current Truth changes." if changed else "No source change detected by this run."
    return f"""# Project Context

## Metadata

- Project Name: {project['project_name']}
- Project ID: `{project['project_id']}`
- Project Type: {project['project_type']}
- Market: Japan (default; verify source-specific market)
- Owner: Not Available
- Status: {project['activity_status']}
- Stage: Discovery / Context consolidation
- Last Updated: {sync_at}
- Confidence: {project['confidence']}

## 1. What It Is

Source-linked project context discovered from existing Feishu metadata and local marketing assets. It is not a product-fact approval.

## 2. Business Objective

Pending Verification. Read the highest-impact canonical sources before setting a formal objective.

## 3. Current Truth

Status: Pending Verification. No product, pricing, positioning, launch, compatibility, or Claim fact was promoted during automated discovery.

## 4. Product Truth

If this is a product project, use Product Knowledge and canonical Feishu sources. Do not copy unverified specifications here.

## 5. Market Truth

Pending Verification. Project sources may contain market/campaign context; verify applicability to Japan before use.

## 6. Consumer Truth

Pending Verification.

## 7. Positioning

Status: Hypothesis / Pending Verification.

## 8. Key Messages

No approved Key Message is stored by automatic discovery.

## 9. GTM Status

Stage is inferred only from source metadata. Review primary GTM/launch sources before declaring execution status.

## 10. Channel Status

Pending Verification. Use project sources and the relevant execution Skill for PR, KOL, Amazon, Rakuten, Yahoo, website, SNS, EDM, LINE, ads, or offline channels.

## 11. Important Dates

Not Available until verified from canonical sources.

## 12. Decisions

See `decisions.md`. No decision is inferred from titles or search summaries.

## 13. Open Questions

- Which source is the current final brief/plan?
- Which current facts can be confirmed for Japan-market use?
- Are any source versions in conflict?

## 14. Risks

- Current discovery is metadata-first; source content may be draft, historical, or market-inapplicable.
- Major-source changes require review before Current Truth changes.

## 15. Next Actions

- P0: Read and classify highest-impact canonical sources.
- P1: Confirm project owner, stage, objective, and current decision records.
- P2: Link durable execution learnings after review.

## 16. Related Skills

{skill_list}

## 17. Sources

{sources}

<!-- PROJECT_MEMORY_SYNC_START -->
## Source Update Notice

- Registry sync: {sync_at}
- Relevant changed sources since prior run: {changed}
- Review status: {review}
<!-- PROJECT_MEMORY_SYNC_END -->
"""


def sources_doc(project, source_map):
    lines = ["# Project Sources", "", "- Total linked sources: %d" % len(project["source_ids"]), "- Full metadata: `../../registry/source_registry.json`.", "", "| Source ID | Title | Type | Updated | Impact | Status |", "|---|---|---|---|---|---|"]
    for source_id in project["source_ids"][:120]:
        source = source_map[source_id]
        lines.append("| `%s` | %s | %s | %s | %s | %s |" % (source_id, cell(source.get("title")), source.get("canonical_type", "unknown"), source.get("updated_at") or "Not Available", impact(source), source.get("catalog_status", "unknown")))
    if len(project["source_ids"]) > 120:
        lines.append("\nOnly the first 120 sources are listed here; use the registry for the rest.")
    return "\n".join(lines)


def decisions_doc():
    return """# Decisions

No confirmed decision has been extracted automatically. Add a decision only with an accepted/final source and preserve superseded entries.

## Decision format

### DEC-XXXX

- Date:
- Topic:
- Decision:
- Previous State:
- Reason:
- Evidence:
- Source:
- Impact:
- Status: Proposed / Accepted / Rejected / Superseded
"""


def templates(output):
    write(output / "templates" / "project_context_template.md", "# Project Context\n\n## Metadata\n\n- Project Name:\n- Project ID:\n- Project Type:\n- Market:\n- Owner:\n- Status:\n- Stage:\n- Last Updated:\n- Confidence:\n\n## Current Truth\n\nStatus: Pending Verification.\n")
    write(output / "templates" / "decision_template.md", decisions_doc())
    write(output / "templates" / "source_template.md", "# Source Record\n\n- Source ID:\n- Title:\n- Canonical URL:\n- Source type:\n- Project IDs:\n- Modified at:\n- Version / content hash:\n- Importance:\n- Confidence:\n- Processing status:\n")


def build(workspace, output, catalog, requested_mode):
    records = [json.loads(line) for line in catalog.read_text(encoding="utf-8").splitlines() if line.strip()]
    source_map = {x["source_id"]: x for x in records}
    state_path = output / "registry" / "update_state.json"
    prior = read_json(state_path, {})
    old_versions = prior.get("source_versions", {})
    versions = {source_id: version(record) for source_id, record in source_map.items()}
    changed = sorted(source_id for source_id, item_version in versions.items() if old_versions and old_versions.get(source_id) != item_version)
    new = sorted(set(versions) - set(old_versions)) if old_versions else sorted(versions)
    grouped = {}
    for record in records:
        for project_id, name, project_type in candidates(record):
            project = grouped.setdefault(project_id, {"project_id": project_id, "project_name": name, "project_type": project_type, "source_ids": []})
            project["source_ids"].append(record["source_id"])
    now_time = datetime.now(timezone.utc)
    projects = [enrich(project, source_map, now_time) for project in grouped.values()]
    projects.sort(key=lambda x: (-x["activity_score"], x["project_id"]))
    formal = [x for x in projects if x["confidence"] in {"High", "Medium"}]
    sync_at = utc_now()
    initial = requested_mode == "initial" or not (output / "PROJECT_INDEX.md").exists()
    project_for_source = defaultdict(list)
    project_by_id = {x["project_id"]: x for x in projects}
    for project in projects:
        for source_id in project["source_ids"]:
            project_for_source[source_id].append(project["project_id"])
    source_registry = []
    for source_id, source in sorted(source_map.items()):
        linked = project_for_source[source_id]
        related = sorted({name for project_id in linked for name in project_by_id[project_id]["related_skills"]})
        source_registry.append({"source_id": source_id, "title": source.get("title", ""), "url": source.get("canonical_url", ""), "source_type": source.get("canonical_type", "unknown"), "project_id": linked, "created_at": source.get("created_at", ""), "modified_at": source.get("updated_at", ""), "first_seen_at": source.get("last_seen_at", ""), "last_checked_at": sync_at, "content_hash": source.get("extract_hash", ""), "version": source.get("source_revision", ""), "importance": impact(source), "confidence": source.get("catalog_status", "unknown"), "related_skills": related, "processed": bool(source.get("extract_path")), "extract_path": source.get("extract_path", ""), "discovery_status": source.get("discovery_status", "Unknown")})

    templates(output)
    write(output / "MEMORY_RULES.md", "# Project Memory Rules\n\n- Feishu is the source of record; Project Memory is structured, source-linked current context.\n- Never copy full source bodies or automatically approve product facts/Claims.\n- Keep FACT, DECISION, HYPOTHESIS, RECOMMENDATION, UNVERIFIED, and OUTDATED separate.\n- Preserve history; supersede rather than delete decisions.\n- Resolve conflicts through review, not silent overwrite.\n- Read the smallest relevant context; do not default-load this repository.\n")
    index = ["# Project Index", "", "| Project | Type | Market | Stage | Status | Last Update | Recent Activity | Source of Truth |", "|---|---|---|---|---|---|---|---|"]
    for project in formal:
        index.append("| [%s](projects/%s/project_context.md) | %s | %s | Discovery / Context consolidation | %s | %s | Score %d; 30d sources %d | `sources.md` + registry |" % (project["project_name"], project["project_id"], project["project_type"], project["market"], project["activity_status"], sync_at[:10], project["activity_score"], project["recent_30_count"]))
    index += ["", "## Project snapshots", ""]
    for project in formal:
        index += ["### " + project["project_name"], "- **Current Focus:** Source-backed project consolidation; formal current truth remains Pending Verification.", "- **Current Truth:** Not automatically promoted. Use canonical sources and Product Knowledge where applicable.", "- **Recent Decisions:** None automatically inferred.", "- **Risks:** %d High/Critical candidate source(s) require review." % project["major_source_count"], "- **Next Actions:** Read highest-impact source and classify any decision or conflict.", "- **Related Skills:** " + ", ".join("`%s`" % name for name in project["related_skills"]), ""]
    write(output / "PROJECT_INDEX.md", "\n".join(index))

    for project in formal:
        directory = output / "projects" / project["project_id"]
        changed_count = sum(source_id in changed or source_id in new for source_id in project["source_ids"])
        context_path = directory / "project_context.md"
        # Never replace manually enriched context. Initial mode creates a
        # missing context; later runs only refresh the delimited sync notice.
        if not context_path.exists():
            write(context_path, context(project, changed_count, sync_at))
        else:
            old = context_path.read_text(encoding="utf-8")
            review = "Review required before Current Truth changes." if changed_count else "No source change detected by this run."
            notice = "<!-- PROJECT_MEMORY_SYNC_START -->\n## Source Update Notice\n\n- Registry sync: %s\n- Relevant changed sources since prior run: %d\n- Review status: %s\n<!-- PROJECT_MEMORY_SYNC_END -->" % (sync_at, changed_count, review)
            write(context_path, re.sub(r"<!-- PROJECT_MEMORY_SYNC_START -->.*?<!-- PROJECT_MEMORY_SYNC_END -->", notice, old, flags=re.S))
        write(directory / "sources.md", sources_doc(project, source_map))
        if not (directory / "decisions.md").exists():
            write(directory / "decisions.md", decisions_doc())
        log = directory / "changelog.md"
        entry = "## %s\n\n- %s\n- Current Truth was not automatically replaced.\n" % (sync_at[:10], "Initial source-linked Project Memory created." if initial else "Registry synchronization; %d relevant source(s) changed since prior run." % changed_count)
        if not log.exists():
            write(log, "# Changelog\n\n" + entry)
        elif not initial and changed_count:
            write(log, log.read_text(encoding="utf-8") + "\n" + entry)

    discovery = ["# Project Discovery Report", "", "- Catalog sources considered: %d" % len(records), "- Formal projects (High/Medium): %d" % len(formal), "- Low-confidence candidates retained but not materialized: %d" % (len(projects) - len(formal)), "", "| Project | Type | Evidence | Related Docs | Recent Activity | Existing Skill | Confidence | Recommendation |", "|---|---|---:|---:|---|---|---|---|"]
    for project in projects:
        evidence = "; ".join(source_map[x].get("title", "") for x in project["source_ids"][:2])
        recommendation = "Create/refresh Project Memory" if project in formal else "Retain as candidate; wait for more evidence"
        discovery.append("| %s | %s | %s | %d | Score %d; 30d %d | %s | %s | %s |" % (project["project_name"], project["project_type"], cell(evidence)[:180], len(project["source_ids"]), project["activity_score"], project["recent_30_count"], ", ".join(project["related_skills"][1:4]), project["confidence"], recommendation))
    write(output / "project_discovery_report.md", "\n".join(discovery))
    review = ["# Memory Update Review", "", "No Current Truth was silently replaced by this run.", "", "| Source | Project(s) | Change | Impact | Required action |", "|---|---|---|---|---|"]
    for source_id in changed[:500]:
        source = source_map[source_id]
        level = impact(source)
        action = "Review before Current Truth update" if level in {"Critical", "High"} else "Classify if new durable context"
        review.append("| `%s` | %s | metadata/content version changed | %s | %s |" % (source_id, ", ".join(project_for_source[source_id]) or "Unmatched", level, action))
    if len(review) == 6:
        review.append("| — | — | No changed source relative to prior state | — | No review proposal |")
    write(output / "memory_update_review.md", "\n".join(review))
    write_json(output / "registry" / "source_registry.json", {"generated_at": sync_at, "source_of_record": "Feishu", "source_catalog": str(catalog), "sources": source_registry})
    write_json(output / "registry" / "project_registry.json", {"generated_at": sync_at, "projects": projects, "formal_project_ids": [x["project_id"] for x in formal]})
    write_json(state_path, {"last_successful_sync": sync_at, "source_catalog": str(catalog), "source_count": len(records), "source_versions": versions, "changed_source_ids": changed, "new_source_ids": new, "mode": "initial" if initial else "incremental"})
    return {"sources": len(records), "projects": len(projects), "formal_projects": len(formal), "changed_sources": len(changed), "output": str(output)}


def check(output):
    required = ["PROJECT_INDEX.md", "MEMORY_RULES.md", "project_discovery_report.md", "memory_update_review.md", "registry/source_registry.json", "registry/project_registry.json", "registry/update_state.json"]
    errors, warnings = [], []
    for name in required:
        path = output / name
        if not path.is_file() or not path.stat().st_size:
            errors.append("Missing or empty: " + name)
    if not errors:
        sources = read_json(output / "registry" / "source_registry.json", {}).get("sources", [])
        source_ids = {item.get("source_id") for item in sources}
        projects = read_json(output / "registry" / "project_registry.json", {}).get("projects", [])
        seen = set()
        for project in projects:
            project_id = project.get("project_id")
            if not project_id or project_id in seen:
                errors.append("Duplicate/missing project id: " + str(project_id))
            seen.add(project_id)
            for source_id in project.get("source_ids", []):
                if source_id not in source_ids:
                    errors.append("Unknown source reference: %s/%s" % (project_id, source_id))
            if project.get("confidence") in {"High", "Medium"}:
                for name in ("project_context.md", "decisions.md", "sources.md", "changelog.md"):
                    if not (output / "projects" / project_id / name).is_file():
                        errors.append("Missing project file: %s/%s" % (project_id, name))
        if not sources:
            errors.append("Source registry is empty")
    return errors, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--mode", choices=("initial", "incremental", "check"), default="incremental")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    output = args.output.resolve() if args.output else workspace / "project-memory"
    catalog = args.catalog.resolve() if args.catalog else workspace / "codex_knowledge" / "source_catalog.jsonl"
    if args.mode == "check":
        errors, warnings = check(output)
        write(output / "validation_report.md", "# Project Memory Validation\n\n- Errors: %d\n- Warnings: %d\n\n## Errors\n\n%s\n\n## Warnings\n\n%s\n" % (len(errors), len(warnings), "\n".join("- " + x for x in errors) or "- None", "\n".join("- " + x for x in warnings) or "- None"))
        print(json.dumps({"errors": len(errors), "warnings": len(warnings), "report": str(output / "validation_report.md")}, ensure_ascii=False))
        return 1 if errors else 0
    if not catalog.is_file():
        raise SystemExit("Source catalog not found: " + str(catalog))
    print(json.dumps(build(workspace, output, catalog, args.mode), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
