# ChatGPT Project Context Contract

本目录用于让 ChatGPT 读取 GitHub 项目状态、理解用户稳定工作偏好并路由任务，但不创建新的 Truth Source。

日常入口见仓库根目录 [`START_HERE.md`](../START_HERE.md)。

## Runtime Authority

1. GitHub `main` 是项目、Skill、Manifest、Decision 和正式状态的版本控制 Authority。
2. 讨论具名项目、Skill、“继续”或“下一步”时，必须先确认最新 `main` HEAD。
3. 依次读取最新 `main` 的：
   - `AGENTS.md`；
   - `operator/profile.yaml`；
   - `operator/task-routing.yaml`；
   - `operator/review-policy.yaml`；
   - `projects/<project-id>/project.yaml`；
   - Manifest / Context Package 指向的任务相关 Sources。
4. `projects/<project-id>/chatgpt-context.md` 只是生成型阅读快照，不是 Product Truth、Project Memory、Decision 或 Approval。
5. ChatGPT Memory 与历史聊天可帮助识别稳定偏好和候选需求，但不得覆盖 GitHub Product Knowledge、Project Memory、Decision 或 Manifest。
6. 无法读取或确认 GitHub `main` 时，输出 `GITHUB_CONTEXT_UNVERIFIED`，不得把快照或历史聊天提升为当前正式状态。
7. 对话中出现的批准，只有在相应 Decision/状态写入正式位置并合并到 `main` 后，才成为 Formal State。

## Authority Precedence

```text
Product Knowledge / Official Source / Project Memory / Accepted Decision / project.yaml
>
Operator defaults
>
ChatGPT generated snapshot
>
Chat history / ChatGPT Memory / model inference
```

Operator 只决定语言、路由、自动执行和审核边界，不决定产品事实。发生冲突时保留差异，以更高 Authority 为准；不得静默回写或自动批准 Product Truth、Claim、价格、上市信息、Visual Freeze、Asset、Send 或 Publication。

## Minimum Read Procedure

### 具名项目

1. 获取并记录最新 `main` HEAD。
2. 读取根目录 `AGENTS.md` 与三个 Operator 文件。
3. 用 `project-context-resolver` 解析项目和任务类型。
4. 读取 Context Package 中标记为 available 的最小 Sources。
5. 检查 `effective_freshness_status`、Blocker、Human Approval 与 Next Action。
6. 根据 `operator/task-routing.yaml` 选择四个中文入口之一。
7. 快照 commit 与最新 `main` 不一致时，先重新生成或直接读取最新 GitHub Sources。

### 未知或未建档项目

1. 检查 `projects/PROJECT_INBOX.md`、现有项目 ID 和 aliases。
2. 未找到正式项目时返回 `PROJECT_BOOTSTRAP_REQUIRED`。
3. 先生成 Source / Objective / Product Boundary / Owner / Stage / Blocker Review Pack。
4. 不自动创建 Formal Project、Product Truth 或 Active 状态。

## User-facing Task Routing

普通用户只需要四个入口：

| 任务 | 入口 |
|---|---|
| 日本市场、关键词、竞品、VOC、评论、Listing 证据 | `$jp-commerce-insights` |
| Amazon JP Gallery、A+、Listing、卖点图、Review HTML | `$jp-commerce-content-flow` |
| GTM、项目管理、KOL/PR、Tracking、活动策划与复盘 | `$switchbot-japan-campaign` |
| 日本 EDM 文案、Brief、HTML、视觉和发送前 QA | `$switchbot-japan-edm` |

不要要求用户手动选择 Product Knowledge、Project Memory、Visual Router、Amazon Renderer、Campaign Review Runtime、EDM Runtime、Customer Review 或 Influencer Marketing。按任务路由自动调用内部模块。

## Continuation Contract

用户说“继续”“下一步”“接着做”时：

1. 读取正式项目 Manifest 和 Next Action；
2. 选择第一个允许执行的未完成 P0，再到 P1、P2；
3. 保留 Blocker、Freshness 和 Human Approval 限制；
4. 不重做已批准的 Product、Offer、Storyline、Visual Direction、Template 或精确资产；
5. 默认执行到下一个 Material Human Gate；
6. 普通过程只汇报：

```text
已完成：
待处理：
下一步：
```

“先这样”不自动代表跨越 Major Gate；“这张先过”只锁定当前精确候选，不等于整套或发布批准。

## Default Automation

自动继续：

- 项目和来源解析；
- 内部 Skill / Runtime 路由；
- 格式规范化、去重和 Source Map；
- 在已批准范围内选择 Formula、Template、Pattern 和执行模式；
- 生成内部 Draft、Brief、Review HTML、Run Manifest 和 QA；
- 最多两轮不改变事实/范围的文案去重、缩短、排版和移动端修复；
- 多个缺口合并为按 Owner 分类的一次性补证包；
- 保留已批准内容，只重开最小必要范围。

必须停下：

- Product / Variant / Bundle / Offer 无法唯一确定；
- Claim、价格、折扣、日期、认证、法务或外部链接需要批准；
- Target、Positioning、Primary Message 或 Scope 发生实质变化；
- 没有可继承视觉决定且 Router 低置信度或冲突；
- 需要批准精确最终资产、Whole-set、Visual Freeze 或 Final Content；
- 飞书/Product Knowledge 正式写回、Bitly、Amazon 上传、ESP 发送或外部发布；
- 两次自动修复后硬性 QA 仍失败。

完整边界以 `operator/review-policy.yaml` 为准。

## Language and Output

- 内部解释、结论、风险和行动项默认简体中文。
- 面向日本消费者和日本合作方的正式文案使用自然、可直接复制的日语。
- 公司名写 `SWITCHBOT株式会社`。
- 产品名使用 `SwitchBot + 正式产品名`。
- 日语中的 hub 写「ハブ」。
- 正式交付先给管理判断，再给证据、影响、动作、Owner/Deadline 和风险。
- 避免空泛的“加强曝光”“优化素材”“提升高级感”，必须指出具体页面、模块、句子、素材或动作。

## Source and Tool Honesty

- 飞书工具只有真实返回正文或结构化数据及 Source Metadata，才算读取成功。
- 认证成功、工具存在、搜索命中或只返回标题，不等于读取了文档。
- Renderer、浏览器、Pillow、Playwright、正式 Runtime 没有实际运行时，不得声称相应 QA PASS。
- 缺失值保持 Missing / Unknown / Unverified，不写成 0、成功或已批准。
- Fixture、占位图和合成数据不得冒充正式产品资料或生产结果。

## Formal-state Boundary

不得静默自动批准或发布：

```text
Product Truth
Approved Claim
Price / Promotion
Launch Date
Visual Freeze
Exact Asset
Final Content
ESP Send
Amazon Upload
Feishu Writeback
External Publication
Permission Change
```

Candidate、Draft、Visual Complete、Browser QA PASS 和 Review Ready 都不等于 Publish Ready。
