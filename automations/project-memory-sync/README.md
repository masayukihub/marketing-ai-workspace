# Project Memory Sync

Status: `PARTIAL`。可复用 `project-memory-manager`；同步只能生成 review proposal，不能静默覆盖重大 Current Truth。

职责边界：Feishu/Source 发现与 Durable Context 更新属于 `project-memory-manager`；`project-context-resolver` 只消费已存在的 Project Memory 与 Manifest，不承担扫描。Review proposal 被接受后，才允许单独更新对应 `project.yaml` 的 Gate、Blocker 或 Next Action。
