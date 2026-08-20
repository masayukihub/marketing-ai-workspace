# SwitchBot Historical EDM Template Library v1.0

This layer makes Historical Template selection the default visual route.

## Decision budget

- 70%: inherit the selected Historical Template skeleton.
- 20%: adapt only declared `FLEXIBLE` regions.
- 10%: fill a documented gap or enter a new-design candidate route.

The ratio is a design-decision budget, not random traffic allocation.

## Build and validate

```bash
ruby historical_templates/build_library.rb
ruby generator/historical_template_renderer.rb tests/historical_template_test_cases.yaml
node historical_templates/browser_qa.js
ruby historical_templates/build_validation.rb
node historical_templates/review_page_qa.js
ruby historical_templates/static_qa.rb
```

`browser_qa.js` and `review_page_qa.js` use local Google Chrome. Generated
Promotion fixtures remain internal and may not render unverified prices,
discounts or periods.

## Runtime use

```bash
ruby generator/historical_template_matcher.rb path/to/normalized_brief.yaml
```

The Matcher returns Top 1/2/3, dimensional scores, reusable regions and required
adjustments. Generic generation is not allowed unless Top-1 is below 50, the
campaign genuinely needs a new structure, or the user explicitly requests one.

## Promotion loop

A generated output does not auto-promote. It may enter the next version of the
Historical Library only after actual launch or a `DELIVERABLE` Human Decision,
with full visual, source/asset traceability and Hard Rule QA.
