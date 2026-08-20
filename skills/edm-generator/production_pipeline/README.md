# Phase 6 One-shot Production Pipeline

The production pipeline is additive to Frozen Generator Logic v1.0 and the Frozen Design System v1.0.

Run both pilots:

```sh
ruby production_pipeline/run_one_shot.rb
```

Run one input:

```sh
ruby production_pipeline/run_one_shot.rb production_pipeline/inputs/pilot_a_lock_ultra.yaml
```

Decision path:

`One-shot input → Product Knowledge adapter → Campaign Truth → audience/complexity → brand mode → Length Engine → frozen Template selection → module composition → Japanese copy → Asset Resolver → HTML → fail-closed QA`

The pipeline may render an `INTERNAL_DRAFT` when the structural inputs are sufficient, but it may not promote that render to `PRODUCTION_READY` until Approved External Claim, production-scope product assets, legal/footer approval and ESP runtime links are all present.

Finalize QA after browser rendering:

```sh
ruby production_pipeline/finalize_qa.rb
ruby production_pipeline/static_qa.rb
```

Build the combined Human Review page:

```sh
ruby production_pipeline/build_review_page.rb
```

Browser automation scripts require the project HTTP server and the bundled Playwright runtime. `browser_qa.js` verifies each EDM at 320/375/390/414/768px; `review_browser_qa.js` verifies the combined page, blank Human Review fields and CSV export at 320/375/414/768/1280px.
