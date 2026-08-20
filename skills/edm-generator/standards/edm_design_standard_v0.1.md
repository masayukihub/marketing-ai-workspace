# SwitchBot Japan EDM Design Standard v0.1

版本：0.1  
生成日期：2026-08-18  
阶段：Phase 2 — Pattern Mining  
状态：可供后续 Generator 执行；尚未进入 Template／Module／Renderer 实现

## 0. Evidence Model

本标准严格使用以下权重：

1. **Tier A（18）**：SwitchBot 品牌、信息层级、产品突出方式、CTA 与视觉基线。
2. **Tier B（4）**：补充可接受结构变体，不覆盖 Tier A。
3. **Tier C（27）**：日本文案、促销表达、价格、CTA、视觉密度与本地化补充，不定义 SwitchBot 品牌。
4. **Tier D（40）**：只补充 Layout、Module、Hero 创意；不得决定日本文案、密度、促销表达、CTA 或品牌特征。
5. **Reject（4）**：只产生 DO NOT 规则。
6. **Special Case（1）**：个案探索，不进入通用频率基线。

数据集中 29 个样本经本轮直接截图复核，65 个为 Phase 1 标签辅助推断。`EXT_005` 因正文未渲染而阻断；`SBG_003` 的截图存在大面积未渲染空白。所有 `≈` 比例是视觉估计，不是像素分割测量。

### Confidence 定义

- **High Confidence**：Tier A／B 一致，或 Human Review 与 Reject 直接支持；可作为默认硬规则。
- **Medium Confidence**：Tier A 有支持，且 Tier C／直接截图补充；作为默认值，可按 Campaign 调整。
- **Experimental**：样本少、依赖二手截图或缺少 Mobile 对照；必须人工确认。

# 1. Brand Principles

1. **一封邮件只服务一个 Primary Objective。** Hero 只允许 1 个同等级 Primary Message；其余信息降级到 USP、Proof 或后续 Module。`High Confidence`
2. **产品必须可辨认。** 产品发布／销售邮件的 Hero 或首个正文 Module 必须展示可识别的官方产品本体；Lifestyle 不能替代产品事实。`High Confidence`
3. **Technology without coldness。** 技术能力必须连接到日本消费者可理解的生活场景、问题或具体利益；禁止只有参数和抽象科技背景。`High Confidence`
4. **先价值，后价格。** 除 Promotion／Last Chance 外，Primary USP 与使用价值优先于 Deal Price；优惠是购买推动，不是产品身份。`High Confidence`
5. **长内容必须分章。** 每个 Module 只回答一个问题，使用标题、留白、背景或卡片边界建立扫描路径。`High Confidence`
6. **CTA 必须说明目的地。** “製品を見る／詳しく見る／購入する／Amazonで見る”按真实去向选择；禁止多个含义相同的主按钮。`Medium Confidence`
7. **所有视觉与 Claim 可追溯。** 产品、UI、价格、期间、兼容性、No.1、媒体评价与优惠必须绑定已确认来源；缺失则标记 `Blocked / Unverified`。`High Confidence`

# 2. Message Hierarchy Standard

Tier A 的 18 个样本全部包含 Hero、CTA 与 Footer；Tier A 中 Lifestyle 11/18、Primary USP 10/18、Feature 10/18、Price 10/18、Product Grid 9/18。此频率用于确认“价值—证明—行动”的骨架，不代表所有邮件必须包含全部 Module。

| Level | Recommended | Maximum | Generator Rule | Confidence |
|---|---:|---:|---|---|
| Primary Message | 1 | 1 | 每封邮件／Hero 只有一个主命题 | High |
| Primary USP | 1 | 1 | 与 Primary Message 直接对应 | High |
| Secondary USP | 2–3 | 3 | 超过 3 个时移入 Feature／Comparison | High |
| Feature | 3–6 | 6 | Brand Story／Category 可实验性扩展至 8，必须分章 | Medium |
| Proof | 1–3 | 4 | Claim-sensitive 信息至少 1 个可核对 Proof | High |
| Primary CTA destination | 1 | 2 | 两个目的地必须明确不同 | High |
| CTA placements | 2–6 | 8 | 8 仅限多产品促销／Last Chance | Medium |

推荐顺序：

```text
Primary Message
→ Primary USP
→ Secondary USP / Feature
→ Proof
→ Price / Promotion（如适用）
→ CTA
```

禁止把 Feature、Proof、价格与 Coupon 同时提升为 Primary Message。

# 3. Hero Standard

## 3.1 通用规则

