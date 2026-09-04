# SwitchBot Japan KOL / PR 操作手册

这份手册用于你最常见的 KOL、YouTube、媒体和 PR 工作：历史合作复盘、竞品合作分析、候选名单、合作方向、Brief、预算/KPI、Tracking 和长期关系沉淀。

日常统一从 `$switchbot-japan-campaign` 进入；需要外部证据时自动调用 `$jp-commerce-insights`，需要创作者评估时调用内部 `influencer-marketing`。用户不需要手动切换这些模块。

## 1. 先判断这是 KOL 还是 PR

| 类型 | 核心价值 | 主要指标 | 常见交付 |
|---|---|---|---|
| KOL / Creator | 借助受众信任，演示产品、解释场景、带来内容与转化 | 有效播放、观看质量、互动、点击、转化、内容复用价值 | YouTube/IG/TikTok/X 内容、Usage Rights、素材 |
| PR / Media | 建立第三方可信度、新闻性、行业认知和搜索长期资产 | 有效媒体覆盖、报道质量、核心 Message 命中、引用、自然搜索和后续转载 | Press Release、媒体 Brief、Hands-on、采访、专题 |

KOL 和 PR 可以属于同一个 Launch Plan，但不能用同一套名单、Brief 或 KPI。

## 2. 标准 Flow

```text
项目 / 产品 / Offer / 上市阶段
→ Product Truth 与 Approved Claim
→ SwitchBot 历史合作证据
→ 竞品历史合作证据
→ Audience / Scene / Content Gap
→ KOL Segment 与 Media Segment
→ Shortlist / Priority
→ Collaboration Brief
→ Usage Rights / Disclosure / Tracking / KPI
→ Human Review
→ 人工邀约和执行
→ Results / Relationship Tier / Memory Proposal
```

## 3. 历史合作审计

每次新品不要从空白名单开始。先回答：

1. SwitchBot 同系列过去合作了多少人/媒体；
2. 使用了哪些平台与内容形式；
3. 哪些卖点和演示方式最常出现；
4. 哪些内容得到较高有效播放、评论质量、点击或长期搜索；
5. 哪些合作只有曝光，没有清晰产品理解；
6. 哪些人已合作过，应该复投、升级、暂停或避免重复；
7. 哪些赛道、粉丝层级、内容风格仍有空缺。

### 历史记录最低字段

```text
partner_id
partner_name
partner_type: creator | media
platform
channel_url_or_public_source
country_language
follower_or_subscriber_as_of
content_url
publish_date
product_variant_offer
content_format
organic_sponsored_gifted
message_points
proof_or_demo
views_as_of
engagement_as_of
click_or_sales_if_available
usage_rights
brand_safety_notes
result_status
source_id
retrieved_at
```

不同时间抓取的播放量不能直接当同一截止时间排名。缺失点击/销售时保持 `NOT_AVAILABLE`，不要写成 0。

## 4. 竞品合作审计

竞品内容只能证明“竞品怎样做”，不能证明该做法一定适合 SwitchBot。

至少分析：

- 竞品选择哪些 Creator / Media Segment；
- 视频是 Dedicated Review、Integration、Comparison、How-to、Lifestyle 还是 Deal；
- 使用了哪些购买障碍和演示结构；
- 是否有长期复投；
- 评论区真实疑问是什么；
- 是否出现明显品牌偏好或排他风险；
- 哪些表达已经被占据，哪些内容空位仍可切入。

## 5. KOL 筛选标准

### 通用评分维度

| 维度 | 重点 |
|---|---|
| Audience Fit | 观众是否真的可能购买该产品 |
| Category Fit | 是否持续做智能家居、家电、清洁、宠物、生活改善等相关内容 |
| Competitor Evidence | 是否测评过同类竞品，能否证明品类理解 |
| Content Quality | 演示、叙事、画面、评论区和长期搜索价值 |
| Sponsored Performance | 广告内容是否仍有真实观看与互动 |
| Brand Safety | 最近内容、争议、竞品冲突和表达风险 |
| Production Fit | 能否完成必须演示的场景和镜头 |
| Cost Efficiency | 费用与有效观看、内容资产、转化潜力是否匹配 |
| Relationship Potential | 是否值得持续合作，而不是一次性投放 |

### 你常用的日本 YouTube 优先条件

对 homerunPET 或类似垂直产品，默认优先：

