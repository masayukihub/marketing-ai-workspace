# Projects

每个目录是一个正式项目工作入口。`project.yaml` 是统一的项目身份、导航、当前 Gate、Blocker 与 Next Action Manifest；README 保留人类可读入口。

Product Truth、Project Memory、Decision、Approved Claim、Visual Freeze 和正式资产仍由 Manifest 指向各自的权威来源，不在项目目录中重复复制。

## 当前正式项目

- `s30-mini`
- `lock-ultra-max`
- `daily-station`
- `homerunpet`

当前状态必须从最新 `project.yaml` 和 Resolver 结果读取，不能根据目录存在、历史聊天或旧输出判断项目已完成。

## 候选项目

从过往任务中识别、但尚未完成正式建档的项目记录在 [`PROJECT_INBOX.md`](PROJECT_INBOX.md)。候选项只用于 Discovery，不是 Active Project，也不代表产品事实、日期、Owner 或预算已经确认。

遇到候选或未知项目时：

```text
PROJECT_BOOTSTRAP_REQUIRED
→ Source / Objective / Product Boundary / Owner / Stage Review Pack
→ Human Review
→ Project Memory + project.yaml
→ Resolver Validation
→ PR
```

不得自动创建 Formal Project 或 Active 状态。

## 项目任务入口

```text
读取 AGENTS.md 与 operator/ 三个控制文件
→ 运行 skills/project-context-resolver/scripts/resolve_project_context.py
→ 消费最小 Context Package
→ 由 operator/task-routing.yaml 选择四个中文入口之一
→ 执行到下一个 Material Human Gate
```

普通用户不需要手动选择 Product Knowledge、Project Memory、Visual Router、Renderer 或内部 Runtime。
