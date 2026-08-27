# Visual Pattern Memory + Visual Router — Phase 1

## 1. Current Architecture Audit

### 结论

仓库已有成熟的 Amazon 页面参考、结构选择、模板原语和渲染 Gate，不应该重写。Phase 1 只补“项目级、跨渠道、可继承”的视觉决策层。

| 现有能力 | 当前状态 | 直接复用 | Phase 1 处理 |
|---|---|---|---|
| Amazon Reference System | 6 个规范化 Reference、5 个 Story Pattern、5 个 Gallery Sequence、5 个 A+ Sequence | 是 | 通过 Adapter 引用，不复制数据 |
| `reference_matcher.mjs` | 8 个产品/页面匹配字段、缺失信号不补分、结构 Gate | 是 | 继续负责 Amazon 竞品 Reference，不改成跨渠道 Router |
| `reference_decision_adapter.mjs` | Pattern 到 Gallery/A+、Primitive、Renderer、Claim Provenance Gate | 是 | 继续负责 Amazon 页面内落地 |
| `templates/template_library.json` | 19 个已注册 Gallery/A+ Primitive | 是 | Amazon Channel Adapter 只映射，不另建模板库 |
| `category-semantics/smart-lock.json` | 信任、兼容、安装、安全与禁用语义 | 是 | 用于 Lock Ultra Max 的类目级视觉约束 |
| `jp-commerce-content-flow` | Product Truth → Planning → Review → Production → Hardening | 是 | 增加 Project Visual Resolution，不改变原 Gate |
| `switchbot-japan-edm` | 历史 Formula、Module、Visual Rhythm、600px/Mobile/ESP Gate | 是 | 按需读取共享 Visual Profile，Runtime 职责不变 |
| `project-memory-manager` | 项目检索、来源、事实/决策/假设治理 | 是 | Project Context 引用它，但视觉合同不写进 Current Truth |
| `projects/` | 项目工作入口，当前只有 README | 扩展 | 增加三份项目视觉合同 |
| `memory/project-memory/` | 当前上下文、状态、来源、决策 | 是 | 只读为来源；不改 Product Truth 或已有 Decision |

### 明确不重复建设

- 不复制 Amazon 的 6 个 Reference 和 19 个模板原语；
- 不重写 Reference Matcher 的产品级竞品选择；
- 不把 Visual Router 变成超级 Skill；
- 不把 Project Visual Profile 写成 Product Truth；
- 不用视觉评分替代 Claim、Product Layer、Hardening 或 Mobile QA；
- 不把未批准 EDM 规划稿当成 Freeze。

## 2. New Architecture Map

```text
Project Memory + Product Truth + Asset Status
                     ↓
         projects/<id>/project-context.yaml
                     ↓
          ┌─ active visual-freeze.yaml ─┐
          │                              │
          └─ Visual Router + Registry ───┤
                                         ↓
                              visual-profile.yaml
                                         ↓
              ┌──────────────────────────┼─────────────────────┐
              ↓                          ↓                     ↓
      Amazon JP Adapter             EDM Adapter       Future LP/Campaign
              ↓                          ↓                     ↓
 Existing Reference Matcher       Existing EDM         Candidate adapter
 + Category Semantics             Formula/Runtime      (no runtime claim)
 + Templates/Renderer                    ↓                     ↓
              └──────────────────────────┴─────────────────────┘
                                         ↓
             Existing Truth / Claim / Asset / Human / QA Gates
```

用户入口仍是现有四个中文入口；`visual-system/` 不在 `skills/` 下，不注册新 Skill。

## 3. File-level Change List

| 文件/目录 | 变化 |
|---|---|
| [`visual-system/`](../../visual-system/README.md) | 新增共享内部视觉系统与维护入口 |
| [`visual-system/references/`](../../visual-system/references/USAGE.zh-CN.md) | Reference 摄入流程、Amazon 适配与中文使用说明 |
| [`visual-system/patterns/`](../../visual-system/patterns/amazon-mechanism-proof.yaml) | 2 个 Amazon Validated 结构 Pattern、1 个 EDM Candidate、1 个未来 Web Candidate |
| [`visual-system/registry/`](../../visual-system/registry/pattern-registry.yaml) | Pattern/Reference Registry 与 JSON Schema |
| [`visual-system/routing/`](../../visual-system/routing/ROUTING_RULES.md) | 权重、阈值、Channel Adapter 与确定性 Router |
| [`visual-system/design-systems/`](../../visual-system/design-systems/switchbot-jp.yaml) | SwitchBot JP 共享品牌约束 |
| [`visual-system/tests/`](../../visual-system/tests/test_visual_system.py) | Contract、Ranking、Freeze 与入口接入回归 |
| [`projects/s30-mini/`](../../projects/s30-mini/project-context.yaml) | Context、自动 Profile、Candidate Freeze |
| [`projects/lock-ultra-max/`](../../projects/lock-ultra-max/project-context.yaml) | Context 与自动 Profile；不创建 Freeze |
| [`skills/jp-commerce-content-flow/SKILL.md`](../../skills/jp-commerce-content-flow/SKILL.md) | Planning/Production 前接入 Project Visual Resolution |
| [`skills/switchbot-japan-edm/SKILL.md`](../../skills/switchbot-japan-edm/SKILL.md) | 正式项目按需读取共享 Profile/Freeze |