```text
日本市场
YouTube 为主
约 1万–10万订阅优先
宠物内容占比较高
测评过同类竞品
未合作过 homerunPET
适合喂食器、饮水机、吹水机、洗澡器等场景
评论区有真实宠物主互动
```

这只是筛选策略，不是硬性事实。粉丝量和是否合作过必须基于当前公开证据和内部记录验证。

### SwitchBot 不同产品的 Creator Segment

| 产品方向 | 优先 Segment |
|---|---|
| 扫地机 / S30 mini | 小户型生活、清洁家电、共働き、育儿家庭、宠物家庭、家电测评 |
| Lock / Doorbell | 智能家居、防犯、租房/家庭安全、DIY、生活改善、科技评测 |
| ハブ / Sensor / Automation | 智能家居自动化、Matter、Apple/Google/Alexa 生态、效率生活 |
| Daily Station / Weather | 家庭信息、育儿、生活管理、智能家居、桌面与家居科技 |
| homerunPET | 猫犬日常、宠物护理、宠物家电、养宠经验、宠物空间改造 |

## 6. 名单输出格式

不要只给一列名字。正式 Shortlist 至少包含：

```text
Priority
Partner Name
Partner Type
Platform
Public URL
Subscribers / Followers + as_of
Main Content Category
Audience / Scene Fit
Relevant Competitor Content
Prior SwitchBot / homerunPET Cooperation
Recommended Product
Recommended Content Format
Recommended Message / Demo
Why Now
Expected Role
Estimated Cost Tier
Expected KPI Type
Usage Rights Potential
Brand / Competitor Risk
Contact Status
Source IDs
Retrieved At
Confidence
```

### 优先级定义

- `P0`：高匹配、当前阶段最值得直接接触；
- `P1`：适合补充覆盖或第二批；
- `P2`：需进一步验证受众、预算或风险；
- `DO_NOT_CONTACT`：竞品排他、明显品牌风险、数据异常或不符合当前目标。

不要把“粉丝多”自动等同于 P0。

## 7. 内容形式选择

| 目标 | 推荐形式 |
|---|---|
| 建立产品理解 | Dedicated Review / Hands-on |
| 低成本扩大触达 | Integration / Seeding / Short |
| 证明差异 | Comparison，但必须避免不实贬损和无证据 Claim |
| 降低安装/使用障碍 | How-to / Setup / 真实一周体验 |
| 生活场景 | Routine / Before-After / 家庭问题解决 |
| 转化 | Deal / Coupon / Affiliate，但必须先冻结 Offer、链接和 Tracking |
| 长期信任 | Repeat Collaboration / Ambassador / Series |

新品早期不要只买 Deal 视频。先确保用户能理解：这是什么、解决什么、为什么可信、是否适合我。

## 8. KOL Brief 模板

Brief 不应逐字控制创作者。固定以下内容：

```text
Background
Campaign Objective
Target Audience
Product / Variant / Offer
Single Core Promise
2–3 Key Talking Points
Required Demo / Proof
Recommended Story Flow
Must Show
Must Mention
Must Not Say
Approved Claims
Pending / Forbidden Claims
CTA / Destination / Tracking
Promotion / Period / Conditions
Disclosure
Usage Rights
Deliverables
Posting Window
Review / Revision Boundary
Success Metrics
Asset / Sample Logistics
Open Questions
```

### 推荐视频结构

```text
观众现实问题
→ 为什么现有方式不够
→ 产品进入生活场景
→ 2–3 个关键演示
→ 使用限制或适合人群
→ 真实体验总结
→ CTA
```

## 9. PR / Media Segment

### 常见角色

| 媒体方向 | 适合内容 |
|---|---|
| 家电/科技媒体 | 新品、性能、生态、Hands-on、比较 |
| 智能家居/IoT | 自动化、Matter、生态联动、安装使用 |
| 生活/育儿 | 用户场景、便利、共働き、家庭问题解决 |
| 防犯/住宅 | Lock、Doorbell、安全和居住场景 |
| 宠物媒体 | 宠物护理、健康、清洁、日常照护 |
| 商业/品牌 | 经销合作、品牌进入、市场策略、公司故事 |

### PR Brief 最低字段

```text
News Angle
Why Now
Target Media Segment
Product / Offer Scope
3 Key Messages
Proof / Data / Demo
Spokesperson / Interview Topic
Embargo / Launch Timing
Images / Assets / Rights
Approved Claims
Prohibited Claims
Media FAQ
Call to Action
Follow-up Plan
Measurement
```

