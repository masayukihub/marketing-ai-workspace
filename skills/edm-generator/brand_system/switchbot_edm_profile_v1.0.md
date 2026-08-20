# SwitchBot Japan EDM Brand Profile v1.0

Status: **Phase 5.5 calibration layer**  
Scope: Tier A Approved SwitchBot Japan EDM only  
Dependency rule: This profile is additive. It does not modify or replace Frozen Design Standard / Design System v1.0.

## 1. Evidence baseline

The primary calibration set is eight Tier A Approved / Anchor messages whose exact Gmail HTML and official CDN image slices were recovered. They were browser-rendered at a 600px desktop canvas and measured from the resulting document height.

- Primary evidence: `SBG_001`, `SBG_003`, `SBG_005`, `SBG_006`, `SBG_007`, `SBG_016`, `SBG_019`, `SBG_020`
- Browser measurement: `output/playwright/phase5_5/approved_measurements.json`
- Structural records: `brand_system/switchbot_approved_reverse_engineering_v1.0.yaml`
- Visual evidence: `output/playwright/phase5_5/approved/*_recovered.png`
- The empty 1×1 tracking GIF in every recovered email is ignored. All meaningful visual assets loaded.
- Some historical messages are fixed-width and overflow below 600px. That is evidence of the old delivery implementation, not permission to copy the non-responsive behavior.

Two counts are intentionally kept separate:

1. **Section count**: macro reader stages such as Hero, Product Story, Comparison, Commerce and Footer.
2. **Module count**: actual top-level `mc:repeatable` composition blocks recovered from the source email. A Product Grid may contain several nested cards, so the module count still understates individual content units.

This distinction is essential. Phase 2's semantic module labels were useful for classification, but they hid how many real visual blocks were used to make the email feel complete.

## 2. Length profile

| Metric | Browser-measured result |
|---|---:|
| Shortest Approved Anchor | 4,797px (`SBG_019`) |
| Median Approved Anchor | 7,072px |
| Longest Approved Anchor | 12,863px (`SBG_007`) |
| Macro sections | 8–10; median 9 |
| Top-level composition modules | 10–22; median 12 |
| Meaningful image assets | 16–40; median about 30 |
| CTA instances | 4–9; median 5.5 |

| Reference | Campaign | Length | Sections | Composition modules | CTA |
|---|---|---:|---:|---:|---:|
| SBG_001 | Product Launch / Ecosystem | 7,043px | 9 | 22 | 5 |
| SBG_003 | Education / User Voice Hybrid | 6,599px | 10 | 10 | 9 |
| SBG_005 | Countdown / Last Chance | 7,101px | 9 | 13 | 8 |
| SBG_006 | Security Theme Promotion | 8,913px | 10 | 18 | 8 |
| SBG_007 | Dual-product Launch | 12,863px | 8 | 11 | 4 |
| SBG_016 | Product-led Air Purifier Promotion | 6,448px | 9 | 11 | 5 |
| SBG_019 | Product Launch | 4,797px | 10 | 11 | 6 |
| SBG_020 | Brand Story / Category Guide | 8,397px | 9 | 22 | 5 |

### Decision

“Shorter is better” is not a valid SwitchBot default. The shortest measured Anchor is still a ten-stage journey with eleven composition blocks. Long-form is legitimate when the message contains distinct products, scenarios, mechanisms, comparisons, proof, offers or purchase questions.

Length is not a target by itself. It is the result of:

`Campaign complexity × Product complexity × Verified information requirement`

## 3. Information density

### Hero

Approved SwitchBot heroes usually establish more than a decorative mood. They combine two or more of the following:

- recognizable product or product family;
- campaign/product identity;
- one clear value or problem;
- launch, offer or deadline when relevant;
- a direct action when the campaign is conversion-led.

The hero is allowed to be visually tall, but it is not allowed to become a generic lifestyle billboard where the product is difficult to identify.

### Middle depth

The middle third is where the current generic renderer is weakest. Approved SwitchBot EDMs commonly use:

- 3–6 distinct feature, mechanism, detail or scenario units for a complex product;
- repeated product presence after lifestyle or editorial relief;
- product-by-product chapters instead of one compressed Product Grid;
- compatibility, installation, UI, comparison or FAQ content when the purchase decision needs it;
- a proof or trust layer when valid evidence exists;
- a separate commerce stage after product understanding.