- Desktop Hero 建议占邮件首屏视觉高度约 `30%–42%`；精确值需在 Phase 3 以 600px Renderer 实测。`Medium Confidence`
- 日文 H1 默认 `12–24` 字、最多 `28` 字、最多 2 行。Brand Story 可到 32 字／3 行，但 CTA 可后移。Tier C 已记录标题中，已知样本范围为 13–37 字；长标题只出现在特定内容／活动场景。`Medium Confidence`
- Product Launch／Single Product 的产品本体建议占 Hero 视觉面积 `40%–55%`；Lifestyle Hero 中仍需 `35%–50%` 的可辨认产品／安装效果。`Medium Confidence`
- Hero 只使用 1 个主要促销 Token；完整 MSRP、Deal Price、Coupon、Period 移入 Price／Coupon Module。`High Confidence`
- Product Launch、Promotion、Single Product 推荐 Hero 内有 CTA；Product Education／Brand Story 可把 CTA 放在第一个解释段之后。`Medium Confidence`
- 背景必须服务产品识别：浅色产品适合低噪声中性／Lifestyle 背景；深色产品需轮廓分离；禁止让 AI Background 改变产品形态。`High Confidence`

## 3.2 Campaign-specific Hero

| Campaign | 推荐 Hero Type | 首屏结构 | CTA | Sale 表达 | Confidence |
|---|---|---|---|---|---|
| Product Launch | `product_center` / `lifestyle` | H1 + Primary USP + 大产品 + CTA | 推荐 | 最多 1 个优惠 Token | High |
| Promotion | `promotion` / `multi_product` | Campaign Benefit + 产品群 + 主要优惠 + CTA | 必须 | 可突出 Deal 或 OFF，其余下移 | High |
| Single Product | `product_center` / `lifestyle` | 产品／安装效果 + 1 个利益 + CTA | 推荐 | 次级 | High |
| Category | `lifestyle` / `multi_product` | 场景／品类命题 + 产品群 + 分类入口 | 推荐 | 进入 Product Grid | Medium |
| Product Education | `split` / `lifestyle` | 问题 + 主要理解点 + 产品证据 | 可后移 | 非首要 | Medium |
| Brand Story | `lifestyle` / `typography` | Context + Brand/Category Thesis | 可后移 | 通常不放 Hero | Medium |
| Last Chance | `promotion` | 截止时间 + 活动利益 + 产品／CTA | 必须 | 允许 Urgency，但必须真实 | High |

# 4. Module Standard

| Module | purpose | when_to_use | when_not_to_use | content_limit | visual_rule |
|---|---|---|---|---|---|
| `hero` | 定义唯一主任务 | 所有 EDM | 无 | 1 Message、1 USP、1 CTA 组 | 产品／场景为最大视觉；不得缺失 |
| `problem` | 建立用户问题 | Education、New Feature、安防／清洁主题 | 纯价格通知 | 1 问题、最多 2 个场景 | 场景图优于抽象图标 |
| `primary_usp` | 回答“为什么值得关注” | Launch、Education、Brand Story | 与 Hero 完全重复时 | 1 USP、正文 40–90 字 | 1 大图或 1 明确产品图 |
| `feature` | 解释能力 | 需要 3–6 个具体能力 | 只有 1 个卖点时 | 每项 1 标题 + 24–60 字 | 图像必须与功能一一对应 |
| `feature_icons` | 快速扫描短证据 | 3–6 个并列短项 | 复杂安装／Claim 说明 | 3–6 项、每项标题 6–14 字 | 图标不可代替真实产品／UI |
| `lifestyle` | 展示使用结果 | 家居、灯光、季节、场景型产品 | 没有官方产品合成／实拍时 | 1 场景 + 1 利益 | 产品或效果必须可辨认 |
| `product_detail` | 证明结构与细节 | Launch、Education、安装说明 | 只需情绪表达时 | 每段 1 细节、最多 3 段 | 官方 PNG／实拍／局部特写 |
| `comparison` | 帮助选择 | 多型号、升级、Category | 无真实选择问题时 | 2–4 列、3–6 个关键维度 | 相同角度、相同尺度，不虚构差异 |
| `product_grid` | 多产品浏览 | Promotion、Category、Ecosystem | 单品发布 | Desktop 2–3 列；每卡 1 价格 + 1 CTA | 产品卡图、名称、价格、CTA 固定顺序 |
| `price` | 解释购买成本 | 有价格或优惠时 | Price 未确认时 | 1 MSRP + 1 Deal + 1 主要优惠 | Deal 最大，MSRP 最小且可删除 |
| `coupon` | 解释额外优惠 | 有真实 Code／领取步骤 | 无券或自动折扣 | 1 券、1 Code、1 条件、1 期间 | 独立卡片，不与 Hero 五种数字竞争 |
| `review` | 提供社会证明 | 有可核对评价／媒体证据 | 来源缺失 | 1–3 条短摘录 | 标注来源；不得伪造评分 |
| `award` | 提供权威证明 | 有当前可使用 Award | 过期／许可不明 | 1–3 个 | 使用官方标志并保留使用权限 |
| `faq` | 解除关键障碍 | 安装、兼容、退换、订阅 | Hero | 3–5 项 | 标题可扫描；正文短段或折叠（Renderer 阶段） |
| `cta` | 明确下一步 | 每个主决策段之后 | 无真实 URL | 每段 1 主 CTA；全邮件 1–2 目的地 | 对比明显、文案说明目的地 |
| `footer` | 法务、退订、品牌信息 | 所有 EDM | 无 | 只放必要信息 | 不与 Campaign CTA 竞争 |

