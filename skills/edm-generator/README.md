# EDM Visual Generator — Phase 8 Visual Deliverable Candidate / Final Human Review Open

当前已完成：Reference → Inventory → Human Calibration → Pattern Mining → Evidence Repair → Design Standard v1.0 → Template / Module System → Human Decision Integration → EDM Design System v1.0 Freeze → Generator Validation → Renderer Calibration → Production Truth Adapter → One-shot End-to-End Pilot。

Phase 8 已将 Machine-verifiable、Inherited Approval 与 Human-required 责任分开：15 项 Manual Approval 被压缩为 2 项，原 7 条 Required Claim 已完成 Evidence Resolution，6 个官方素材获得 `DESIGN_PRODUCTION_APPROVED`。Lock Ultra 已经三轮受控 One-shot / Browser QA，达到 `VISUAL_DELIVERABLE_CANDIDATE`；Final Human Review 与 ESP Runtime Contract 仍保持独立。

`EDM Design Standard v1.0`、`EDM Design System v1.0` 与 Generator Logic v1.0 均保持冻结。Phase 8 没有新增 Template、Module、Pattern 或 Renderer。当前优先交付营销可用视觉稿；实际发送仍必须完成 Final Human Decision 与 ESP Token Contract，因此 `VISUAL_DELIVERABLE_CANDIDATE` 不等于 `PRODUCTION_READY`。

已完成：

- 40 个外部 EDM 参考案例及全长桌面截图；其中另存 10 个 Mobile 截图。
- 503 条指定官方发件人 Gmail 记录、4 条 Chrome 关键词检索的视觉补充记录、8 条本地文件记录。
- 24 个 Gmail 全长视觉样本、3 个本地 HTML 原型视觉样本。
- 外部来源索引、SwitchBot Inventory、基础标签、重复标记和中文收集报告。
- 27 个 SwitchBot Visual Samples 的最终 Human Review：Tier A 17、Tier B 4、Reject 5、Special Case 1。
- 27 个 Japan EDM 外部样本及本地化字段。
- 94 条 Phase 2 Pattern Analysis、8 个 Anchor 深入分析和 4 个 Reject Anti-pattern。
- `SwitchBot Japan EDM Design Standard v0.1` 与同步的 Machine-readable YAML。
- 可筛选的 Pattern Review HTML，用于继续人工校准规则与证据边界。
- `SBG_003` 完整 600×6278 视觉恢复，并改为 User Voice + Promotion Hybrid 条件性 Anchor。
- 8 个 Tier A Gmail HTML 的 Desktop/Mobile 源码级条件记录；独立渲染视觉 Pair 仍为 0，Mobile Rules 保持 Experimental。
- `SBL_001` 最终改为 Reject／No Tier／Not Anchor／Anti-pattern only；`EXT_005` 保持 Mobile-only Tier D 补充。
- 19 条 Rule Traceability 与只包含 13 个待决策项的 Human Decision Review 页面。
- Phase 3 Human Decision 58/58 回写：6 个 Template Family、15 个 Variant、31 个 Module、6 组 Visual Rhythm 全部 `Keep`。
- 冻结 6 个 Template Family、15 个职责可区分的 Variant 与 31 个可复用 Module；孤立 Module 为 0。
- 冻结 Template Selection、Module Composition 与 Visual Rhythm v1.0；四组相似 Variant 已建立确定性职责边界。
- 建立 `phase4_generator_contract.md`、Machine-readable Input Schema 与确定性 Generator Pipeline。
- 执行 17/17 个 Generator Test Case：Template Selection 命中 17/17，重复输入结构一致，Unsafe Hard Rule 违反、虚假 Claim/Price 与 AI 产品重绘均为 0。
- 每个案例输出 Campaign Brief、Decision Trace、Design Spec、Japanese Copy Draft、Asset Plan 与 QA Report，共 102 个逐案例文件。
- GTC-016 因缺少产品主素材正确 `ASSET_BLOCKED`；GTC-017 可选 EDU-A，但因 Promotion/Period/CTA Destination 缺失正确阻塞 Production。
- 建立 `research/generator_test_review.html`，现已预载正式 Human-assisted Review，并支持本地保存、筛选与 CSV 导出。
- 完成 17/17 Human-assisted Review：Pass 2、Needs Modification 15、Fail 0；15 个修改项均保留为 Copy / Product Knowledge / Asset / Verification 工作，不通过修改冻结规则掩盖缺口。
- 冻结 `generator/generator_logic_v1.0/`，包含 Schema、Decision Logic、v1.0 Rule Dependencies、Test Harness、Human Validation 与可校验 Manifest。
- 生成 `phase5_renderer_brief.md`；仅定义 Renderer 输入、输出、生产原则与 QA Gate，未创建 Renderer。
- 完成 GTC-001、GTC-007、GTC-004、GTC-010 的 16 个 Pilot Truth Pack YAML；价格候选、Claim、CTA、日文名和素材缺口均保持可追溯状态。
- Phase 5A 历史 Gate 判定四个候选均为 `BLOCKED`；Phase 6 仅对其中两个任务新增官方来源 Truth Adapter 与内部 Pilot 素材授权，完成结构和渲染验证，但没有把内部授权提升为生产授权。
- 完成 PILOT-A Lock Ultra 与 PILOT-B Smart Daily Station 的 One-shot 链路；输入未指定 Template、Module、Length 或 Hero。
- 自动选择 `TPL-CONVERT-A / Standard / 10 modules` 与 `TPL-EDU-B / Standard / 10 modules`，生成 600×5374 与 600×4824 的完整 EDM 长图。
- 两案均输出 Editable HTML、Desktop/Mobile/Full PNG、Final Copy、Asset/Truth Manifest、Design Review、QA 与 Product Knowledge Claim Lint。
- `research/end_to_end_review.html` 提供 Tier A 品牌基线、完整链路追溯、六项人工营销审核与 CSV 导出；Human 字段保持空白。

