# Phase 5 Pilot Renderer

This renderer is a bounded visual-production layer. It does not decide campaign strategy or invent product truth.

## Inputs

1. Generator campaign brief and frozen template/module IDs.
2. `standards/edm_design_rules_v1.0.yaml`.
3. `design_system/*_v1.0.*`.
4. Pilot Truth Pack and Asset Manifest.
5. Verified copy records and real CTA destinations.

## Pipeline

`Truth Gate → render spec → component composition → 600px HTML → responsive reflow → browser screenshots → QA`

`renderer/core/dependency_context.rb` loads and validates the frozen Standard, Template Library, Module Library, selection/composition rules, visual-rhythm rules and each Pilot campaign brief before any output is rebuilt. The renderer may consume those IDs and constraints; it cannot redefine campaign type, template selection or product truth.

## Boundaries

- Product and device UI pixels are never redrawn or reconstructed.
- AI-generated assets are not used in this pilot.
- CONDITIONAL renders are marked `社内検証用` and are not production deliverables.
- BLOCKED cases receive evidence-labelled wireframes only.
- Frozen Design Standard and Design System files are read-only dependencies.

## Run

```sh
ruby renderer/render/build_pilots.rb
ruby renderer/qa/static_check.rb
```

## SwitchBot Brand Layer (Phase 5.5)

For `brand = SwitchBot` and `market = Japan`, the additive Brand Context defaults to:

```yaml
render_mode: switchbot_brand
```

This mode reads `brand_system/switchbot_composition_rules_v1.0.yaml` and does not overwrite the Frozen Design Standard or Design System v1.0.

```sh
ruby renderer/render/build_brand_pilots.rb
NODE_PATH=/Users/lai/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules \
  /Users/lai/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  renderer/qa/phase5_5_brand_browser_qa.js
```

Brand V2 outputs are written under `pilot/P02/brand_v2/` and `pilot/P04/brand_v2/`. They remain `CONDITIONAL` internal calibration assets until Product Knowledge and the production footer/legal package are approved.
