# SwitchBot Japan EDM Design Standard v1.0

版本：1.0  
冻结日期：2026-08-19  
状态：**Frozen — Phase 2 Closed**  
人工决策来源：`/Users/lai/Downloads/standard_human_decisions.csv`  
机器规则：`standards/edm_design_rules_v1.0.yaml`  
追溯台账：`standards/rule_traceability.csv`

## 0. 使用边界

本文件是后续 EDM Generator 的唯一正式设计基线。`v0.1` 保留为历史版本，不再作为新规则的执行入口。

证据权重固定为：

```text
Tier A（SwitchBot Approved）
> Tier B（SwitchBot Usable）
> Tier C（Japan External）
> Tier D（English External）
```

Tier D 只允许补充 Layout、Module Structure 与 Hero Creative，不得决定 SwitchBot 品牌特征、日文文案、信息密度、促销表达、CTA 或 Japan Localization。

Phase 2 关闭后的样本口径：Tier A 17、Tier B 4、Tier C 27、Tier D 40、Reject 5、Special Case 1。`SBL_001` 已由最新 Human Decision 从 Approved 改为 Reject。

## 1. Rule Classification 与 QA

| Rule Type | 执行方式 | QA 结果 |
|---|---|---|
| Hard Rule | Generator 必须遵守 | 违反时 `QA = BLOCKED` |
| Soft Rule | 默认遵守；可按 Campaign、Product、Promotion、Content Requirement 调整 | 不直接阻塞，但必须记录偏离原因 |
| Experimental Rule | 仅用于建议、测试和 Validation | 不得阻塞 EDM Production |

正式规则数量：Hard 18、Soft 16、Experimental 5。

# 2. Hard Rules — 必须遵守

| Rule ID | Rule | QA Failure Code |
|---|---|---|
| `R-BRAND-001` | 每封 EDM 必须明确且只服务一个 Primary Objective。 | `PRIMARY_OBJECTIVE_MISSING_OR_MULTIPLE` |
| `R-WEIGHT-001` | Tier D 不得覆盖 Tier A；Tier C 只补充 Japan Localization 与视觉参考，不得重写 SwitchBot 品牌基线。 | `EVIDENCE_TIER_OVERRIDE` |
| `R-PRODUCT-001` | 销售／发布 EDM 的 Hero 或首个正文模块必须出现可辨认的官方产品本体；关键视口不得破坏性裁切或遮挡产品。 | `PRODUCT_NOT_RECOGNIZABLE` |
| `R-ASSET-001` | 产品、App UI、包装、配件、安装关系与 Detail Close-up 必须来自可追溯的官方或已确认素材。 | `ASSET_PROVENANCE_MISSING` |
| `R-ASSET-002` | Test Copy、Placeholder、Dummy URL、缺图占位和未确认产品视觉不得进入 Final。 | `PLACEHOLDER_OR_TEST_CONTENT` |
| `R-AI-001` | AI 不得重绘、重构或补画产品本体、App UI、接口、传感器、按钮、配件或包装。 | `AI_PRODUCT_REDRAW` |
| `R-AI-002` | AI 只可辅助环境、人物、道具、光线和背景探索；必须保持产品轮廓、颜色、比例、安装关系与功能事实不变。 | `AI_PRODUCT_INTEGRITY_CHANGED` |
| `R-CLAIM-001` | 规格、价格、优惠、期间、库存、兼容性、Matter、No.1、Award、评价与媒体 Claim 必须有当前有效来源；缺失时标记 `Blocked / Unverified`。 | `UNVERIFIED_CLAIM` |
| `R-CLAIM-002` | 产品本体能力与配件／服务／App 能力必须分开表达，不得把外部能力写成产品本体能力。 | `CAPABILITY_BOUNDARY_VIOLATION` |
| `R-CTA-001` | 每个模块最多 1 个 Primary CTA；全邮件只允许 1–2 个明确目的地，多产品卡可按 SKU 重复同一目的地。 | `CTA_HIERARCHY_OR_DESTINATION_OVERLOAD` |
| `R-CTA-004` | CTA 文案必须说明动作或目的地，且链接必须真实可用；Marketplace 必须明确写明渠道。 | `CTA_DESTINATION_INVALID` |
| `R-MODULE-001` | Final EDM 必须具有 Hero、明确的 Primary Message、主要 CTA、必要产品／Proof 视觉以及 Footer；关键图片必须加载成功。 | `REQUIRED_EDM_STRUCTURE_MISSING` |
| `R-PROMO-002` | Urgency、截止时间、Deal、OFF、Coupon 与适用条件必须真实且可核对；不得制造虚假紧迫感。 | `PROMOTION_FACT_UNVERIFIED` |
| `R-COPY-002` | Final 文案不得包含测试文字、Placeholder、未经确认的事实或把 `Unknown` 改写成确定性表述。 | `COPY_FACT_OR_PLACEHOLDER_FAILURE` |
| `R-DESKTOP-001` | SwitchBot 正式 EDM 的 Desktop 内容宽度基线为 600px。 | `DESKTOP_BASELINE_WIDTH_VIOLATION` |
| `R-EVIDENCE-001` | 未渲染空白、加载失败、Gallery Frame 或只有 Metadata 的样本不得支持尺寸、布局、Hero Geometry 或视觉频率规则。 | `INSUFFICIENT_VISUAL_EVIDENCE` |
| `R-QA-001` | 任何必要事实、素材、URL、价格、期间或授权仍为 `Blocked / Unverified / Conflict` 时，Final Production 必须阻塞。 | `REQUIRED_INPUT_UNRESOLVED` |
| `R-QA-002` | Hard Rule 违反必须 `BLOCKED`；Soft Rule 偏离必须解释；Experimental Rule 不得用于阻塞 Production。 | `RULE_CLASSIFICATION_MISAPPLIED` |

