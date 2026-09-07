# Flow 与 Codex 能力衔接及同步

## 结论

继续保留四个业务入口。仓库负责规则、项目上下文和可复现 Runtime；Codex 中的个人技能负责发现入口，按任务调用实际可用的工具。安装了入口，不代表已经安装 Renderer、模板、Product Knowledge、Visual Router 或浏览器依赖。

## 结合点

| 业务入口 | 可结合的 Codex 能力 | 交接内容 | 边界 |
|---|---|---|---|
| `jp-commerce-insights` | 网络搜索、浏览器、表格分析 | 带 URL、日期、范围的 Insight Pack / Creative Handoff | 研究与 VOC 不升级为 Approved Claim；只在工具真实可用时执行 |
| `jp-commerce-content-flow` | 图像生成、官方产品素材、已有 Amazon Renderer、浏览器 QA | 已批准 Asset ID / Handoff → 场景层 → 官方产品层与文字层 → Review HTML | 图像生成只处理获准场景层；不重画正式产品、Logo 或精确 UI |
| `switchbot-japan-edm` | 共享 Visual Router、既有 EDM Runtime、浏览器 QA | Project Visual DNA → EDM Adapter → Formula / Module → 600px HTML | 只继承视觉原则，不复制 Amazon 布局、密度、Claim 或价格；不发送 |
| `switchbot-japan-campaign` | 表格、文档、演示文稿及数据分析能力 | Campaign Context → 渠道 Brief / Tracking 草稿 / KPI 复盘 | 保留口径、Owner 和审批；不自动写飞书、创建短链或发布 |

具体使用某项能力时读取该环境提供的对应技能；此表不是依赖安装清单，也不承诺任何工具已经认证或具有写入权限。

`amazon-generic-mobile-preview` 仅作为可选预览适配器评估，不增加业务入口。使用前检查其说明所引用的 `scripts/scaffold_preview.mjs`、`scripts/verify_preview.mjs`、模板和当前任务所需参考文件是否真实存在。缺失时标记 `BLOCKED_RUNTIME_MISSING`，保留已有 Renderer 路线。制作本地审核页不包含公开部署授权；未发布产品资料不得因预览模块的默认行为而公开。需要公开链接时另行遵守当前任务的发布授权与托管审批。

## 两种安装环境不能混为一谈

| 环境 | 定位方式 | 检查命令 |
|---|---|---|
| 常规 Codex CLI 镜像 | `$CODEX_HOME/skills/<skill-name>` | `scripts/verify_codex_runtime.py` |
| 个人技能目录 | 平台分配的目录名，以 `SKILL.md` 的 `name` 识别 | `scripts/audit_personal_skill_mirrors.py` |

不要把常规镜像同步脚本的目标设为整个个人技能目录。不要复制、删除或重新命名平台分配的技能目录。

个人目录检查示例（将占位值替换为当前环境实际目录）：

```bash
python scripts/audit_personal_skill_mirrors.py \
  --workspace . \
  --personal-skills-root PATH_TO_PERSONAL_SKILLS
```

默认检查 Skill Lock 中四个 `user_visible: true` 入口，可用重复的 `--skill` 参数缩小范围。返回码 `0` 表示所选入口内容一致，`2` 表示缺失、停用、重复、内容差异、来源锁不一致或无法安全检查。

审计只读，不连接外部服务、不执行技能、不安装、不启用停用技能、不提交或发布。它逐文件比较正文、引用、脚本、测试和行为配置；只允许已知的个人目录产品列表及被 UI 元数据引用的图标差异。提示词、依赖声明和自动触发开关差异仍会报错。未声明的额外脚本不会被忽略。

`PERSONAL_ENTRIES_IN_SYNC` 只证明入口包一致。报告始终保留 `runtime_execution_verified: false`，不得将其解释成完整 Runtime、浏览器 QA、生产或发布就绪。

## 安全同步顺序

1. 读取最新 GitHub `main` 与 Skill Lock；确认源码对应已合并版本。常规本地同步仍要求 clean `main`。
2. 执行只读检查，按名称识别已安装入口。存在重复、停用、非预期的新内容或未提交用户改动时，先解决冲突，不强制覆盖。
3. 在个人技能环境中使用该环境的正式技能维护机制，逐个更新已确认入口。保留平台图标和原有行为设置，不从个人镜像反向覆盖仓库。
4. 每个入口运行技能格式验证及所带测试，保存后核实已保存内容，再做一次全量入口审计。没有保存成功，不报告已更新。
5. 新的仓库改动先经过独立分支、PR 和 CI；未合并改动不作为正式版本安装。产品事实、价格、Claim、Project Memory 与审批状态不在技能同步范围内。

内部 Runtime 继续从受控工作区解析。缺少 `project-context-resolver`、Visual Router、模板或外部 creative-flow 运行时时，只交付允许的分析、Brief 或 Review Package，说明阻塞；不要把所有内部模块盲目装成新的用户入口。

## 本轮基线

2026-09-07 检查源为 `main` 提交 `cf7c9996c86f44057a88006830422d30e7038c78`。四个已安装入口均落后于该版本：洞察和 Campaign 缺项目上下文预检；内容 Flow 缺 Project Visual Resolution 与引用文件；EDM 缺 Visual Pattern 衔接文件；Campaign/EDM 还缺已有契约测试。

这描述的是同步前检查，不是未来永久状态。以后以实时审计结果为准。既有 #1 产品导入审核、产品事实、项目 Gate、公开预览权限及所有发布状态保持独立。
