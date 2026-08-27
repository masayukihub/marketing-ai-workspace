# Project Memory

每个项目必须包含：`PROJECT.md`、`STATUS.md`、`DECISIONS.md`、`SOURCES.md`、`TODO.md`。

Project Memory 保存当前项目上下文和已确认决策，不是文档备份，也不替代 Product Knowledge。重大事实或决策变更必须保留来源并经过人工 Review。

项目入口和任务路由由 `projects/<project-id>/project.yaml` 与 `project-context-resolver` 负责。Project Memory Manager 负责新 Source、Durable Context 和 Memory Update；Resolver 不承担飞书扫描或事实写入。