# 3. Soft Rules — 默认遵守

| Rule ID | Default Rule | 允许调整的条件 |
|---|---|---|
| `R-HERO-001` | Hero 保留 1 个主活动／主命题；Promotion Hybrid 可增加 1 个次级促销层，但两者不能同等级竞争。 | Promotion Hybrid、Last Chance |
| `R-HERO-002` | 不再使用固定 Hero 高度比例。标题、产品与主 CTA 应在首屏形成完整任务，整体高度尽量接近常规 Desktop／Mobile 的一屏。 | Campaign 内容复杂度、产品画幅 |
| `R-DENSITY-001` | 模块数量只作诊断参考，不作阻塞阈值；优先检查 Primary Message、产品证据、主要 CTA 与必要 Proof 是否完整。 | Brand Story、Category、Promotion |
| `R-PROMO-001` | Hero 同时高强调的促销 Token 最多 2 个，优先只突出 Deal／OFF 中的 1 个；Last Chance 可强化紧迫感，但事实必须真实。 | Last Chance、短期大促 |
| `R-CTA-002` | 不设全邮件 CTA placement 硬上限；按模块管理，每模块 1 个 Primary CTA，多产品卡可按 SKU 重复。 | Multi-product、Marketplace 分流 |
| `R-COPY-001` | 日文 H1 默认 14–26 字，软上限 28 字；Editorial／Brand Story 可至 38 字，并按语义控制在 2–3 行。 | Editorial、Brand Story |
| `R-MESSAGE-002` | Primary USP 默认 1 个；Secondary USP 默认 2–3 个，超过时移入 Feature、Comparison 或后续模块。 | Education、Category |
| `R-MESSAGE-003` | Feature 默认 3–6 个，Proof 默认 1–3 个；需要更多内容时必须分章，不得在 Hero 同级堆叠。 | Education、Brand Story、Category |
| `R-HERO-004` | Product Launch／Single Product 优先 `product_center` 或 `lifestyle`；Promotion／Last Chance 优先 `promotion` 或 `multi_product`；Education 优先 `split` 或 `lifestyle`。 | Campaign Type、可用官方素材 |
| `R-COPY-003` | Subheadline 默认 18–40 字；正文每段 40–90 字；Feature Title 6–16 字；Feature Body 24–60 字；CTA 4–12 字。 | 产品复杂度、法务说明 |
| `R-COPY-004` | 英文只用于 Brand、Product Name、已确认技术名或必要导航；理解风险高时紧邻自然日文解释。 | 全球统一技术名、品牌资产 |
| `R-PROMO-003` | 视觉优先级默认 `Campaign Benefit / Deal Price > OFF% 或减额 > Coupon > MSRP > Period / Condition`；同一 SKU 的优惠信息默认最多重复 2 次，Last Chance 可到 3 次。 | Last Chance、多 SKU Promotion |
| `R-MODULE-003` | 每个模块只回答一个消费者问题；长内容必须用标题、留白、背景或重复语法分章。 | Brand Story、Product Education |
| `R-MODULE-004` | 推荐结构：Launch `Hero > USP > Feature/Detail > Lifestyle > Proof > Price > CTA > Footer`；Promotion `Hero > Product Grid > Price/CTA > Proof/Coupon > Closing CTA > Footer`；Education `Hero > Problem > USP > Feature > Detail/Proof > CTA > Footer`。 | Campaign Objective、内容需求 |
| `R-CTA-005` | CTA 使用动作 + 对象／目的地，例如 `詳しく見る`、`製品を見る`、`購入する`、`Amazonで見る`；避免只有 `こちら` 或含义相同的双按钮。 | 真实目的地与 Funnel Stage |
| `R-COPY-005` | 日本文案必须自然、具体、便于日本消费者理解；优先使用“具体场景 + 用户利益 + 已确认产品能力”，避免中文直译和无事实的夸张形容词。 | Brand Voice、Campaign Tone |

# 4. Experimental Rules — 不得阻塞 Production

