# Output Contract V4

## Canonical directory

```text
output/
├── PROJECT_STATE.json
├── spec/
│   ├── PRODUCT_BRIEF.json
│   ├── SELLING_POINT_MATRIX.json
│   ├── PRODUCT_PAGE_SPEC.json
│   ├── ART_DIRECTION_SPEC.json        # derived; never edits Product Page Spec
│   ├── ASSET_RESOLUTION_PLAN.json
│   └── copy_deck.json
├── reference/
│   ├── REFERENCE_SELECTION.json
│   ├── REFERENCE_SELECTION.md
│   ├── REFERENCE_DECISION_TRACE_V2.json
│   ├── REFERENCE_DECISION_TRACE_V2.md
│   └── reference_decision_review.html
├── review/
│   ├── product_understanding_cn.html
│   ├── story_review.html
│   ├── layout_review.html
│   ├── ART_DIRECTION_CONTACT_SHEET.html
│   └── design_review_cn.html
├── preview/
│   ├── amazon_pdp_preview.html
│   └── mobile_preview.html
├── design/
│   ├── product_images/
│   ├── aplus/
│   ├── svg/
│   └── assets/
├── final/                             # only when Publish Gate PASS
│   ├── product_images/
│   ├── aplus/
│   ├── comparison/
│   └── editable/
├── workbooks/
├── export/                            # only when Publish Gate PASS
├── reports/
└── qa/
```

`design/` and `workbooks/` are stable compatibility paths. `final/` and `export/` are conditional handoff views created only when Publish Gate is `PASS`; they are copies, not additional authoring sources. When the gate is `BLOCKED`, both directories must be absent and `reports/FINAL_OUTPUT_NOT_GENERATED.md` must contain exactly `FINAL_OUTPUT_NOT_GENERATED\nReason: Publish Gate BLOCKED`. The lowercase `spec/asset_resolution_plan.json` may be emitted as a deprecated compatibility alias; uppercase is canonical.

## Phase deliverables

- KNOW: Product Brief, product understanding review, project state only.
- REFERENCE: thresholded structural/inspiration selection; not a human Gate. ON is default; OFF remains for regression, troubleshooting and legacy fallback.
- PLAN: Selling Matrix, Product Page Spec with Reference Adapter decisions, 14-item Decision Trace and Story Review; stop at Gate 1.
- DESIGN: Asset resolution/template/layout information and Layout Review; stop at Gate 2.
- ART DIRECTION handoff: after approved DESIGN, derive production briefs and Contact Sheet without adding a phase/gate or changing Story, Claim, Reference, Primitive, rhythm or module count.
- PRODUCE: SVG/JPEG, 8 XLSX, Amazon/Mobile Preview, Design Review and reports. `final/`/`export/` are synchronized only after Publish Gate PASS.

## Consumer Preview

`amazon_pdp_preview.html` simulates the consumer sequence: gallery → Title → 5 Bullets → A+ → purchase checks → FAQ. It must not expose Claim IDs, sources, risk, internal statuses or Chinese production notes. `mobile_preview.html` opens the same source-backed composition at 390px mode.

## Design Review

For every product image and every A+ Unit, show beside the actual render: ID, Consumer Question, Story Role, Main Message, Selected Reference, Reference Role, Decision Reason, Learned Principle, SwitchBot Adaptation, Layout Primitive, Why This Layout, What Was Not Copied and Status. Also show Product/Scene/Graphic layers, asset provenance, Claim IDs/source/status, safe area, mobile rule and publication status. Mobile Design Review uses a compact sticky navigation with Gallery/A+/QA anchors; it must not cover the target headings.

## XLSX contract

Exactly these eight Spec-derived workbooks are required:

1. `visual_composition_plan.xlsx`
2. `selling_point_matrix.xlsx`
3. `product_image_brief.xlsx`
4. `aplus_content_plan.xlsx`
5. `comparison_chart.xlsx`
6. `amazon_seo_keywords.xlsx`
7. `asset_requirements.xlsx`
8. `asset_gap_analysis.xlsx`

They use frozen headers, filters, readable widths/wrapping, status coloring and visible Spec hash. Blank values remain blank; they are not converted to zero. Validate formulas/errors and render at least one preview per workbook.

When Art Direction is generated, `asset_requirements.xlsx` becomes the production brief with Asset ID, Used In, Purpose, Shot/Render Type, Angle, Crop, Resolution, Transparency, Required Product State, Lighting, Scene Requirement, Claim Dependency, Priority, Owner, Status and Fallback. `asset_gap_analysis.xlsx` uses the same Asset IDs for priority/status/fallback/owner tracking. The other six workbooks and the total count of eight remain unchanged.

## Structural and Publish Gates

Structural Gate checks JSON validity, fixed seven-image decision order, 5–8 A+ modules, registered templates, 8 readable workbooks, actual JPEG signatures, editable SVG paths, Spec hash consistency and consumer-page separation.

Publish Gate independently checks:

- Product Accuracy: every product is user-provided official and not AI-generated;
- Claim: every core external Claim has current JP/SKU/channel evidence;
- Copy: Japan Localization Review approved;
- Layout: every visual uses a registered formal template;
- Mobile: browser evidence at 390×844 passes;
- Asset: no fixture, unauthorized temporary file or placeholder enters Final;
- Visual Consistency: SwitchBot Japan Amazon visual review passes.

Asset authorization is proven field by field: `file_resolved`, `source_verified` and `usage_approved` are independent. A file path alone is not approval. `placeholder`, `external_reference`, `generated_scene` and `unknown` are never allowed as Product Layer.

Structural Pass never implies Publish Ready.

Unverified rating/review values render as `—`; the consumer Preview must never invent a star rating or review count.

Reference selection is not Product Truth and cannot approve claims, copy, assets, templates, layouts or publication. Competitor images, copy, UI, logos, trade dress and complete layouts must not enter output or Final.

## Browser QA

Use Desktop 1440×1000 and Mobile 390×844. Check seven thumbnails, at least two thumbnail interactions, seven A+ modules using dedicated mobile assets, Reference Selection/Trace, review navigation, internal-token leakage, missing content, broken images, overflow and console errors. `qa/mobile-readability-gate.json` must pass effective font, line-count, density, collapse, padding, CTA and crop rules; no overflow alone is insufficient. Save screenshots and `qa/browser-qa.json`. Browser absence/timeouts must be reported as `structural_only`.

```bash
node scripts/validate_pdp.mjs --output <output-dir>
node scripts/browser_qa_v4.mjs --output <output-dir> --base-url http://127.0.0.1:<port>
node scripts/attach_browser_qa.mjs --spec <output-dir>/spec/PRODUCT_PAGE_SPEC.json --output <output-dir> --qa <output-dir>/qa/browser-qa.json
node scripts/spec_sync_regression.mjs --spec <output-dir>/spec/PRODUCT_PAGE_SPEC.json --output <output-dir>
```
