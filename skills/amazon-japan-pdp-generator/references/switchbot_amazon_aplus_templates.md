# SwitchBot Japan Amazon A+ Template Baseline

Accessed: 2026-08-17. This reference controls visual structure and brand logic only. It is never a Claim source for a different SKU.

## Current evidence baseline

- [Amazon Japan — SwitchBot Plug Mini](https://www.amazon.co.jp/SwitchBot-%E3%82%B9%E3%83%9E%E3%83%BC%E3%83%88%E3%82%B3%E3%83%B3%E3%82%BB%E3%83%B3%E3%83%88-Bluetooth-Wi-Fi%E4%B8%A1%E6%96%B9%E5%AF%BE%E5%BF%9C-SmartThings%E5%AF%BE%E5%BF%9C/dp/B09PYLWNGV): live page checked on 2026-08-17. Its A+ markup exposes 50/50 image-and-text, 1464 px full-background, four-column and Brand Story carousel structures.
- [Amazon Japan — SwitchBot Thermometer Plus](https://www.amazon.co.jp/SwitchBot-%E6%B8%A9%E6%B9%BF%E5%BA%A6%E8%A8%88%E3%83%97%E3%83%A9%E3%82%B9-Alexa-%E6%B8%A9%E5%BA%A6%E8%A8%88-%E6%B9%BF%E5%BA%A6%E8%A8%88/dp/B09PYKJ6CS): live page checked on 2026-08-17. It uses a 1464×600 full-background hero, 650×350 two-column feature images and a Premium comparison table.
- [SwitchBot Japan — K11+](https://www.switchbot.jp/products/switchbot-robot-vacuum-cleaner-k11): current official page includes Amazon A+ assets named at 1464×600 and shows the Japan brand rhythm: short benefit-first headlines, warm interiors, authentic product photography, pale proof cards and restrained cyan accents.
- [Amazon official JP A+ guidance](https://sellercentral.amazon.co.jp/seller-forums/discussions/t/2677b990-b0f9-4ee2-90ff-12073e340e58): keep content concise, combine clear text with high-resolution images and select from current Builder modules. Price/promotion, delivery, purchase CTAs, exaggerated claims and low-quality/unreadable images are prohibited.

Amazon may change Module names and Seller Central availability. Treat Module availability as `Need Verification` until confirmed in the live JP Seller Central account for the target ASIN.

## Brand visual grammar

- Use authentic official product photography or render as the product source of truth.
- Prefer warm, believable Japanese interiors with restrained cyan/blue-green accents, dark gray copy and ample light space.
- Lead with a short Japanese benefit headline; supporting copy should be compact and readable on mobile.
- Use proof cards, icons and diagrams only when their content is source-backed.
- Keep the product silhouette, proportions, color, material, Logo, buttons, ports, screen, accessories and installation structure unchanged.
- AI may generate or extend scene, people, background, lighting, props and empty composition space. It must never generate, redraw, inpaint or redesign the product body.

## Formal A+ template library

| ID | Template | Decision job | Typical visual logic | Use when |
|---|---|---|---|---|
| A-HERO | Hero | 理解产品 + 产生兴趣 | 1464×600 full-width lifestyle or product hero; short headline; one core value | Open A+ and define category/value |
| A-50-50-FEATURE | 50/50 Feature | 理解核心优势 | 50% concise copy + 50% official product/feature visual | Explain the main mechanism → benefit |
| A-THREE-FEATURE-GRID | Three Feature Grid | 理解核心优势 | Three consistent cards with equal image and copy scale | Scan supporting benefits without overload |
| A-LIFESTYLE | Lifestyle Full Image | 看到真实场景 | Believable Japanese scene + safe-area headline | Turn value into a real use moment |
| A-TECHNICAL | Technical Diagram | 相信产品 | Official render + sourced proof cards / simple diagram | Explain measurable or technical trust |
| A-INSTALLATION | Installation | 判断适配 | Two or three verified setup steps | Explain installation without inferred accessories |
| A-ECOSYSTEM | Ecosystem | 相信产品 + 判断适配 | Verified product/app/ecosystem relationship | Value depends on compatible connections |
| A-COMPARISON | Comparison / Fit | 判断适配 | Fit checklist or source-backed family comparison | Help buyers select and avoid wrong purchase |
| A-FAQ | FAQ / Confidence | 消除顾虑 | FAQ, box contents, separate-purchase note, support route | Remove final objections |
| A-BRAND | Brand | 品牌信任 | One approved brand message with official logo layer | Brand story is approved and relevant |

## Matching rules

1. Assign every A+ Module one formal `template_id` and one decision-stage job. `SB-A01`—`SB-A08` are deprecated intake aliases only.
2. Use `A-HERO` once at the opening. Use Feature/Technical/Installation/Ecosystem only where they add information beyond the seven secondary images.
3. Use `A-COMPARISON` only with source-backed current values. Unknown cells remain internal and must not appear as status text in Consumer Preview.
4. Use `A-FAQ` near the end. Clarify included items, separate purchases, requirements, setup and support without unsupported promises.
5. Do not force all templates into every PDP. Select the smallest 5–8-module set that carries the whole decision journey. There is no 15-image target.
6. A content unit is not automatically a feature and not automatically a JPEG. Combine problem, transformation, scene, proof, installation, compatibility, comparison and objection units inside the appropriate Module.
7. Product images and A+ must not repeat the same headline, scene and proof. Secondary images accelerate the decision; A+ deepens explanation.

## Visual production source gate

Every final JPEG must record:

- official product source path;
- `sourceOrigin`;
- `sourceAssetType`;
- source and output SHA-256;
- `productBodyAiGenerated`;
- allowed `aiGeneratedElements`;
- composition operations;
- `visualProductionStatus`.

Only `sourceOrigin = User Provided Official`, an approved official asset type, and `productBodyAiGenerated = false` may qualify for `Final Ready`. Official-site research downloads can be test fixtures, but they are not a substitute for assets supplied by the user for formal launch.
