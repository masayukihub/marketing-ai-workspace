# Spec + Template Production System

## Canonical flow

```text
Intake + canonical facts
  → PRODUCT_BRIEF.json                 (KNOW)
  → REFERENCE_SELECTION.json           (REFERENCE; design-decision input)
  → SELLING_POINT_MATRIX.json          (PLAN)
  → PRODUCT_PAGE_SPEC.json             (PLAN; sole page source)
  → ASSET_RESOLUTION_PLAN.json         (DESIGN)
  → HTML / SVG / JPEG / XLSX / Review  (PRODUCE)
```

`PRODUCT_BRIEF`, `REFERENCE_SELECTION` and `SELLING_POINT_MATRIX` are upstream planning records. With REFERENCE=ON, PLAN must apply the Decision Adapter and persist traceable Story/Layout/Sequence decisions in `PRODUCT_PAGE_SPEC.json`; a metadata-only snapshot is not sufficient. Once the Spec is persisted, every page, design, workbook, SEO export and review output must read that persisted Spec, not the intake file or parallel copy deck.

Reference selection never becomes a product fact source. It controls story architecture, information density and visual rhythm only; competitor copy, images, trade dress, UI and complete layouts are prohibited.

`copy_deck.json` and `ASSET_RESOLUTION_PLAN.json` are derived convenience views. They must carry the same `spec_sha256` and must never become a competing content source.

## Phase boundaries

| Phase | May read | May create/update | Forbidden |
|---|---|---|---|
| KNOW | intake, canonical facts, official asset inventory | Product Brief, understanding review, state | image plan, A+, AI scene, final render |
| REFERENCE | Product Brief, Reference Library | Top 3 Reference selection and combined strategy | claims, copy, product facts, assets, templates, human approval |
| PLAN | Product Brief, Reference Selection, intake structure | Selling Matrix, Product Page Spec, Story Review | high-fidelity render |
| DESIGN | approved Story Spec, template library, official assets | Asset Resolver, template mapping, Layout Review | final scene production before Layout approval |
| PRODUCE | approved persisted Spec and asset mapping | SVG/JPEG/XLSX/Preview/Design Review/reports | manual flattened-only edits |

## Gate state

`PROJECT_STATE.json` records `current_phase`, all phase statuses, Story Gate, Layout Gate, QA and Publish Gate. A human or explicit internal regression approval updates both state and the matching `spec.human_gates` record.

- Story not approved: DESIGN and PRODUCE stop.
- Story approved: persist a Gallery/A+ sequence fingerprint. Adapter/DESIGN/PRODUCE may enrich records but may not reorder, insert, delete, merge or split. A structural change requires explicit Story reset, PLAN rerun and re-approval.
- Layout not approved: PRODUCE stops.
- `--force`: emits a persistent risk warning and is never publication approval.
- Publish `BLOCKED`: `final/` and `export/` are absent; review/design artifacts remain available. Publish `PASS`: handoff directories are synchronized from the persisted Spec.

## Template contract

Each registered template lives under `templates/amazon/<template>/` and contains:

- `template.json`: machine-readable rules and historical references;
- `template.html` + `template.css`: editable layout contract;
- `template.svg`: editable structural wireframe;
- `preview.jpg`: review thumbnail;
- `README.md`: usage and layer rules.

Each page visual references a fixed `template_id` and a frozen `template_snapshot`. Updating the registry does not silently change an approved project; intentionally rebind the snapshot and rerun Layout Approval.

## Change impact

- Copy change: affected visual copy/layout/render plus shared HTML/XLSX; no KNOW rerun.
- Scene mapping change: affected visual render and asset records plus shared reviews; no product-fact rewrite.
- Sequence change: reset Story Gate, unlock, rerun PLAN and reapprove; ordered Spec arrays, HTML and workbooks then update together.
- Claim change: all consumers of that Claim are reported and marked for Story/Copy/Claim re-review.

All regenerated files must be deterministic for an unchanged Spec. A changed `spec_sha256` proves content changed; it does not by itself prove publication readiness.