边界：

- 外部案例均来自二手邮件画廊，已标记 `secondary_reference`；复用前仍需回查品牌原始邮件。
- Gmail 截图和索引来自私人邮箱，仅供本地内部研究，不应外传。
- `good / ok / bad / unclassified` 仍是 Phase 1 机器初筛；Human Review 才决定 Tier A／B／Reject／Special Case。
- Phase 2 规则权重固定为 `Tier A > Tier B > Tier C > Tier D`；Tier D 只能补充 Layout、Module 与 Hero 创意。
- 当前正式 Standard 为 v1.0：Hard 18、Soft 16、Experimental 5；v0.1 保留为历史版本。
- Experimental Rules 不得阻塞 Production；所有 Hard Rule 违反均令 `QA = BLOCKED`。
- 本阶段没有编写正式 Generator `SKILL.md`，也没有扩展 Template / Module / Pattern / Design Standard。
- Phase 6 生成的是两个 `INTERNAL_DRAFT` Pilot 的 EDM、PNG 与可编辑 HTML，不是发送用 Production Final；产品本体没有使用 AI 重绘。
- 原 17 个 Phase 4 Fixture 仍是测试输入；Phase 6 只打通两个 Pilot。Product Knowledge 当前仍无这两个产品的 Approved External Claim，真实生产价格、活动期间、素材授权与发送环境需逐案审批。

核心文件：

