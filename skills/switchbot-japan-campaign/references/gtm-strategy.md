# GTM 策略决策接入契约 v1.0

这是 Campaign PLAN 的内部模块，不是第五个用户入口。只处理策略决策及其向 Brief 的交接，不负责渠道执行、正式写回或发布。

## 路由与顺序

- 新品完整 GTM，或受众、场景、定位、核心价值、主信息等发生实质改变：运行本模块。
- 已确认方向下的局部文案、尺寸改版、历史活动续作：继承已接受 baseline，只检查当前范围，不强制补齐十四问。
- 老项目没有 decision pack：继续原有 Accepted Decision / Campaign Context 和原 Gate，标记 `LEGACY_SCOPED_REVIEW`；只有策略发生变化时才迁移，不能伪造一个已批准版本。
- `route_request()` 提供以上路由判断。KOL名单、单封EDM或单张图任务不因 Campaign 使用 PLAN 而自动扩大成完整 GTM。

```text
Resolver / Product Truth / Commerce Insight Pack
→ 00 GTM答案完整度地图
→ 候选比较、价值—证据链、反证与补证任务
→ STRATEGY_SCOPE_GATE（现有 Gate）
→ 人工接受的准确策略版本
→ One Pager / 同版本各渠道 Brief
```

策略分析前读取 [藏锋理论应用与来源边界](gtm-theory.md)。本模块只引用必要的方法，不复制完整公众号知识库。

## 输入与评估

运行仓库脚本，不调用全局镜像或旧独立 `gtm-thinking-framework` 脚本：

```bash
python3 skills/switchbot-japan-campaign/scripts/gtm_strategy.py assess INPUT.json --output-dir NEW_RUN_DIR
```

空输入模板：[gtm_input.example.json](../assets/gtm_input.example.json)。未知答案可省略，生成器会保留全部十四问为 Unknown，而不是补造结论。`--as-of` 仅用于确定日期的审计/测试，正常运行使用当天。

必填元数据：`schema_version: "1.0"`、`project_id`、`market`（日本为 `JP`）、`scope_ref`、`strategy_version`。`scope_ref` 标识准确产品/变体/Offer决策范围，不填写规格副本。

`context` 来自本次 Resolver 与实际来源读取，包含：

- `effective_freshness_status`、`state_as_of`、`threshold_days`：沿用 Resolver，不用输出文件日期刷新旧状态；
- `product_truth_ref`：正式指针，未知为 null；
- `blocking_items`：当前任务有效的 Blocker ID，不遗漏或自行豁免；
- 可附 `resolver_ref`、`main_sha`、`source_refs` 以供追溯。

十四个稳定问题 ID：

`why_now, primary_audience, core_problem, old_vs_new, category, positioning, core_value, rtb, objection, message_hierarchy, launch_story, channel_role, launch_sequence, success_metric`

每个 answer：

```json
{
  "id": "primary_audience",
  "conclusion": "Unknown",
  "confidence": "Unknown",
  "classification": "HYPOTHESIS",
  "origin": "New Hypothesis",
  "principle_ids": ["F11"],
  "evidence_ids": [],
  "core_scene": "Unknown",
  "selection_reason": "Unknown",
  "disconfirming_evidence": "Unknown",
  "stop_doing": "Unknown",
  "candidates": [],
  "gaps": ["需要日本本地的触发行为与现有替代方式证据"],
  "evidence_needed": "决策相关的最小必要证据",
  "validation_method": "待定义，不能把假想访谈当成VOC",
  "owner": "Unassigned",
  "deadline": "TBD",
  "priority": "P0",
  "decision_affected": "primary_audience"
}
```

`classification` 独立于思想来源，使用 FACT / DECISION / HYPOTHESIS / RECOMMENDATION / DATA_GAP / RISK。`origin` 只允许 Source Idea / Synthesized Insight / New Hypothesis。针对 SwitchBot 得出的新项目判断通常不是 Source Idea，即使使用了作者框架。

FACT另标 `fact_domain`：product / market / consumer / competitor / test；市场事实不要求产品批准，产品域、RTB及显式 `requires_product_truth` 的结论才要求准确产品批准来源。未知事实领域先澄清，不能改标Recommendation绕过产品事实门槛。

受众、定位、核心价值三个选择必须有一个 `preferred` 候选，以及至少一个有理由的 `deferred` 或 `rejected` 候选；每个候选有 `id, description, status, reason`。未研究出候选时留空，不能为了 Gate 编造。明确 `stop_doing`，不要只写一个赢家。

前十问为策略关键依赖，必须记录选择理由与可观察的反证。日本 positioning 另外要求 `conclusion_ja`，用于验证日本市场逻辑，不代表消费者文案已获批准。

## 来源证据契约

每个 evidence 对象包括：

`id, ref, kind, status, market, scope_ref, as_of, valid_until, assessed_by, independence_key, supports`

- `kind`：product_truth / approved_claim / market / voc / competitor / test / decision / theory。
- `status: verified` 只能由真实阅读和评估后填写；只有标题、搜索摘要或工具连接成功不能填写 verified。
- `supports` 是 question_id → 支持理由的映射。引用存在不等于支持结论，必须说明具体对应关系。
- `as_of` 是证据时点，`valid_until` 是明确的复核期限，不允许任意延长以通过 Gate；稳定机制与价格等易变事实可采用不同期限，并在来源评估中解释。
- `independence_key` 标记独立采样/来源。转载、同一研究的不同网页不能算独立证据；同一个 ref 不重复计数。
- `contradicts` 是尚未解决的反证 question_id 列表，`conflicts_with` 是尚未解决的来源冲突 ID。即使没有选入答案的 evidence_ids，登记的反证仍会阻断对应结论。
- 产品事实及 RTB 还需要 product_truth / approved_claim 类型和 `approval_ref`。研究、消费者认知、从众或作者案例都不能替代该批准。
- 中国案例、其他变体、过期数据、theory 和内部 decision 不自动验证日本项目。

