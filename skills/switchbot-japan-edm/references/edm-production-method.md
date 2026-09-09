# 日本 EDM 生产方法与兼容映射

## 1. 产品角色与位置

| 角色 | 典型证据 | 推荐位置 |
|---|---|---|
| 流量主力 | 高销量、广泛认知、点击吸引力强 | 主题匹配时进入 Hero 或首张主卡 |
| 营收主力 | 销售额或客单贡献高 | Top 3 或主解决方案 |
| 战略新品 | 新品或业务优先级高 | 主推位置，配简短教育 |
| 场景搭档 | 与主品构成完整场景 | 同一方案模块，不单独堆砌 |
| 次级补充 | 相关但优先级较低 | 紧凑 2×2 网格或末段 |
| 移除 | 主题弱或信息不确定 | 不进入主邮件 |

销量与销售额冲突时，不要盲目平均排名。先说明各产品的商业角色，再以 Campaign 的唯一任务作为决胜条件。

## 2. 历史模板优先规则

历史模板只提供已经验证的结构、节奏和模块关系，不能继承旧价格、旧日期、旧产品、旧 Claim 或过期链接。

具体检索、证据分级、Recipe 与 HTML 的衔接见 [history-evidence-workflow.md](history-evidence-workflow.md)。用户指定历史邮件时，实际读取对应 Gmail 邮件或可核对的已有快照，不能仅凭模板库的描述声称“参考了过去推送”。正文、HTML、图片和实际推送状态分别记录；只有主题/纯文本时，不得升级为视觉证据。

推荐匹配维度：

- Campaign 类型与阶段；
- 产品数量和角色组合；
- 是否促销、教育、UGC、场景或 Last Call；
- Hero、CTA、信息密度和期望长度；
- 可用素材类型；
- Desktop/Mobile 证据等级。

匹配后把结构表达为：

`历史证据 → Recipe / Formula → Section → Module → 当前 Content / Asset Slot`

原则：

- 优先复用已经验证的 Formula、Module 和 Visual Rhythm。
- 只在职责或信息层级变化时调整结构，不因单次文案长度随意增加模块。
- 新结构先标记 Candidate，经人工 Review 后才允许进入正式模板库。
- Test、Duplicate、Metadata-only、Reject 和 Anti-pattern 不能作为核心视觉模板。
- Mobile 证据不足时，规则只能作为 Experimental，不得假装已验证。
- 模板选择后输出历史到新稿的模块对照；改稿时同时说明旧稿被替换的位置。Recipe 必须实际决定结构及主次几何，不能只写入模板名称或 CSS 颜色。
- 可继承内容包括 Hero 构图、商品组合方式、图文方向、促销层级、日期条、CTA 形状与模块背景节奏；其有效性以实际图像或渲染证据为准。
- 真实推送也可能有占位 Preheader、过长产品列表、重复 CTA 或旧 No.1 文案。先筛选有效特征，不能因为“曾经发过”就视为良好模板或当前已批准事实。

## 3. 结构与密度

- 一般销售 EDM 控制为约四到五个主要移动端阅读屏，实际以内容任务为准。
- 模块之间留白；模块内的 Label、标题、图片、Copy、价格和 CTA 保持视觉聚合。
- 主推与次级产品的视觉权重来自商业角色，具体采用大卡、左右图文或网格由选定 Recipe 决定；不要把不同历史邮件统一改写为白底卡片列表。
- 每张产品卡只保留一个主要利益点；次要参数移到图标行、对比表、LP 或省略。
- 重复同一目的或 CTA 的模块应合并。
- 不缩小字体、不盲目加列来解决密度问题。

## 4. Campaign 适配

### Teaser

- 强调期待、品类、时间和 Wishlist/Preview 行为。
- 不提前泄露尚未批准的全部优惠，也不制造虚假紧迫感。

### Sale Launch

- 首屏放最强的已确认利益和最清晰购买路径。
- 主推主题匹配、转化潜力和库存确定性高的产品。
- 先解释 Sale，再进入次级品牌故事。

