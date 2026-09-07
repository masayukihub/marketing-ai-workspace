# Visual Quality System

## Boundary

This layer changes only deterministic rendering parameters inside the existing 19 Layout Primitives. It must not change Product Knowledge, Claims, Reference selection, Story sequence, Template IDs, asset provenance, Gallery/A+ counts, workbooks, human Gates or Publish Gate.

`VISUAL_QUALITY=ON` is the production default. Set `VISUAL_QUALITY=OFF` only for regression or troubleshooting. Registered Reference renderers retain composition priority on desktop and mobile; quality presets are fallbacks and must not silently replace the selected Reference primitive.

## Visual Roles

- IMPACT: establish identity or value with dominant focus.
- EXPLAIN: connect one mechanism to one shopper consequence.
- DETAIL: organize parallel facts that answer the same question.
- BREATHE: lower density for a Story reason, never decorative emptiness.
- SCENARIO: prove household fit or routine using an allowed Scene Layer.
- PROOF: keep source conditions adjacent to the mechanism.
- COMPARE: help selection; do not create superiority theatre.
- CLOSURE: resolve the final objection with a quiet product anchor.

## Rhythm Detection

Check Gallery and A+ separately for three or more consecutive repeats of:

- background family;
- layout family;
- product position;
- card structure;
- information density;
- product scale.

Emit `VISUAL_RHYTHM_WARNING` for every run. A retained run requires a recorded Decision Reason proving that continuity serves the Story. Never randomize layouts or backgrounds to remove a warning.

## Gallery vs A+

Gallery accelerates a purchase decision: one image, one main message, strong product/benefit hierarchy and square mobile-safe composition.

A+ builds understanding and trust: alternate mechanism, proof, detail, ownership/scenario, comparison and closure. If the same composition/copy/card grammar simply enlarges Gallery content, emit `GALLERY_APLUS_REDUNDANCY_WARNING`.

## SwitchBot Brand Fit (INFERRED)

Until an approved comprehensive Brand Guideline is provided, treat these as inferred production rules:

- product first;
- smart but approachable;
- functional clarity;
- believable Japanese home scale;
- everyday benefit after technical explanation;
- restrained white, mint and warm-neutral expression;
- consistent typography and programmatic Graphic Layer;
- scene/product balance without AI-generated product bodies.

Reference learning may change information rhythm, but must never import competitor copy, imagery, logo, UI, Trade Dress or complete layout. Use `KEEP STORY PRINCIPLE / CHANGE VISUAL EXPRESSION` when structural learning is useful but competitor likeness risk is high.

## Anti-template Rules

- Rounded cards cannot be the default treatment for Proof, Detail, Comparison and Closure.
- Mobile cannot use one universal card stack for every A+ module.
- Equal spacing, centered composition, identical product scale and three-card grids require a semantic reason.
- Internal fixture, approval and Pending phrases cannot be promoted into consumer artwork; keep them in Spec and Design Review.
- Low-density space is valid only for BREATHE or CLOSURE with a clear conversion task.

## Output and QA

ON writes `reports/VISUAL_QUALITY_MANIFEST.json`, including Visual Role and deterministic parameters. Rhythm scores describe planned metadata only. Brand Fit and Template Feeling remain `NOT_ASSESSED` until the actual files are inspected; ON/OFF is not image evidence. Any Story, Claim, Asset, Mobile, renderer or Publish hard failure remains blocking. Use [creative-review-record.md](creative-review-record.md) for observed findings.

Required regression freezes Product Brief, Claims, Reference Selection, Story Lock, sequence, Template IDs and Asset Resolution, then compares Baseline vs ON. Browser QA must cover Gallery, full A+, Design Review and Before/After Review at desktop and 390×844.
