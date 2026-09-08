# 能力地图

| 旧入口 | 合并后的内部角色 | 保留能力 | 不再承担 |
|---|---|---|---|
| JP Commerce Creative Flow | `ROUTER + SOURCE GOVERNANCE` | 来源治理、Product Truth、阶段路由、人工Gate、Evidence边界 | 不单独产出创意稿 |
| Japan Listing Demo | `UPSTREAM LISTING ROUTER` | 上游主路由、Checkpoint、Context Firewall | 不承载SwitchBot业务规则 |
| Listing Planning / Production / Hardening | `STAGE RUNTIMES` | Stage 0–10的规划、生产、核验与交付 | 不作为用户入口，不改变Gate顺序 |
| Amazon Japan PDP Generator | `SPEC + TEMPLATE RENDERER` | 7图/A+结构、模板、Spec、Amazon预览、移动端和回归QA | 不直接从原始资料跳到成品 |
| Amazon Listing Creative | `CREATIVE MODULE` | 方向探索、单张深化、局部修改、日文文案、视觉Brief | 不自建另一套完整Listing流程 |

完整调用链、阶段所有权和运行时解析顺序见 [internal-components.md](internal-components.md)。

## 用户入口

用户只调用 `$jp-commerce-content-flow`。内部按任务自动路由：

- 完整页面：Router → Planning → Renderer → Hardening。
- 只探索一张图：Router核对Truth → Creative Module。
- 继续已在做的项目：读取状态 → 当前阶段。
- 修改已批准资产：Local Revision → 最小范围再验证。
- 只要最终HTML：先确认Production Freeze → Hardening。

## 与洞察Skill的关系

`$jp-commerce-insights` 回答“用户、市场和竞品告诉我们什么”。

`$jp-commerce-content-flow` 回答“基于已确认事实和洞察，页面具体做什么、如何生产和验证”。

两者通过 Commerce Insight Pack 的 Creative Handoff 连接；下游不重新抓取完整研究历史。