评估器最多保留调用方的 confidence，不会自动升级：无可用证据最多 Low，单一/独立性未确认来源最多 Medium；多份独立来源或准确范围内的正式产品事实可保留 High。仍有缺口时最多 Medium。Low/Unknown、冲突、禁止Claim不得进入 One Pager。

**自动评估只验证结构化来源评估是否完整一致，不能证实网页内容、评估理由的真实性、样本代表性或审批人的权限。** Source QA 和 Strategy Human Review 必须实际阅读支持链；不得把脚本 PASS 当成市场验证。

## 依赖、Gate 与输出

核心受众影响问题定义；问题和现有替代方式影响定位/价值；定位、价值、RTB、异议共同影响信息层级。上游 Low/Unknown 会阻断依赖的下游答案。

- 前十问任何一项不足、Product Truth缺失、当前Blocker未解或项目stale/unknown：策略 Red，仅进行补证和Review准备。
- 前十问至少 Medium：允许提交既有 Strategy Gate；Yellow必须保留限制，Green也不自动接受。
- A–F 是完整度诊断，不新增六个人工审批。F Channel 是下游缺口，不能形成“先要渠道计划才能批准策略”的循环依赖。
- 本模块永远不生成渠道执行计划。产品、Claim、预算、商业、资产、生产和发布保留原审批。

固定生成顺序：

1. `00_gtm_answer_completeness_map.md`：五列主会议表；
2. `01_strategy_decisions.md`：十四问、候选比较、思想来源、证据与反证；
3. `02_strategy_review_gate.md`：诊断与现有策略Gate；
4. `03_validation_plan.csv`：按决策关联Owner/期限/验证任务，包括项目上下文阻塞；
5. `04_gtm_decision_pack.json`：唯一结构化策略来源，始终保留生成时的 proposed 状态；
6. `05_gtm_one_pager.md`：未取得准确版本的接受记录时只输出 Deferred；
7. `06_campaign_context_patch.proposed.json`：仅提出 Campaign Context 的引用补丁，不写正式数据。

目录必须是新 run，不覆盖旧批准对象。Campaign Context 的 `gtm_decision_pack` 包含 `project_id, strategy_version, path, sha256`；相对路径以所在Context文件为基准，实际接入时只更新指针，不复制产品事实。

## 人工接受与 Brief 继承

现有 Strategy Gate 人审后，由原 Decision Owner 正式记录；本模块不能创建接受记录。机器适配的接受记录须具有以下字段：

`decision_id, project_id, market, scope_ref, strategy_version, pack_sha256, gate: STRATEGY_SCOPE_GATE, status: accepted, reviewer, approved_at, valid_until, source`

接受对象包含整个 decision pack 的规范化 SHA-256，任何改变都不能继承原批准。`source` 指向具名人审证据；审批有效期不得超过相关证据可使用范围。记录合并 main 后才作为 Formal State。历史Markdown Decision无需批量迁移，也不能由模型自行翻译成一个 accepted JSON。

接受与渲染按实际审核/使用日复核，不用旧assessment_date判断新批准是否有效。One Pager检查实际将输出的问题；Brief检查核心策略及其声明的依赖。补充结论证据到期也不能继续继承，但未知的下游Channel问题不因此成为核心策略审批前置。

```bash
python3 skills/switchbot-japan-campaign/scripts/gtm_strategy.py render-accepted \
  --pack PACK.json --decision-record REPO_RELATIVE_DECISION.json \
  --authority-ref VERIFIED_MAIN_FULL_SHA --workspace . --output-dir NEW_ACCEPTED_RENDER_DIR

python3 skills/switchbot-japan-campaign/scripts/gtm_strategy.py check-brief \
  --pack PACK.json --brief BRIEF.json --decision-record REPO_RELATIVE_DECISION.json \
  --authority-ref VERIFIED_MAIN_FULL_SHA --workspace .
```

CLI 从经 preflight 确认的 main 提交读取接受记录，不读取本地被改成 accepted 的文件。调用前必须核验远端最新 main；脚本验证该SHA属于 origin/main，但不替代网络freshness检查。

Amazon/EDM/PR/KOL Brief 共用 `project_id, brief_id, gtm_decision_pack, decision_ids`。如重复填写策略结论，放在 `strategy_assertions`（question_id → 原结论）供漂移校验；自然日语表达和版位Copy另存，不要求各渠道使用同一句话。原Brief自由文本也必须人工核对，脚本不会解析任意文档。

`check-brief` 返回相同核心策略投影和限制；`STRATEGY_INHERITED` 仅说明策略引用可用，不代表产品事实、Claim、制作或发布已批准。

## 增量变更

```bash
python3 skills/switchbot-japan-campaign/scripts/gtm_strategy.py assess NEW_INPUT.json \
  --previous-pack OLD_PACK.json --briefs BRIEF_INDEX.json --output-dir NEW_RUN_DIR
```

变更结论、场景、证据、关键范围或有效性时必须使用新 strategy_version。`07_brief_impact.json` 标记受影响的下游决策和旧版本Brief，不改写原文，不取消或迁移旧批准；由现有Gate决定新版本是否取代旧版。

测试：`python3 -m pytest -q skills/switchbot-japan-campaign/tests`。