PR 的新闻角度不能只是“发布了一款新品”。需要回答它对日本用户、行业或生活方式有什么新的意义。

## 10. KPI 与预期

### KOL

根据目标选择：

- 有效播放和观看时长；
- 评论区相关问题和正向理解；
- 点击、Coupon、Affiliate 或 Amazon Attribution；
- 品牌搜索和后续自然流量；
- 内容二次使用表现；
- Cost per Qualified View / Click / Conversion；
- Repeat / Long-tail Performance。

### PR

- 目标媒体命中率；
- 报道质量和核心 Message 命中；
- 原创 Hands-on / Interview 比例；
- 自然转载与搜索可见性；
- 引荐流量；
- 后续媒体关系；
- 与 Launch 节奏和内容资产的协同。

不要把 AVE/EMV 或总曝光作为唯一结论。

## 11. Tracking 和权利

合作前冻结：

```text
Tracking Name
Destination URL
UTM / Amazon Attribution / Coupon
Content Usage Rights
Paid Media Rights
Usage Period
Territory
Exclusivity
Raw File Availability
Whitelisting / Creator Ads
Disclosure Requirement
```

Amazon 链接不得默认附加通用 UTM；先确认 Amazon Attribution 或团队既定方案。

## 12. 自动化边界

### 默认自动完成

- 历史内容和公开页面检索；
- 去重和实体映射；
- 平台、粉丝层级、内容类别和竞品经历分类；
- 建立评分和优先级候选；
- 生成 Brief、KPI、Tracking 和 Owner Action Pack；
- 将多个缺口合并成一次 Human Review。

### 必须停下

- Product / Offer / Claim 不清；
- 需要决定预算、费用或合作承诺；
- 竞品排他、品牌安全或法律风险；
- 需要正式联系人、邮件发送或飞书写回；
- 需要批准最终 Brief、合同、Usage Rights 或发布。

不自动发送邀约、不自动承诺费用、不自动签署权利、不自动写正式飞书名单。

## 13. 直接复制的任务指令

### SwitchBot 历史 KOL/PR 复盘

```text
使用 $switchbot-japan-campaign，解析【项目】。
先通过 $jp-commerce-insights 审计 SwitchBot 同系列和主要竞品过往 KOL/PR：数量、平台、内容形式、播放/覆盖、核心 Message、优缺点和证据限制。
再按 KOL 与 PR 分别给出：应该合作的 Segment、候选标准、内容方向、媒体方向、Brief、预算/KPI假设和执行节奏。
一次性输出 Review Pack；不要逐条询问，不自动发送。
```

### homerunPET 日本 YouTube 名单

```text
使用 $switchbot-japan-campaign，解析 homerunPET 项目。
筛选日本 YouTube 宠物向 Creator，优先约1万–10万订阅、测评过同类竞品、未合作过 homerunPET、适合喂食器/饮水机/吹水机/洗澡器。
名单必须包含公开来源、订阅数截止时间、竞品视频、内容适配、合作理由、推荐产品、预计形式、风险和信心等级。
生成 KOL Brief 与 Tracking/KPI 方案，停在 Shortlist Human Review Gate。
```

### Lock Ultra Max KOL/PR

```text
使用 $switchbot-japan-campaign，解析 Lock Ultra Max 项目。
审计 SwitchBot 过去 Lock 系列与 SESAME、Qrio 等相关竞品的日本 Creator/媒体动作。
区分防犯、智能家居、家电测评、住宅/DIY、生活改善五类 Segment；给出 Launch 前后节奏、Hands-on/Comparison/How-to 角色、媒体角度、Brief 和预期。
未批准的解锁速度、电池、认证和兼容性不得进入对外 Brief。
```

## 14. 复盘和长期关系

每次合作结束后将 Partner 标记为：

```text
REPEAT_PRIORITY
REPEAT_CONDITIONAL
ONE_OFF_COMPLETE
SEEDING_ONLY
PAUSE
DO_NOT_REENGAGE
```

并记录原因：受众匹配、内容质量、沟通、准时、事实准确、播放质量、转化、使用权和长期价值。

可持续结论写入 Project Memory Proposal；跨项目稳定的筛选规则写入 Skill Learning Proposal。不要把一次合作的偶然表现直接变成全局规则。
