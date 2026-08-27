---
name: product-knowledge
description: Use the SwitchBot Japan Product Knowledge Hub to retrieve, verify, update, and apply traceable product marketing knowledge. Use whenever a task mentions a SwitchBot product, alias, SKU, model, variant, bundle, or series, or needs PR, EDM, LP, Amazon/Rakuten/Yahoo content, SNS, App Push, KOL/media briefs, product-page review, pricing, claims, compatibility, FAQ, competitor analysis, launch planning, sales training, VOC analysis, or product-level campaign review. Treat Feishu as the primary knowledge source and this Skill as the normalized, governed single source of truth for reusable facts and marketing guidance.
---

# Product Knowledge Hub

Use this Skill as the SwitchBot Japan product-fact gate and reusable marketing knowledge hub.

## Project context preflight

When the request names an existing repository project, first consume the `project-context-resolver` Context Package. Use its identity, stage, blockers, and Product Truth pointer; then apply this Skill's canonical fact checks. The Manifest never approves a product fact or Claim, and projectless product lookup continues to use the normal entity index.

## Architecture

- **Feishu** is the primary discovery and evidence source. Search it before asking the user to download documents.
- **`references/`** is the canonical normalized fact layer. It retains source IDs, revisions, markets, validity dates, approval status, and historic records.
- **`knowledge/`** is a generated, readable reuse layer for marketers. It never overrides `references/`.
- **`snapshots/`** holds incremental discovery state and Change Sets, not copies of Feishu documents.
- **`outputs/`** provides runtime indexes and validation results for downstream Skills.

## Retrieve or write marketing content

1. Resolve the entity in `outputs/product_index.json`. Use `identifier_lookup` for ASIN, SKU, JAN, or model number before exact normalized aliases. Keep `product_id`, `variant_id`, and `bundle_id` distinct. Never fuzzy-match unknown or excluded aliases.
2. Read `knowledge/products/<product_id>.md` for fast internal orientation, then verify the necessary canonical records:
   - Always: `product_master.xlsx`, `product_facts.xlsx`, `claim.md`, `compliance.md`, `known_issues.md`, and the product Profile.
   - Price: `pricing.xlsx`; comparison: `competitor.xlsx`; ecosystem: `compatibility.xlsx`; detailed parameters: `product_specs.xlsx`; channel copy: `product_positioning.xlsx`; support: `faq.md`.
3. Confirm Japan applicability, source and revision, review status, dates, firmware, dependencies, limitations, and unresolved conflicts.
4. Use only supported facts. State missing information as `未确认`, `Pending Verification`, or `需要补充官方资料`.

## Update Product Knowledge

For `更新Product Knowledge`, `更新<产品>产品资料`, or any request to refresh a product:

1. Start incrementally. Read `config/product_mapping.yaml`, `config/source_priority.yaml`, `config/update_rules.yaml`, and the latest snapshot. Use a full refresh only when explicitly requested or when the structure changes.
2. Search the registered Feishu folder and relevant Feishu content using the product's English, Japanese, Chinese, historical, model, alias, feature, and launch terms. Use multiple queries such as product + `仕様`, `PR`, `FAQ`, `KOL`, `media`, `launch`, `企画`, `比較`, and `competitor`.
3. Register only source metadata and extract atomic proposals with source ID, revision, evidence location, market, conditions, and validity dates. Do not copy whole Feishu documents into the Skill.
4. Apply an explicit, current, JP-applicable P1 fact only when it is non-conflicting. Queue prices, promotions, performance, AI/privacy, firmware, compatibility, certification, award, competitors, and all Claims for review unless already approved under the policy.
5. Preserve old facts by closing `valid_to`; never overwrite history or silently resolve conflicts. Run `build_change_set.py`, record the snapshot, regenerate the knowledge layer and runtime index, and report changes, conflicts, staleness, and missing sections.

Use `docs/feishu_sync_contract.md` for the extraction payload and review boundary.

## Fact and claim rules

- Use `product_facts.xlsx` for atomic feature ownership and state. A bundle capability does not become a capability of every component.
- Keep `subject_product_id`, `capability_owner_product_id`, and `required_product_id` distinct.
- Treat `released`, `beta`, `announced`, `firmware_required`, `region_limited`, `unsupported`, and `unknown` as different states.
- Preserve performance conditions for battery life, speed, noise, accuracy, coverage, suction, and similar measurements.
- Use only `Approved` claims directly in external copy. Include all conditions for `Conditional` claims. Block `Pending Verification`, `Internal Only`, `Prohibited`, and `Expired` claims from external factual output.
- Treat `validation_status: pass` as structural integrity only. External copy also requires the product-level `external_publish_ready` flag and an Approved Claim whose source allows external use.
- Do not generate or endorse unsupported superlatives such as industry first, most advanced, absolutely safe, 100% accurate, fully automatic, or maintenance-free.

## Price rules

- Match product, market, channel, price type, currency, tax basis, and effective date.
- Never substitute Amazon, Rakuten, Yahoo, official-store, coupon, bundle, launch, or campaign prices for one another.
- Treat expired prices as historical. Missing price is not zero.

## Conflict behavior

When user-provided information differs from the knowledge base, report:

```markdown
## 产品信息冲突

| 项目 | 用户提供 | 知识库记录 | 来源 | 最后确认日期 |
|---|---|---|---|---|
| <field> | <user value> | <verified value or 未确认> | <source_id> | <date> |
```

Do not silently choose or overwrite a conflicting value. If the knowledge base has no verified value, state `未确认` rather than treating the user value as confirmed. Source priority may guide review order, but unresolved conflicts remain explicit.

## Validation and updates

Before relying on the index after knowledge changes, run:

```bash
"$PYTHON" scripts/validate_product_data.py --skill-dir . --output outputs/validation_report.md
"$PYTHON" scripts/check_conflicts.py --skill-dir . --as-of <YYYY-MM-DD>
"$PYTHON" scripts/build_product_index.py --skill-dir .
"$PYTHON" scripts/check_copy_claims.py --skill-dir . --input <draft.txt> --output outputs/claim_lint_report.md
"$PYTHON" scripts/build_knowledge_hub.py --skill-dir . --write-baseline-snapshot
"$PYTHON" scripts/discover_feishu_sources.py --skill-dir . --product-id <product_id>
```

Use the Python executable returned by `load_workspace_dependencies`. Run `update_last_verified.py` without `--apply` first; it requires a source or product selector plus a source revision.
The copy linter is a fail-closed screen for unsupported product, numeric-performance, capability-owner, comparison, launch, and universal-compatibility language. A clean lint does not itself approve copy.

Run `discover_feishu_sources.py --execute` only when Feishu credentials are available. It is read-only and generates a source snapshot; compare it with `build_change_set.py` before extracting or applying facts.

Read [README.md](README.md) only when maintaining the knowledge base. Read templates only when creating profiles, comparisons, or claim checks.

## Completion check

- Every non-empty factual value has a `source_id`.
- No critical validation or unresolved critical conflict remains.
- External copy uses only allowed claims with conditions.
- Unknown product, price, firmware, region, and compatibility details remain explicitly unknown.
- Generated marketing knowledge is traceable, current enough for its information type, and does not become an external Claim by itself.