### Category/Solution

- 从日本用户熟悉的问题或生活场景切入。
- 展示完整方案，不堆叠无关 SKU。
- 用场景标签加快扫描。

### Reminder

- 提供新的角度、场景、产品组合或可信证据。
- 不只替换日期后重复发送 Launch 版。

### Last Call

- 使用真实截止时间和剩余购买机会。
- 优先成熟的流量/营收主力和最强已确认 Offer。
- 缩短教育内容，并重复同一主目的地，而不是增加新的 CTA 分支。

## 5. Copy 模式

### Subject / Preheader

- Subject：收件箱中的打开理由；促销上线、场景精选、功能教育分别选择适合的切入点，仅在真实截止条件下使用紧迫感。
- Preheader：补充品类、时间或 Offer 细节，不重复 Subject。
- Hero：打开邮件后的主利益与视觉主题，不要求逐字重复 Subject。
- 重新设计时给出少量可区分的主题方案并推荐一个；已确认的标题保持不变。不能复制历史邮件中类似「ここにプレヘッダーを入れます」的占位文案。

### Hero

1. 短 Campaign/利益标题；
2. 一句连接日常生活的说明；
3. 已确认期间或截止时间；
4. 一个主 CTA。

### 产品卡

1. `SwitchBot + 正式产品名`；
2. 一个结果导向的利益句；
3. 已确认的 MSRP/活动价/折扣，或工作稿中的 `要確認`；
4. 可选的简短 Promotion Strip；
5. 具体 CTA。

### CTA 示例

- `Amazonでセール価格を見る`
- `対象製品をチェック`
- `玄関の防犯アイテムを見る`
- `終了前にチェック`

CTA 必须说明真实下一步，不为视觉变化而增加多个目的地。

## 6. UGC 与素材

UGC 最低要求：

- 原始 Quote 和来源；
- 使用许可；
- 产品映射；
- 日期；
- 归属方式；
- 使用评分或互动指标时有可验证数据。

只能在不改变意义的前提下缩短 Quote。缺少可信 UGC 时，输出素材缺口清单。

正式产品素材规则：

- 官方产品图、UI、包装、配件和安装关系保持原样；
- AI 场景层不能覆盖或改变产品形态；
- 不从竞品或历史邮件复制未授权图片；
- 外部参考只作为 `CREATIVE_REFERENCE`。

## 7. Fact Status

工作表和 Brief 使用：

- `確認済み`：当前来源支持；
- `要確認`：缺失、冲突、不稳定或超出 Runtime 已验证范围；
- `不使用`：风险过高或与本 EDM 无关。

消费者最终稿不能保留会误导用户的占位信息；未确认事实应阻断该模块的正式发布，而不是用猜测替换。

## 8. Runtime 合同

GitHub `skills/edm-generator` 是原有内部确定性 Runtime，在已验证范围内负责：

- 冻结的 Design Standard、Template/Module System 和 Visual Rhythm；
- Input Schema、Campaign Classifier、Template Selector、Module Composer；
- Product/Campaign/Pricing/Claim/Asset Truth Gate；
- Copy、Renderer、600px HTML、Desktop/Mobile 输出和 QA；
- Readiness、人工审批和状态机。

运行前必须检查：

1. Runtime 和依赖真实存在；
2. 不依赖失效的本机绝对路径；
3. 当前产品、活动类型、价格场景和人工审批脚本受支持；
4. 输入事实、素材和授权达到所选输出的 Gate；
5. 没有修改冻结规则、Manifest 或 Fixture 来掩盖单次失败。

当前只验证过的产品/案例不能自动代表所有促销、新品或价格组合。超出覆盖范围时使用 `BLOCKED_RUNTIME_SCOPE`。

`skills/switchbot-japan-edm/scripts/` 增加可移植的历史证据适配路径，服务多产品促销和原 Runtime 未覆盖的内部视觉候选。它不改变冻结 Ruby Runtime 的状态、标准或回归结论，也不新增用户入口。

