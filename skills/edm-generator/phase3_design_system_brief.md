# EDM Visual Generator — Phase 3 Design System Input Brief

生成日期：2026-08-19  
输入基线：`standards/edm_design_standard_v1.0.md`  
状态：Phase 2 Closed / Phase 3 Not Started

本文件只负责把 Phase 3 必须继承的设计约束集中到一个入口。它不是 Template Library、Module Library、Schema、Renderer 或 Skill。

## 1. Brand Principles

- Clean、Smart、Friendly、Modern。
- Technology without coldness：技术能力必须连接到日本消费者可理解的场景和利益。
- Product Truth first：产品事实、官方素材和真实目的地优先于视觉概念。
- Japan consumer first：不把英文 EDM 的文案、促销密度和 CTA 习惯直接移植到日本市场。
- Value before price：除 Promotion／Last Chance 外，先说明价值，再进入价格与优惠。
- Decision path, not feature list：内容服务于理解、信任与行动，不平均分配给每个 Feature。

## 2. Hard Rules

Phase 3 必须直接继承以下 18 条 Hard Rule；任何违反都令 `QA = BLOCKED`：

`R-BRAND-001`、`R-WEIGHT-001`、`R-PRODUCT-001`、`R-ASSET-001`、`R-ASSET-002`、`R-AI-001`、`R-AI-002`、`R-CLAIM-001`、`R-CLAIM-002`、`R-CTA-001`、`R-CTA-004`、`R-MODULE-001`、`R-PROMO-002`、`R-COPY-002`、`R-DESKTOP-001`、`R-EVIDENCE-001`、`R-QA-001`、`R-QA-002`。

实现时必须从 `edm_design_rules_v1.0.yaml > rules` 读取 requirement、failure_code 与 QA 行为，不得在 Template 或 Renderer 中复制另一套相互冲突的规则。

## 3. Soft Rules

默认继承以下 16 条 Soft Rule；偏离时记录 Campaign、Product、Promotion 或 Content Requirement 原因：

`R-HERO-001`、`R-HERO-002`、`R-DENSITY-001`、`R-PROMO-001`、`R-CTA-002`、`R-COPY-001`、`R-MESSAGE-002`、`R-MESSAGE-003`、`R-HERO-004`、`R-COPY-003`、`R-COPY-004`、`R-PROMO-003`、`R-MODULE-003`、`R-MODULE-004`、`R-CTA-005`、`R-COPY-005`。

关键 Human Decision：

- Hero 不冻结 30%–42% 高度；尽量让标题、产品和主 CTA 在常规 Desktop／Mobile 一屏形成完整任务。
- 模块数量只作诊断参考，不作为阻塞阈值。
- CTA 不设全邮件硬上限；按模块与 SKU 管理。
- 日文 H1 默认 14–26 字、软上限 28；Editorial／Brand Story 可到 38 字。

## 4. Experimental Rules

以下 5 条只能用于建议、测试和后续 Validation，不得阻塞 Production：

- `R-HERO-003`：产品视觉面积测试区间。
- `R-MOBILE-001`：390px Mobile QA 视口。
- `R-MOBILE-002`：语义堆叠与单列 Product Grid。
- `R-MOBILE-003`：Mobile 字体、CTA 高度和图片宽度目标。
- `R-CTA-003`：CTA 尺寸按实际排版确定，不冻结 Desktop 宽度。

`R-SPACING-001` 已 Remove。Phase 3 不得提前冻结 Padding 或 Module Spacing 数值；应在 Renderer 的 600px／390px 双视口测量后另行提案。

## 5. Approved Anchor References

| Anchor | Phase 3 用途 | 禁止泛化 |
|---|---|---|
| `SBG_006` | Theme Campaign / Promotion | 不作为 Evergreen 密度基线 |
| `SBG_007` | Product Launch | 双产品／性能风格不适用于所有单品 |
| `SBG_020` | Brand Story / Category Education | 不用于短促销 |
| `SBG_019` | Single-product Launch | Neon 风格不是品牌通用视觉 |
| `SBG_016` | Product-led Visual | 暖木风只适用于相关家居品类 |
| `SBG_001` | Hero / Product Focus / Ecosystem | 多产品结构不用于真正单品 |
| `SBG_005` | Countdown / Last Chance（Conditional） | 只用于真实截止；促销感不可扩散 |
| `SBG_003` | User Voice + Promotion Hybrid（Conditional） | 不定义通用 Mobile 或 Product Education Geometry |

