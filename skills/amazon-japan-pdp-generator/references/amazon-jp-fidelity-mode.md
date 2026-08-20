# Amazon Japan Fidelity Preview Mode

Use this mode only when the user needs consumer-facing Amazon Japan page fidelity, above-the-fold comparison, Premium A+ simulation, or browser fidelity QA. It does not change Product Truth, Story, Claims, Reference decisions, Primitive mapping, Gates, workbook structure or final publish eligibility.

## Contract

- Invocation: `PREVIEW_MODE=AMAZON_JP_FIDELITY`.
- Single source: the approved or review-state `spec/PRODUCT_PAGE_SPEC.json`.
- Coexists with internal Amazon Preview, Mobile Preview, Design Review and Art Direction Review.
- Consumer Preview contains no internal Dashboard, status chip, score panel, Source ID, Claim ID, review control or test fixture.
- Missing commerce data renders fail-closed as `—` or `情報なし`.
- Public Amazon observations are `LIVE_REFERENCE_ONLY`; never write them back into Product Truth or Claim data.

## Page structure

Render the Amazon shell, search/header, breadcrumbs, Gallery thumbnails and main image, Title/store/rating/price area, Bullet list, Buy Box, Product Description, Premium A+ full-width/overlay/carousel modules, product comparison and FAQ. Use the existing seven Gallery images and existing seven A+ modules; do not add a Primitive or change Story order.

Premium A+ uses the existing 1464px desktop masters and the existing mobile derivatives. Carousel controls and pagination must work through programmatic HTML/JS. Consumer copy remains programmatic Graphic Layer; product imagery remains official-only under the project provenance status.

## Responsive behavior

- Desktop evidence viewport: 1440×1000.
- Mobile evidence viewport: 390×844.
- At 390px, the above-fold columns stack, thumbnails remain operable, A+ overlay text remains visible, comparison can use its own scroll container, and the document itself must not overflow horizontally.
- All A+ Unit headline/body/condition/annotation content remains present and untruncated through the Mobile A+ Render Contract.

## Browser QA

Check in a real browser:

1. console errors = 0;
2. broken image = 0;
3. document horizontal overflow = 0;
4. missing consumer content = 0;
5. Gallery switching changes the main image;
6. A+ previous/next and pagination change the active slide;
7. minimum effective font size and 390px readability pass;
8. desktop/mobile screenshots are captured at the declared viewport.

A native Amazon mobile page or app must not be claimed when only a 390px desktop Chrome viewport was observed.

## Hard failure priority

Semantic correctness, Mobile content completeness, Product Truth and existing Safety/Publish Gates precede platform similarity and visual polish. A fidelity score cannot override a hard failure.