从统一 Skill 目录执行：

```bash
python scripts/edm_history.py plan --brief <brief.json> --evidence <evidence.json> --out <plan-directory>
python scripts/render_edm.py --input <render-input.json> --plan <plan.json> --out <output-directory>
```

- `assets/history-recipes.json` 保存脱敏版式；真实 Gmail 邮件与证据外置，由任务输入指定。Recipe 名称不是邮件已读取或模板已批准的证明。
- 计划必须给出选源、证据限制、采用的版式和适配理由，渲染输入绑定当前产品、素材、Copy 和链接。具体可用字段以脚本实际输入合同为准，不在文档中补造运行结果。
- 未确认价格、优惠和 URL 可在内部稿省略或保留待配置状态；不能为了填满版面自动使用历史优惠。缺官方原图时，保留明确的缺图版位；整体视觉仍可供讨论，产品素材 Gate 继续保留。
- 用实际 HTML 生成长图。分别报告静态检查、离线排版、浏览器、邮件客户端与 ESP 的执行状态；离线图不能替代浏览器 QA。
- 已有有效 Visual Freeze 或 Accepted Planning Decision 时，仍按项目规则继承。新的历史参考只支持获准的调整范围，不能自动推翻冻结决定。

## 9. 发布状态与人工责任

| 状态 | 含义 | 不能代表 |
|---|---|---|
| `INTERNAL_DRAFT` | 内部结构/文案/视觉草稿 | 设计完成或可发送 |
| `DESIGN_READY` | Brief 和必要事实足以进入制作 | HTML/视觉已验证 |
| `VISUAL_DELIVERABLE_CANDIDATE` | 视觉候选可供 Final Review | Content Approved 或 Production Ready |
| `CONTENT_APPROVED` | 具名人工完成内容批准 | ESP 已就绪 |
| `ESP_READY` | Token、Footer、URL、客户端和发送环境通过 | 已实际发送 |
| `PRODUCTION_READY` | 内容和 ESP Gate 均满足 | 自动发送授权 |

Codex 可以自动校验和生成 Review 材料，但不能代替人工批准人，也不能自动发送。

## 10. 旧入口兼容映射

| 旧入口/模块 | 合并后的职责 |
|---|---|
| `optimize-japan-edm` | `CRITIQUE`、`COPY`、`DESIGN_BRIEF`、`LOCAL_REVISION` 方法层 |
| `edm-generator` | `HTML_VISUAL`、`RESUME` 的内部 Runtime |
| `switchbot-japan-edm-generator-v1-1-internal` | 待源码核验的 Runtime 适配器；不能仅凭截图宣称已合并源码 |
| `switchbot-japan-edm-visual-template-skill` | 待源码核验的历史模板/视觉适配器；只由视觉模式调用 |
| Candidate、旧版、备份、Harness | 测试或归档，不注册为用户入口 |

当前无法读取的模块只保留清晰的接口映射。取得原始目录、Manifest 和测试后，先验证再接入；不能用同名空目录冒充已完成迁移。

## 11. 最终 QA

1. 一封邮件只有一个主任务和主 CTA。
2. 产品排序基于角色，不是单字段排序。
3. Hero、主推和次级产品有清晰权重。
4. 日语简短、自然、结果导向。
5. 模块间宽松、模块内紧凑。
6. UGC 真实、有来源和许可。
7. 价格、折扣、日期、链接和免责声明一致。
8. 产品图、UI 和配件关系未经 AI 改写。
9. Desktop/Mobile/Browser QA 状态与实际执行一致。
10. Final Human、ESP 和发送 Gate 没有被绕过。
11. 所选历史邮件有真实来源，模块对照能解释当前稿的可见版式；没有将 metadata、模板标签或自评分当成视觉证据。
12. 长图来自所交付 HTML；历史事实、私有收件信息及个性化链接没有进入当前消费者稿或代码仓库。