## 4. Visual Pattern Schema

Pattern 最小字段：

```yaml
pattern_id: VP-...
lifecycle:
  status: CANDIDATE | VALIDATED | DEPRECATED
fit:
  channels: []
  categories: []
  consumer_goals: []
  information_complexity: []
  brand_fit: 0-100
  mobile_fit: 0-100
historical_performance:
  status: UNKNOWN | DIRECTION_APPROVED | MEASURED
  score: 0-100
asset_requirements:
  required: []
  optional: []
reusable_layers: []
prohibited_layers: []
sources: []
```

Project Contract：

- `project-context.yaml`：事实/假设状态、市场、渠道、目标、复杂度、视觉原则和素材状态；禁止写死 Pattern。
- `visual-profile.yaml`：Router 生成，保存评分、推荐、Fallback、排除项、原因、Adapter、来源和边界。
- `visual-freeze.yaml`：只保存人工批准或待复核的人工记录。Candidate 必须 `active: false`。

## 5. Routing Rule

权重：Channel 20、Category 15、Consumer Goal 15、Brand 15、Information Complexity 10、Asset 15、Mobile 5、Historical Performance 5。

执行规则：

1. 先检查 active + APPROVED + 具名人工的 Freeze；
2. Freeze 无冲突时继承，不再问视觉方向；
3. 否则按 8 个维度排序；
4. 不支持 Channel 或 Deprecated 直接排除；
5. 默认选择 Top 1；
6. 仅在分差小于 8、Brand Fit 低于 70、素材不满足、Candidate Pattern、低于自动阈值、Freeze 冲突或用户探索时 Human Review；
7. Historical Performance 未知时明确为 `UNKNOWN`，不制造效果数据。

完整规则见 [`ROUTING_RULES.md`](../../visual-system/routing/ROUTING_RULES.md)。

## 6. S30 mini Validation

| 项目 | 结果 |
|---|---|
| 推荐 | `VP-AMZ-MECHANISM-PROOF` |
| Score | 89.7 |
| Fallback | `VP-AMZ-JAPAN-FIT-TRUST` |
| Freeze | `CANDIDATE`，未激活 |
| Human Review | Required |
| 原因 | 官方产品素材为 Partial；机制 Proof 仅 Review Only；现有人工记录没有批准这份 Freeze 合同 |

已存在的 `APP-WHOLE-SET-V3-20260824` 明确批准“整组方向与精确当前输出”，因此生成 Candidate Freeze；其范围明确不包含 Product Truth、Claim Evidence、DVT、Amazon Upload 和 Channel-native Module Fit。

## 7. Lock Ultra Max Validation

| 项目 | 结果 |
|---|---|
| 推荐 | `VP-AMZ-JAPAN-FIT-TRUST` |
| Score | 81.1 |
| Fallback | `VP-AMZ-MECHANISM-PROOF` |
| Freeze | 不生成 |
| Human Review | Required |
| 原因 | 官方产品、安装和兼容素材均 Missing or Unverified |

现有 EDM 文档是 `PLAN_ONLY`，且 Product Truth、Claims、CTA 与素材未完成，不足以建立 Candidate Freeze。

## 8. Regression Test

测试覆盖：

- Registry 与 Pattern ID/状态一致；
- 8 项权重合计 100；
- Project Context 不含具体 Pattern；
- S30 / Lock 排名结果稳定；
- Candidate Freeze 不自动继承；
- 合格 APPROVED Freeze 可继承；
- Deprecated、Channel 冲突、素材缺失会阻断继承；
- Amazon 原 Gate 与 EDM Final Human/ESP Gate 仍在入口合同中；
- Reference 禁止复制项完整。

运行：

```bash
python3 -m unittest discover -s visual-system/tests -p 'test_*.py' -v
python3 tests/validate_workspace.py
```

## 9. 中文使用说明

普通用户只需要三种表达：

1. 第一次：`把这个页面加入我的视觉参考库。`
2. 新项目：`用日本电商内容生成做 XXX。`
3. 老项目：`继续 XXX。`

系统在后台完成 Context、Pattern Ranking、Profile、Freeze 继承和 Channel Adapter。只有真实冲突才需要用户 Review。详细说明见 [`USAGE.zh-CN.md`](../../visual-system/references/USAGE.zh-CN.md)。

## Phase 1 边界

- 已完成结构、规则、自动路由、项目验证和 Skill 接入；
- 未扩展成在线数据库、管理后台或大规模抓取平台；
- 未自动批准 S30 Candidate Freeze；
- 未创建 Lock Ultra Max Freeze；
- 未修改任何已批准 Product Truth、Claim 或 Asset；
- 未实现未来 LP / Campaign 的正式 Runtime，只保留兼容 Adapter Contract。