## 4.1 Tier A 常见结构候选

- Launch：`Hero > Primary USP > Feature/Product Detail > Lifestyle > Proof > Price > CTA > Footer`
- Promotion：`Hero > Product Grid > Price/CTA > Proof/Coupon > Closing CTA > Footer`
- Education：`Hero > Problem > Primary USP > Feature > Product Detail/Proof > CTA > Footer`
- Brand Story：`Hero > Context/Lifestyle > Comparison > Product Options > Proof > CTA > Footer`

这些是 Template Candidate，不是已实现 Template。

# 5. Information Density Standard

Human Review 的主要失败并非简单“字多／字少”，而是决策信息是否完整、是否有层级。

| Level | 可执行判定 | Generator 行为 | Confidence |
|---|---|---|---|
| Low | 下列至少 2 项缺失：可辨认产品、Primary USP、Proof、主要 CTA；或正文 Module < 4 | 阻止输出或补齐价值／证据，不以装饰图片填充 | High |
| Recommended | 1 Message、1 USP、2–3 Secondary USP、3–6 Feature、1–3 Proof、2–6 CTA placements、约 6–10 个正文 Module | 默认生成范围 | Medium |
| High | 9–13 个 Module、Feature > 6 或 CTA placements 5–8，但有清楚分章、重复语法和单一 Primary Objective | 仅用于 Category、Brand Story、Promotion；启用 Section Header | Medium |
| Overload | 以下任 2 项：Primary Message ≥ 2；Hero 同级卖点 > 3；同级促销数字 ≥ 4；目的地 > 3；连续正文 > 120 日文字符且无小标题；产品 Grid 循环 > 2 | 阻止输出并合并／下移信息 | Medium |

特殊判定：`SBG_021` 属于“Copy Overload + Visual Hierarchy Too Low”；文字很多不代表信息完整。`SBL_001` 的 Approved 与四项 1 分发生冲突，在人工决策前不得用于下调 Recommended 下限。

# 6. Japanese Copy Standard

Tier C 27 个样本中，English Usage 为 light 11、moderate 11、heavy 5。SwitchBot 默认只允许 Brand／Product Name／技术名使用英文，不以 Tier C 的 heavy 样本作为默认。

| Element | 推荐字数 | 最大值 | 写法 | Confidence |
|---|---:|---:|---|---|
| H1 | 12–24 | 28（Brand Story 32） | 具体场景／利益 + 产品或活动；1–2 行 | Medium |
| Subheadline | 18–40 | 46 | 补充对象、条件或 Primary USP，不重复 H1 | Medium |
| Body paragraph | 40–90 | 120 | 每段一个问题；超过 90 字优先拆段 | Medium |
| Feature title | 6–16 | 20 | 名词／结果导向，避免抽象形容词 | Medium |
| Feature body | 24–60 | 80 | 场景 + 能力 + 结果 | Medium |
| CTA | 4–12 | 16 | 动词 + 对象／目的地 | High |
| Promotion Copy | 8–24 | 32 | 优惠 + 条件／期间，禁止无事实的煽动 | Medium |

推荐 CTA：`詳しく見る`、`製品を見る`、`ラインナップを見る`、`購入する`、`今すぐチェック`、`Amazonで見る`。  
避免：只有 `こちら`、`CLICK HERE`、同一段两个含义相同的按钮。

标点与换行：

