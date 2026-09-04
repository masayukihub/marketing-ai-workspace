# Operator Layer

`operator/` 是面向日常执行的薄控制层，用于记录默认语言、任务路由、自动执行边界和人工 Gate。

它不新增用户可见 Skill，也不复制任何 Product Truth、Project Memory、Claim、价格、素材或项目状态。

## 文件

| 文件 | 作用 |
|---|---|
| `profile.yaml` | SwitchBot Japan Marketing 的稳定工作偏好、命名和安全边界 |
| `task-routing.yaml` | 将常见任务自动路由到现有四个中文入口及必要内部模块 |
| `review-policy.yaml` | 决定哪些步骤自动继续、哪些情况必须人工审核 |

## Authority

```text
Product Knowledge / Official Source / Project Memory / Decision / project.yaml
>
Operator defaults
>
Chat history or ad-hoc prompt
```

Operator 文件只能决定“怎么执行”，不能决定“产品事实是什么”。发生冲突时，正式来源优先，并保留冲突记录。

## 使用方式

Codex 在读取根目录 `AGENTS.md` 后，应读取这三个文件，再解析具体项目。ChatGPT 在讨论具名项目、“继续”或“下一步”时，也应按 `chatgpt/PROJECT_INSTRUCTIONS.md` 使用相同路由。

普通用户仍只需要使用四个入口：

- `$jp-commerce-insights`
- `$jp-commerce-content-flow`
- `$switchbot-japan-campaign`
- `$switchbot-japan-edm`

KOL、PR、Project Management、Visual Router、Campaign Review Runtime、Amazon Renderer 和 EDM Runtime 都是内部能力，不要求用户手动选择。

## 修改边界

只有稳定的跨项目偏好才写入 `operator/`。单个项目的事实、阶段、Owner、Deadline、资产和决策应继续写入该项目的正式治理位置。
