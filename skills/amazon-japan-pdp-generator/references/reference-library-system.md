# Amazon Japan PDP Reference Library System

## Purpose

The library turns observed Amazon Japan pages into reusable design-decision knowledge. It does not store competitor production assets and it does not add fixed page templates.

```text
KNOW
→ REFERENCE
→ PLAN
→ Story Gate
→ DESIGN
→ Layout Gate
→ PRODUCE
→ QA
```

REFERENCE is a machine-complete stage, not a human Gate. Story Approval and Layout Approval remain the only two human Gates.

## What a Reference contains

Each `reference-library/references/<ASIN>/reference.json` records:

- observed source and viewport boundary;
- page type and complexity;
- every Product Gallery item's role, consumer question, message, feature, benefit, layout, product scale, density, background, content type and why it works;
- every major A+ container's type, story role, layout, message, density, product/scene/technical presence, interaction and relation to adjacent modules;
- story and visual grammar;
- strengths, weaknesses, USE, ADAPT, AVOID and suitable product conditions;
- a matcher profile.

`analysis.md` is the human-readable view derived from the same JSON. The Viewer embeds only structured observations. It does not embed competitor images or copy.

## Observation boundary

The first library version was inspected on 2026-08-18 in a live Chrome session:

- Desktop: 1440×1000;
- narrow viewport: 390×844;
- the browser automation layer did not expose mobile user-agent switching, and Amazon retained a fixed desktop-width content region in this environment.

Therefore mobile statements must say “390px browser viewport”, not “Amazon mobile site”. This limitation is retained in every Reference JSON.

## Pattern extraction

- `story_pattern_library`: Feature-led, Category Education, Performance-led, Scenario-led and Technology-led decision paths.
- `gallery_sequence_library`: product-type-specific seven-role sequences. These are not seven feature slots.
- `aplus_sequence_library`: A+ continuation patterns that avoid replaying Gallery.
- `layout_primitive_mapping`: audits the existing 19 templates against Hero / Technology / Scenario / Feature / Proof / Comparison / Detail / Closure roles.

Patterns are selection rules, not new templates. Production continues to reference one of the 19 existing `template_id` values.

## Matcher contract

Input: `PRODUCT_BRIEF.json`.

Matching fields and weights:

| Field | Weight |
|---|---:|
| Category | 20 |
| Product Complexity | 8 |
| Primary USP | 18 |
| Consumer Tension | 12 |
| Product Type | 18 |
| Story Requirement | 10 |
| Technical Complexity | 6 |
| Target Audience | 8 |

Missing fields receive zero available signal and are reported explicitly. The score is normalized against available input weight; the matcher never fabricates a value. At least 40/100 signal weight is required. Below that threshold the artifact is emitted as `blocked_insufficient_brief`, no arbitrary Top 3 is returned, and PLAN remains blocked.

Output:

- Top 3 with score and field-level evidence;
- why each Reference was selected;
- what to borrow;
- what not to borrow;
- a combined Structure / Technology Explanation / Visual Rhythm / SwitchBot Brand strategy.

```bash
node scripts/reference_matcher.mjs \
  --brief <output>/spec/PRODUCT_BRIEF.json \
  --output <output>
```

The orchestration form is:

```bash
node scripts/run_phase.mjs --output <output> --phase reference
```

PLAN reads `reference/REFERENCE_SELECTION.json`, applies the Reference Decision Adapter, and writes `REFERENCE_DECISION_TRACE_V2.{json,md}`. Reference must affect Gallery/A+ story, sequence or layout; metadata-only use is under-utilization and blocks ON mode. Every decision passes Role Match, Renderer Availability, 390px Mobile Readability and Claim Provenance before entering the Spec. A Reference rerun invalidates downstream PLAN/Story/DESIGN/Layout/PRODUCE status because the story basis changed.

The Adapter may select and apply structure only before Story Approval. Once the Story sequence fingerprint is locked, it may annotate, map and enrich the approved Gallery/A+ records but may not reorder, insert, delete, merge or split them. Any structural Reference change requires an explicit Story reset, PLAN rerun and renewed approval; silent post-approval mutation is a hard failure.

Structural selection also requires Same Category, Minimum Match Score, Product Role Match and Page Intent Match. Cross-category or low-match candidates remain inspiration-only and cannot change Gallery/A+ structure or module order. If signal weight is insufficient, Top 3 is not forced; if no structural Reference remains, ON mode blocks PLAN. `REFERENCE=OFF` skips Matcher/Adapter for regression, troubleshooting and backward-compatible legacy execution.

## Non-copy rule

Allowed:

- consumer-decision sequence;
- information architecture;
- density and whitespace principles;
- scene/technical rhythm;
- Visual Role suitability;
- failure modes and adaptation requirements.

Prohibited:

- competitor copy or translated copy;
- competitor images or image recreation;
- brand colors, typography, card shapes or other trade dress;
- logos, awards, UI or technical diagrams;
- a complete competitor layout or module sequence copied as a page.

All Product Truth, Claims, Japanese copy, official Product Layers, Graphic Layers and production templates remain SwitchBot-owned inputs governed by the existing V4 system.