- H1 最多使用一个强调符号组；不连续堆叠 `！`、Emoji、括号与斜线。`Medium Confidence`
- 换行按语义块，不拆产品名、金额、OFF%、日期或 CTA 动词。`High Confidence`
- 英文技术名首次出现时，如有理解风险，紧邻日文说明。`Medium Confidence`

# 7. Promotion Standard

## 7.1 Visual Priority

```text
Campaign Benefit / Deal Price
→ OFF% 或 Discount Amount（二选一为主要强调）
→ Coupon（独立卡）
→ MSRP（最弱）
→ Period / Condition（可读但不抢主视觉）
```

| Element | Rule | Confidence |
|---|---|---|
| Deal Price | 商品卡中的最大价格信息；必须已确认 | High |
| MSRP | 可选；存在时小于 Deal Price，并明确对比关系 | High |
| OFF% | Hero 最多 1 个主要百分比；多 SKU 在各自卡片内表达 | High |
| Discount Amount | 与 OFF% 选择一个作为主强调；另一个降级 | Medium |
| Coupon | 独立 Module，包含 Code／领取方式／条件／期间 | High |
| Period | 必须可读；Last Chance 允许提升到 Hero | High |
| Urgency | 仅在真实截止、库存或时间条件成立时使用 | High |

## 7.2 避免“促销感过重”

- Hero 同时高强调的促销 Token 最多 2 个。`High Confidence`
- 常规 Launch／Education 的优惠色不得覆盖产品主色与产品轮廓。`High Confidence`
- 同一 SKU 的 Price／OFF／Coupon 在全邮件中最多重复 2 次；Last Chance 可到 3 次。`Medium Confidence`
- 多产品促销以统一 Product Card 重复，不以不同颜色／徽章为每件商品重新建立视觉语法。`Medium Confidence`

# 8. Product Visual Standard

1. **AI 不得重绘产品本体。** `High Confidence`
2. 产品本体只允许使用：官方透明 PNG、官方实拍、已确认的包装／配件图、已确认的 App UI。来源缺失时状态为 `Blocked`。`High Confidence`
3. AI Background 只可用于环境探索；必须保持产品轮廓、颜色、比例、按钮、传感器、接口、配件与安装关系不变。`High Confidence`
4. Product PNG：用于 Hero、Product Grid、Comparison、Price Card；应保持边缘清晰与真实比例。`High Confidence`
5. Lifestyle：用于 Problem、Benefit、Seasonal、使用完成态；必须能辨认产品或产品效果。`High Confidence`
6. Detail Close-up：用于结构、材质、安装、传感器、接口等可验证细节；不使用 AI 生成细节。`High Confidence`
7. App UI：用于 New Feature、Automation、Ecosystem；必须是目标市场与当前版本可用的真实 UI。`High Confidence`
8. Accessory：必须与产品本体区分，不能把配件能力写成产品本体能力。`High Confidence`

# 9. CTA Standard

- 每个 Module 最多 1 个 Primary CTA；Hero 最多 2 个按钮，且目的地必须不同。`High Confidence`
- 全邮件默认 1–2 个 CTA destinations；同一目的地可在 Hero、中段、结尾重复。`High Confidence`
- Launch／Single Product 推荐 2–4 次 CTA placements；Education 2–3 次；多产品 Promotion 4–8 次。`Medium Confidence`
- 文案使用动作 + 对象／目的地；Marketplace 必须写 `Amazonで見る`、`楽天市場で見る` 等。`High Confidence`
- Desktop Button 建议宽 `200–320px`、高至少 `44px`；Mobile 高至少 `44px`、可用内容宽度的 100%，但最大宽度与正文一致。`High Confidence`
- Button 文字建议 Desktop/Mobile 均不低于 `16px`；相邻按钮间距至少 `12px`。`High Confidence`
- 禁止仅通过颜色区分 Primary／Secondary；还需 Fill／Border／Label 差异。`Medium Confidence`

# 10. Desktop / Mobile Standard

基准：Desktop `600px`，Mobile Preview `390px`。

| Element | Desktop | Mobile | Confidence |
|---|---|---|---|
| Content width | 600px | 390px viewport，内容自适应 | High |
| Two-column | 50/50 或 40/60 | 默认顺序堆叠；语义优先于左右位置 | High |
| Product Grid | 2–3 列 | 默认 1 列；信息短且可读时实验性 2 列 | Medium |
| H1 | 28–36px | 24–30px | Medium |
| Body | 16–18px | ≥16px | High |
| CTA | ≥44px high | ≥44px high；建议全宽 | High |
| Hero | 产品／文字平衡 | 优先保产品和标题，不做破坏性裁切 | High |
| Image | 1×/2× 清晰资源 | 宽度 100%，保持比例；必要时提供移动端裁切 | High |