| Rule ID | Experimental Guidance | Validation Requirement |
|---|---|---|
| `R-HERO-003` | Product Launch／Single Product 可测试产品视觉面积 40%–55%，Lifestyle 可测试 35%–50%；这些值只是视觉估算。 | Renderer 统一像素分割后再决定是否升级 |
| `R-MOBILE-001` | 使用 390px 作为默认 Mobile QA 视口，不把 390px 写成邮件内容宽度。 | 继续补充真实设备与邮件客户端测试 |
| `R-MOBILE-002` | Desktop 双栏默认按语义顺序在 Mobile 堆叠；3–4 列 Product Grid 默认测试为 1 列，可按实际内容优化。 | 至少 8 组独立渲染 Desktop/Mobile Pair |
| `R-MOBILE-003` | Mobile 正文目标不低于 16px、CTA 目标高不低于 44px、图片目标为内容宽 100% 且保持比例。 | 390px 与真实设备可读性测试；当前不能作为硬门槛 |
| `R-CTA-003` | CTA 尺寸根据实际排版、文案和可读性确定；Desktop 不冻结固定宽度，Mobile 参考 `R-MOBILE-003`。 | Renderer 在 600px／390px 双视口测量 |

# 5. Brand Principles

1. **Clean, Smart, Friendly, Modern。** 技术感不能变成冰冷的抽象装饰。
2. **Product Truth first。** 所有视觉与文案都必须能回到产品事实、官方素材和真实目的地。
3. **Japan consumer first。** 不把英文案例的极简、CTA、促销密度或文案习惯直接移植到日本市场。
4. **Value before price。** 除 Promotion／Last Chance 外，先说明用户价值，再说明价格与优惠。
5. **Decision path, not feature list。** 内容顺序服务于理解、信任和行动，不平均分配给每个 Feature。

# 6. Approved Anchor References

| Anchor | Role | Boundary |
|---|---|---|
| `SBG_006` | Theme Campaign / Promotion | 高促销密度只适用于明确主题活动 |
| `SBG_007` | Product Launch | 双产品／性能型发布，不作为所有单品模板 |
| `SBG_020` | Brand Story / Category Education | 长内容必须分章；不用于短促销 |
| `SBG_005` | Countdown / Last Chance（Conditional） | 促销感重；只用于真实截止场景 |
| `SBG_019` | Single-product Launch | 深色 Neon 视觉是产品特定，不是品牌通用风格 |
| `SBG_016` | Product-led Visual | 暖木 Lifestyle 只适用于相关家居品类 |
| `SBG_003` | User Voice + Promotion Hybrid（Conditional） | 可用于 UGC 分组与渠道 CTA；不得定义通用 Mobile 或 Education Geometry |
| `SBG_001` | Hero / Product Focus / Ecosystem | 多产品生态结构不得机械用于单品 EDM |

`SBL_001` 最终为 Reject：不属于 Tier A／B，不是 Anchor，不提供正向 Rule Evidence；仅作为“信息量不足、与当前 EDM 模板不适配”的 Anti-pattern。

# 7. Campaign Type Candidates

- Product Launch
- Single Product
- Promotion / Sale
- Multi-product / Category
- Product Education
- Seasonal Campaign
- Countdown / Last Chance
- Brand Story
- User Voice + Promotion Hybrid

这些是 Phase 3 的设计系统候选分类，不是已实现 Template。

# 8. Module Candidates

`hero`、`problem`、`primary_usp`、`feature`、`feature_icons`、`lifestyle`、`product_detail`、`comparison`、`product_grid`、`price`、`coupon`、`review`、`award`、`faq`、`cta`、`footer`。

Module Candidate 只有语义职责与使用边界；本阶段没有创建 Template Library、Module Library、Schema 或 Renderer。

# 9. Anti-patterns

1. Final 中出现 Test Copy、Placeholder、Dummy URL 或未加载图片。
2. Hero 缺少明确 Primary Objective、产品证据或主要 CTA。
3. AI 重绘产品、App UI、接口、配件或安装关系。
4. Lifestyle 画面成为唯一产品证据。
5. 多个同级 Primary Message、促销数字或含义相同的 CTA 互相竞争。
6. Copy 很长但没有标题、短段、视觉或 CTA 分章。
7. 信息量过低，不能回答“是什么、为什么值得、下一步做什么”。
8. 把 Gallery Frame、加载失败或 Metadata 当作视觉规则依据。
9. Tier D 反向覆盖 Tier A 的 SwitchBot 品牌或日本表达。
10. 把 `SBG_005`、`SBG_003` 或 `SBG_017` 的场景特定风格变成通用标准。

# 10. Freeze Record

- 13 / 13 Human Decisions 已回写。
- `SBL_001 = Remove → Reject / No Tier / Not Anchor / Anti-pattern only`。
- `R-SPACING-001 = Remove`，不进入正式 Generator Rules。
- v1.0 不冻结 Padding 或 Module Spacing 的像素范围；等正式 Renderer 以 600px／390px 双视口测量后再提案 spacing tokens。
- `v0.1` 保留：`standards/edm_design_standard_v0.1.md`、`standards/edm_design_rules.yaml`。
- Phase 2 到此关闭；不得自动进入 Phase 3。