Seven of the eight Anchors combine product-only imagery with lifestyle or use-case imagery. The exception is the commerce-led last-chance email (`SBG_005`), which uses product groups and offer changes to create rhythm.

### CTA behavior

Approved messages often contain a second or later CTA, but the repetition is purposeful:

- different products have different destinations;
- the same destination returns after a new information stage;
- a mid-course action answers a different task from the final action;
- a final deadline reminder repeats a verified campaign condition.

CTA count alone is not a target. A duplicate button after no new information is a failure.

### Long-form education

Long education is supported when distinct questions are answered in order:

`Problem → Product answer → Mechanism → Feature/detail → Scenario → UI/compatibility → Objection/proof → Action`

If verified truth, proof or official assets are missing, the renderer must stop expanding. It must not paraphrase the same value to simulate completeness.

## 4. SwitchBot brand rhythm

The recurring rhythm is not one fixed template. It is a controlled alternation of evidence roles:

`Product identity → Lifestyle/use case → Feature/mechanism → Product detail/UI → Scenario/choice → Proof when verified → Commerce/action → Deep footer`

What makes it feel like SwitchBot:

1. **Products keep returning.** Product bodies, product families or official UI remain visible throughout the middle, not only in the Hero.
2. **Lifestyle is a bridge.** It shows why a capability matters, then hands the reader back to product evidence.
3. **Feature depth is visual.** A complex product receives several large, distinct feature/detail blocks rather than a dense icon row alone.
4. **Commerce follows understanding.** Price, coupon and CTA may appear early in a promotion, but the email still explains what is being bought.
5. **Repetition changes role.** Repeated blocks correspond to a new product, scenario, proof item or action stage.
6. **The footer is a real closing stage.** Campaign conditions, service/channel paths, proof/legal and brand/subscription closure create a deep ending.

Campaign-specific art direction may change dramatically—security, neon lighting, pet care, air purification or Prime Day—but those six structural habits remain recognizable.

## 5. Comparison with Frozen Templates

Frozen Template v1.0 remains a valid decision skeleton, but it is too coarse to act as a SwitchBot production composition by itself.

| Dimension | Frozen templates | Approved SwitchBot reality |
|---|---|---|
| Default sequence | 7–8 semantic slots | 8–10 macro stages and 10–22 composition blocks |
| Feature expansion | Often one Feature/Detail slot | Multiple mechanism, feature, detail, scenario or compatibility beats |
| Product presence | Hero plus one Detail/Grid | Re-enters repeatedly across the middle and commerce stages |
| Multi-product | One Product Grid | Several themed product groups or product chapters |
| CTA | Usually one closing CTA | 4–9 instances tied to products, stages or destinations |
| Footer | One Brand Footer slot | Deep campaign/legal/channel/brand closure |
| Visual cadence | Uniform module list | Campaign-specific alternation of full visual, dense explanation, product reset and action |

The required correction is an additive **SwitchBot Brand Layer**, not a destructive rewrite of Frozen v1.0.

## 6. Length governance

These are Soft ranges, never Hard Rules:

- **Compact: 5–7 core modules** — familiar product, one task, low information burden.
- **Standard: 8–11 core modules** — multiple purchase questions or moderate education.
- **Long-form: 12–18 core modules** — complex smart hardware, several distinct scenarios/products, or substantial mechanism/compatibility/proof needs.

Header and internal validation notices are excluded from the count. Footer is included.

## 7. Product complexity

- **LOW**: familiar category, one use case, little setup/compatibility education.
- **MEDIUM**: several differentiators/use cases, moderate setup or comparison burden.
- **HIGH**: complex smart hardware requiring mechanism, installation, compatibility, device/App UI, ecosystem, service or objection handling.

HIGH complexity normally points to Long-form. If Product Truth or Asset coverage cannot support it, the honest result is a Standard render plus explicit blockers—not an artificially long email.

## 8. Calibration outcome

All six Template Families need a SwitchBot Long-form option. The need is strongest for:

1. Product Launch
2. Theme Promotion
3. Product Education
4. Category / Multi-product
5. Brand / Ecosystem Story

Single Product Conversion also needs a long-form branch for HIGH-complexity smart hardware. Familiar or price-led products may remain Compact or Standard.

See:

- `brand_system/template_calibration_proposal_v1.0.yaml`
- `brand_system/switchbot_long_form_variants_v1.0.yaml`
- `brand_system/switchbot_composition_rules_v1.0.yaml`

