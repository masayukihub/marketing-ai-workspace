# Amazon Japan Visual Layout System

## Shared rules

- Canvas: product images 2000×2000; Premium-style A+ master 1464 px wide unless the live Builder requires another exact size.
- Grid: 80–120 px outer safe area on 2000 px canvases; align all type and cards to one grid.
- Visual center: product first, one message second, proof third.
- Hierarchy: Level 1 Headline; Level 2 one benefit sentence; Level 3 zero to four proof/spec items.
- Typography: natural Japanese sans serif; Headline 72–96 px on 2000 px, Sub Copy 32–42 px, proof 24–32 px. A+ sizes scale to module height.
- Headline: prefer 5–15 Japanese characters; allow up to 28 only after mobile and line-break QA.
- Avoid stage labels, internal workflow labels, excessive icons, dense paragraphs and decorative effects that resemble an AI poster.

## Product image layouts

| Formal template_id | Name | Structure | Default job |
|---|---|---|---|
| P-MAIN-OFFICIAL | Main Image | Pure white, centered official product, no marketing copy | Image 1 / Product recognition |
| P-HERO-SPLIT | Hero Split | 38–40% copy + 60–62% official product | Image 2 / Why buy |
| P-FEATURE-CENTER or P-FEATURE-SPLIT | Feature | Centered proof or controlled 50/50 | Image 3 / Core mechanism |
| P-LIFESTYLE-FULL | Lifestyle | Large believable scene + short safe-area headline | Image 4 / Real use scenario |
| P-TECHNICAL-PROOF or P-ECOSYSTEM | Technical / Ecosystem | Official render + sourced proof / verified relationships | Image 5 / Trust |
| P-COMPARISON | Comparison / Fit | Uniform grid/table and current sourced values | Image 6 / Fit |
| P-PURCHASE-CONFIDENCE | Purchase Confidence | Product/in-box + up to three checks | Image 7 / Objection removal |

Default seven-image sequence:

```text
Image 1 P-MAIN-OFFICIAL — What is it?
Image 2 P-HERO-SPLIT — Why buy?
Image 3 P-FEATURE-CENTER — Why is the core mechanism useful?
Image 4 P-LIFESTYLE-FULL — How does it work in real life?
Image 5 P-TECHNICAL-PROOF — Why trust it?
Image 6 P-COMPARISON — Does it fit me?
Image 7 P-PURCHASE-CONFIDENCE — What must I confirm before purchase?
```

Use only a registered formal `template_id`. The library may also contain Feature Split and Ecosystem alternatives, but switching them requires Layout Approval and must preserve the decision order.

## Wireframe contract

Every wireframe must label:

- Level 1, Level 2 and Level 3 regions;
- official Product Layer region and target product share;
- Scene Layer and empty composition space;
- Graphic Layer cards, labels or diagram;
- desktop and mobile safe areas;
- visual center and intended eye path.

Wireframes are internal editable SVG files. Do not expose them in Amazon Preview.