移动端规则：

1. 双栏按照“文本解释 → 对应产品／图像”或“产品 → CTA”的语义顺序堆叠，不按纯视觉左右顺序。`High Confidence`
2. 3–4 列 Grid 默认改为 1 列；只有产品名、价格和 CTA 在 390px 下仍完整时才用 2 列。`Medium Confidence`
3. 不缩小正文到 16px 以下来保留 Desktop 排版。`High Confidence`
4. Hero 标题、产品、CTA 必须在移动首屏或紧邻首屏内出现；装饰背景可裁切，产品本体不可裁断。`High Confidence`
5. 当前 Mobile 对照样本只存在于部分外部英文样本，且未完成逐对照审查；Grid breakpoint、图片裁切与字体缩放仍为 `Experimental`，Phase 3 前需 390px 人工验证。

# 11. Anti-pattern Rules — DO NOT

1. **DO NOT** 输出缺少 Hero、Primary Message、Primary CTA 或关键图片未加载的正式 EDM。`High Confidence`
2. **DO NOT** 在 Hero 中同时存在 2 个以上同级 Primary Message。`High Confidence`
3. **DO NOT** 在 Hero 中放置安装步骤、FAQ、版本兼容长文或连续程序性段落。`High Confidence`
4. **DO NOT** 使用 placeholder、AI 重绘、无法确认来源的产品本体或 UI。`High Confidence`
5. **DO NOT** 让 Lifestyle 氛围图成为唯一产品证据。`High Confidence`
6. **DO NOT** 让 4 个以上促销数字／徽章处于同一最高视觉层级。`Medium Confidence`
7. **DO NOT** 使用两个含义相同的 Primary CTA，或让 CTA 目的地不可辨认。`High Confidence`
8. **DO NOT** 把未渲染空白、加载失败或 Gallery 外壳当作有效 EDM 结构。`High Confidence`
9. **DO NOT** 将 Tier D 的英文 CTA、信息密度、促销表达或极简风反向覆盖 Tier A 的 SwitchBot 特征。`High Confidence`
10. **DO NOT** 将 `SBG_005` 的强促销密度扩展到 Evergreen／Education，或将 `SBG_017` 的 Premium Art Direction 纳入通用频率。`High Confidence`

## 12. Phase 3 Candidates（仅提案，未实现）

### Template Candidates

1. `T1_single_product_launch` — Anchor：`SBG_019`、`SBG_016`
2. `T2_theme_promotion` — Anchor：`SBG_006`；Last Chance 变体参考 `SBG_005`
3. `T3_product_education` — Anchor：`SBG_003`（语义）+ `SBG_016`（结构）；需先重截 `SBG_003`
4. `T4_category_brand_story` — Anchor：`SBG_020`
5. `T5_ecosystem_multi_product` — Anchor：`SBG_001`

### Module Candidates

`hero_product_focus`、`hero_lifestyle`、`hero_promotion`、`problem_scenario`、`primary_usp_story`、`feature_split`、`feature_icons`、`product_detail`、`comparison_table`、`product_grid`、`price_card`、`coupon_card`、`proof_review`、`cta_band`、`legal_footer`。

这些 Candidate 只有结构定义，没有正式 HTML、资产、Schema 或 Renderer。

## 13. Open Decisions / Weak Evidence

1. `SBL_001`：Approved 与四项 1 分／“信息量太少”冲突；需人工决定改为 Reject、Special Case 或保留 Tier A 但降权。
2. `SBG_003`：需重截完整 EDM 后再确认模块数量、Hero 与留白。
3. Mobile：缺少 SwitchBot 与 Japan 样本的 Desktop/Mobile 成对截图；390px Grid、裁切、字体缩放只能作为实验规则。
4. 日文正文、Feature 与 CTA 字数范围主要来自有限 Tier C 可见标签和代表截图；需在下一轮对 20+ 日文样本进行文本级人工标注。
5. Hero／Product Visual Ratio 目前是视觉估计；Phase 3 应由 Renderer／图像分割产生像素级测量。
6. `EXT_005` 需重截；在此之前不进入 Tier D 视觉频率。
7. 二手 Japan Gallery 样本的 `via` URL 不证明官方邮件归档；只能作为 `secondary_reference`。

Phase 2 在本标准、Machine-readable YAML、Pattern Review 完成后停止；不自动进入 Phase 3。