- `research/source_index.csv`：外部参考索引。
- `research/switchbot_inventory.csv`：Gmail 与本地文件统一 Inventory。
- `research/gmail_switchbot_messages.csv`：Gmail 原始结构化导出。
- `research/collection_report.md`：数量口径、分布、缺口与人工复核清单。
- `research/phase2_input_manifest.csv`：Human Review 加权后的 Phase 2 输入。
- `research/pattern_analysis.csv`：94 个样本的结构化 Pattern 字段与证据方法。
- `research/anchor_reference_analysis.md`：8 个 Anchor 的适用／禁用边界。
- `research/anti_patterns.md`：Reject 导出的 Failure Pattern 与 DO NOT 规则。
- `research/pattern_review.html`：Phase 2 快速人工审核页。
- `research/standard_decision_review.html`：Phase 2.5 待决策规则与样本冲突页面。
- `standards/edm_design_standard_v0.1.md`：SwitchBot Japan EDM 可执行设计标准。
- `standards/edm_design_rules.yaml`：与 Markdown 同步的 Machine-readable Rules。
- `standards/rule_traceability.csv`：规则证据、Reject、置信度、测量类型与 Human Decision 台账。
- `standards/edm_design_standard_v1.0.md`：正式冻结的 SwitchBot Japan EDM Design Standard。
- `standards/edm_design_rules_v1.0.yaml`：后续 Generator 的机器可读规则入口。
- `phase3_design_system_brief.md`：Phase 3 启动时使用的历史输入 Brief，保留用于追溯。
- `design_system/templates_v1.0.yaml`：冻结的 6 个 Template Family 与 15 个 Variant。
- `design_system/modules_v1.0.yaml`：冻结的 31 个 Module 及 Template 使用关系。
- `design_system/template_selection_rules_v1.0.yaml`：确定性的 Template / Variant 选择规则。
- `design_system/module_composition_rules_v1.0.yaml`：Module 组合、依赖与有限验证规则。
- `design_system/visual_rhythm_rules_v1.0.md`：冻结的 Visual Rhythm 规则。
- `research/phase3_design_system_human_decisions.csv`：Phase 3 Human Decision 原始导出副本。
- `phase4_generator_contract.md`：后续正式 Generator Skill 的输入、依赖、流程与输出 Contract。
- `tests/generator_test_cases.yaml`：17 个冻结输入定义；执行结果写入 Generator Outputs，不回写 Fixture。
- `generator/input_schema.yaml`：最低输入、可选输入与 Can Infer / Can Default / Must Verify 策略。
- `generator/pipeline.rb`：读取冻结 v1.0 的确定性 Generator 管线入口。
- `generator/outputs/scorecard.yaml`：17 个案例评分、负向路径与 Renderer Gate 汇总。
- `generator/outputs/GTC-*/`：每案例 6 个 Contract 输出文件。
- `research/generator_test_review.html`：Phase 4 Human Review 页面。
- `research/generator_human_review.csv`：17 个案例的 Human-assisted Review 正式记录。
- `research/phase4_failure_analysis.md`：Human Validation、Needs Modification 分类和 Renderer Gate 判定。
- `generator/generator_logic_v1.0/`：冻结的 Generator Logic v1.0 快照与 Manifest。
- `phase5_renderer_brief.md`：Phase 5 Renderer 的输入、输出、生产原则和 QA Brief。
- `pilot/pilot_case_selection.md`：4 个 Pilot 的选择理由和替代案例排除理由。
- `pilot/truth_pack/`：4 个 Pilot 的 Product Truth、Campaign Truth、Asset Manifest 与 Copy Verification Input。
- `pilot/pilot_truth_pack_summary.md`：Truth/Asset 完整度、QA 和 Renderer 阻塞结论。
- `production_truth/`：Product/Campaign/Claim/Pricing/Asset/Proof/Service/Footer/Legal 的生产事实适配层。
- `production_pipeline/`：One-shot Decision、Length、Copy、Asset Resolver、Renderer 与 QA 管线。
- `production_output/PILOT-A-LOCK-ULTRA/`：Lock Ultra End-to-End Pilot 完整输出。
- `production_output/PILOT-B-DAILY-STATION/`：Smart Daily Station End-to-End Pilot 完整输出。
- `research/end_to_end_review.html`：Phase 6 合并营销审核页与 Human Decision 导出入口。
- `research/phase6_report.md`：Production Truth、Asset、自动决策、交付状态与剩余人工 Gate 总结。
- `research/approval_reduction_report.md`：15 项审批的 AUTO_VERIFY / INHERIT / HUMAN_REQUIRED / NOT_REQUIRED 重分类与 15→2 KPI。
- `research/claim_evidence_resolution.yaml`：原 7 条 Required Claim 的 Source、Evidence、条件、置信度与状态建议。
- `research/phase8_visual_delivery_review.html`：Lock Ultra 五维整封 Final Human Review 与空白 CSV 导出。
- `research/phase8_report.md`：Phase 8 自动关闭范围、三轮 Iteration、Gate 状态与真实剩余阻塞。
- `production_registry/`：Phase 8 Product、Claim、Asset、Campaign、Pricing、Legal、Footer 与 Approval Single Source of Truth。
- `production_registry/readiness_snapshot.yaml`：自动计算的两案 Domain Percent、状态机与逐项 Blocker。
- `production_readiness/evaluate_readiness.rb`：Readiness / Gate 计算与 Output 状态同步。
- `production_readiness/apply_approvals.rb`：Human Approval CSV 审计回写；保留 before/after 与 JSONL Ledger。
- `production_readiness/advance_pilot.rb`：仅在 `CAMPAIGN_READY` 时允许自动重跑 One-shot；不接收 Template、Module、Length 或 Hero 参数。
- `research/production_readiness_dashboard.html`：Phase 8 Visual / Content / ESP / Production Gate 与 Blocker drilldown。
- `research/manual_approval_queue.html`：自动化后仅保留的 2 个正式人工责任项。
- `production_readiness/apply_phase8_visual_review.rb`：五维 Final Review CSV 的审计回写入口。
- `research/design_system_issue_log.md`：Phase 4 运行中发现的问题与未来版本候选；不修改冻结 v1.0。
- `research/screenshots/`：外部、Gmail 与本地 HTML 的视觉截屏。
- `examples/`：指向统一截图源的分类引用；不复制截图文件。