`SBL_001` 已最终 Reject，不是 Anchor，不提供正向 Rule Evidence。

## 6. Campaign Type Candidates

- Product Launch
- Single Product
- Promotion / Sale
- Multi-product / Category
- Product Education
- Seasonal Campaign
- Countdown / Last Chance
- Brand Story
- User Voice + Promotion Hybrid

Phase 3 可以据此提议 Template Families，但在正式授权前不得创建 Template。

## 7. Module Candidates

`hero`、`problem`、`primary_usp`、`feature`、`feature_icons`、`lifestyle`、`product_detail`、`comparison`、`product_grid`、`price`、`coupon`、`review`、`award`、`faq`、`cta`、`footer`。

Phase 3 建模时，每个 Module 至少需要：purpose、allowed_campaigns、required_inputs、content_limit、asset_requirement、CTA behavior、mobile behavior、QA checks。当前只记录 Candidate，不定义实现。

## 8. Anti-patterns

- Test Copy、Placeholder、Dummy URL、缺图或未确认产品视觉进入 Final。
- Hero 缺少 Primary Objective、产品证据或主要 CTA。
- AI 重绘产品、UI、接口、配件或安装关系。
- Lifestyle 成为唯一产品证据。
- 多个同级 Message、促销数字或 CTA 竞争。
- 长正文没有标题、短段、视觉或 CTA 分章。
- 信息量太少，无法回答“是什么、为什么值得、下一步做什么”。
- Gallery Frame、加载失败或 Metadata 被误当作视觉证据。
- Tier D 覆盖 Tier A 的 SwitchBot 或日本市场特征。
- 把 `SBG_005`、`SBG_003`、`SBG_017` 的场景特定表现变成通用规则。
- `SBL_001`：与当前 EDM 模板不适配、信息量不足，只作为 Failure Pattern。

## 9. Japan Localization Rules

- H1 默认 14–26 日文字符，软上限 28；Editorial／Brand Story 可到 38。
- 按语义换行，避免拆开产品名、金额、OFF%、日期和 CTA 动词。
- CTA 使用自然日语动作 + 对象／目的地；Marketplace 明确写 `Amazonで見る`、`楽天市場で見る` 等。
- 英文仅限 Brand、Product Name、技术名与必要导航；有理解风险时紧邻日文解释。
- 优先“具体场景 + 用户利益 + 已确认产品能力”，避免中文直译、AI 空话和无事实夸张。
- Tier D 不得决定日文文案、信息密度、促销表达或 CTA。

## 10. Asset Rules

- 产品本体、App UI、包装、配件、安装关系与细节必须可追溯。
- 只有官方透明 PNG、官方实拍、已确认包装／配件图和已确认 UI 可以进入 Final。
- Claim、价格、优惠、期间、兼容性与授权必须绑定当前有效来源。
- Test、Placeholder、过期资料或来源不明素材令 `QA = BLOCKED`。

## 11. AI Generation Boundaries

AI 可以：

- 探索环境、人物、背景、道具、构图、光线与气氛。
- 在不改变产品事实的前提下提出组合与背景方向。

AI 不可以：

- 重绘或补画产品本体、按钮、接口、传感器、配件、包装或 App UI。
- 改变产品轮廓、颜色、比例、安装方式和结构关系。
- 生成未确认功能、规格、Claim、价格、日期或 UI 状态。
- 让概念图冒充 Final Production Asset。

## 12. Phase 3 Start Gate

Phase 3 开始前必须显式获得授权，并确认：

1. v1.0 Markdown、YAML 与 Traceability 仍为同步版本。
2. Template／Module 的每一条约束引用 v1.0 `rule_id`。
3. Experimental Rules 不进入 Blocking QA。
4. Renderer 同时输出 600px Desktop 与 390px Mobile QA 结果。
5. 本文件不构成 Phase 3 已开始；当前仍处于停止状态。
