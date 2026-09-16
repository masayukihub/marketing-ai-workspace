# Page Unit Contract

Every full-page Amazon plan must describe each unit with the same consumer-facing contract before rendering.

```yaml
unit_id:
unit_type: gallery | aplus | carousel | native_copy | brand_story | series_comparison | faq
consumer_question:
story_role:
message:
consumer_takeaway:
evidence:
visual_proof:
copy:
asset_bindings:
mobile_strategy:
publishability:
status:
```

Rules:

- `consumer_question` is mandatory for every unit.
- `message` is one primary message; supporting details stay secondary.
- `evidence` must point to confirmed Product Truth / Approved Claim / formal source.
- `visual_proof` is mandatory for mechanism/evidence-led units.
- `publishability` separates internal-only research from Amazon-ready content.
- Brand Story and Series Comparison must use their dedicated contracts.
- Native fields must remain native when appropriate; do not rasterize long copy or tables solely for visual consistency.
- Reusing the same Product Layer is allowed; reusing the same final composition across multiple story roles requires explicit justification.
