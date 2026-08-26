# 日本营销活动生命周期参考

## 1. 阶段与 Gate

| 阶段 | 核心问题 | 必须产物 | 进入下一阶段的最低条件 |
|---|---|---|---|
| Discover | 为什么做、给谁做 | 问题、受众、机会、假设 | 目标与受众可解释 |
| Plan | 卖什么、怎么讲、在哪投 | 策划案、渠道角色、预算方向 | 产品/Offer 范围明确 |
| Prepare | 是否能安全上线 | 素材表、RACI、Readiness | Blocker 已清零或获明确豁免 |
| Launch | 是否按计划上线和测量 | 链接表、状态表、运行日志 | 链接与事件验证通过 |
| Optimize | 什么需要调整 | 异常、原因、动作 | 修改有 Owner 和指标 |
| Review | 是否达标、以后怎么做 | 复盘、行动计划、数据缺口 | 结论可追溯且口径冻结 |

## 2. Tracking Name 最小字段

推荐稳定顺序：

`market_campaign_stage_channel_placement_audience_product_creative_date_version`

规则：

- 使用小写英文、数字和统一分隔符；不要混用空格、全角字符和临时缩写。
- `market`、`campaign`、`channel`、`date` 为必填。
- 产品需要使用正式短码；组合素材使用已定义的 bundle/solution 短码。
- 一个 Tracking Name 只对应一个可追溯投放单元。
- 版本只在素材或落地逻辑真实变化时递增。

## 3. UTM 最小规范

| 字段 | 用途 | 规则 |
|---|---|---|
| `utm_source` | 平台/发送方 | 使用固定字典，如 google、line、newsletter |
| `utm_medium` | 媒介类型 | 使用固定字典，如 cpc、paid_social、email |
| `utm_campaign` | 活动 | 与活动主 ID 对齐 |
| `utm_content` | 素材/版位 | 对齐 creative 或 placement |
| `utm_term` | 关键词/受众 | 仅在有真实用途时填写 |

保留原始 Landing URL；规范化参数顺序；检查已有 query、fragment、重复参数和编码。不要把敏感信息或个人标识写入 UTM。

### Destination 路由

- 官网、楽天、Yahoo 等外部落地页：按已批准的渠道字典生成 UTM。
- Amazon：先确认 Amazon Attribution/tag 或团队既定方案；不得默认把通用 UTM 加到正式 Amazon URL。
- 目标类型或平台方案未确认：可以生成 Tracking Name 草案，但 Full Tracking URL 必须保持 `NEED_CONFIRMATION`。

## 4. Bitly 与飞书安全流程

固定链路：

`项目资料 → 营销动作 → Tracking Name/Full URL → 数据链路表 → 人工审核 → 飞书导入 → Bitly 人工上传 → 结果下载 → 匹配与写回预览 → 人工确认正式写回`

Codex 只生成 Bitly 人工上传清单和结果匹配预览，不自动登录、创建或上传 Bitly。

Bitly 输入门槛：

- `status = approved`；
- Tracking Name 唯一；
- Full Tracking URL 非空且通过 URL 校验；
- Title、Destination 与 Campaign 一致；
- 没有覆盖已发布短链。

## 5. KPI 定义卡

| 项目 | 内容 |
|---|---|
| 指标名 | 业务可理解的唯一名称 |
| 目的 | 该指标支持什么决策 |
| 公式 | 明确分子、分母、过滤条件 |
| 粒度 | Campaign/渠道/产品/日/素材 |
| 时间 | 时区、周期、截止时间 |
| 归因 | 窗口、点击/浏览、平台差异 |
| 数据源 | 系统、表、字段、Owner |
| 目标/基线 | 目标值及其来源 |
| Guardrail | 不能因优化主指标而恶化的指标 |
| 缺失规则 | Missing、Unverified、Not Comparable，不写成 0 |

## 6. 三份核心文档建议结构

### 营销渠道素材需求汇总

1. 活动信息与版本；
2. 渠道素材总表；
3. 母版与改版关系；
4. Copy/价格/链接/法务依赖；
5. Owner、截止时间和风险。

### 营销策划案

1. 管理判断；
2. 背景、目标、受众与洞察；
3. 产品/Offer 与核心信息；
4. 活动阶段和渠道策略；
5. 内容/素材计划；
6. Tracking 与测量；
7. RACI、时间线、预算方向、风险和 Gate。

### 促销项目目标和数据复盘

1. 结论与目标达成；
2. 数据范围和可信度；
3. 核心 KPI；
4. 历史/目标对比；
5. 渠道、产品、阶段和素材表现；
6. 原因诊断与替代解释；
7. `继续 / 调整 / 停止 / 新增`；
8. 数据补全计划与下次目标。

## 7. 旧 Skill 对应关系

| 旧入口/模块 | 现在所在阶段 |
|---|---|
| `gtm-thinking-framework` | Discover、Plan、Launch Readiness |
| `jp-traffic-link-governance` | Prepare、Launch 的 Tracking/UTM/短链治理 |
| `switchbot-campaign-review` | Review 的数据清洗、指标、报告运行时 |

旧模块可保留脚本和测试，但不应再作为日常首选入口。
