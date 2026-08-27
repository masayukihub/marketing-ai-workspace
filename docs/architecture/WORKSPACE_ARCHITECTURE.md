# Workspace Architecture

```text
Official / Feishu Sources
        ↓
Product Knowledge + Source Registry
        ↓
Project Memory
        ↓
Project Visual Context + Visual Pattern Router
        ↓
Skills and Automations
        ↓
Reports / Dashboards / Internal Tools
        ↓
Human Review and Release Gate
```

## 边界

- GitHub 负责版本、评审、测试与部署。
- 飞书和官方资料负责原始事实。
- Project Memory 保存来源关联的当前项目上下文，不充当产品事实库。
- Visual Pattern Router 只选择可复用的项目视觉结构并继承人工 Freeze，不审批产品事实、Claim、素材或发布。
- Skills 只消费事实和上下文，不自行把假设升级为 Claim。
- Apps 只发布已通过对应 Gate 的内容。
