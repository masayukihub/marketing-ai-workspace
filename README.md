# Marketing AI Workspace

这是日本市场营销工作的长期 GitHub 工作空间，用来管理可复用的 AI Skills、Project Memory、自动化脚本、数据结构和可视化应用。

它不是飞书或正式产品资料的替代品。飞书与官方资料仍是 Source of Record；本仓库保存经过筛选、可版本管理的执行能力和项目上下文。

## 目录说明

| 目录 | 用途 |
| --- | --- |
| `skills/` | 可复用的营销 AI Skills、脚本、测试和规范 |
| `projects/` | 各营销项目的工作入口，不复制全部原始素材 |
| `memory/` | 项目记忆、产品记忆接口和决策日志 |
| `visual-system/` | 页面类 Skill 共用的 Visual Pattern Memory、Router、Registry 与 Channel Adapter；不作为用户入口 |
| `data/` | 可公开给团队版本管理的结构化数据；默认不放个人信息和原始密钥 |
| `automations/` | 监测与同步任务 |
| `apps/` | Dashboard、报告和内部工具 |
| `docs/` | 工作流、标准与架构说明 |
| `tests/` | 工作空间级验证脚本 |
| `.github/` | Actions、Issue 和 PR 模板 |

## 如何让 Codex 工作

项目型任务先由 `project-context-resolver` 读取轻量 Manifest，生成最小 Context Package，再进入执行 Skill。直接说明项目、目标、来源、期望输出和允许的修改范围。例如：

```text
解析 S30 mini 项目后，只读取 Amazon 所需 Context，
在 feature/s30-pdp 分支更新 Amazon PDP 流程；不要修改产品事实，完成后运行测试。
```

Codex 必须先读取根目录 `AGENTS.md`，再解析 `projects/<project-id>/project.yaml`。Manifest 只负责导航、Freshness、当前 Gate、Blocker 和 Next Action；Product Truth 与 Project Memory 仍由原有系统负责。Manifest 当天修改不代表项目状态当天确认；`freshness_status_at_manifest_update` 只是维护时快照，运行时状态以 Resolver 生成的 `effective_freshness_status` 为准。

仓库内 `skills/` 是正式运行来源，`runtime/skill-lock.json` 锁定关键 Runtime。`$CODEX_HOME/skills/` 只作为安装镜像；检查全部锁定 Skill 时运行：

```bash
python3 scripts/verify_codex_runtime.py
python3 scripts/sync_codex_skill_mirror.py --dry-run
```

出现 `RUNTIME_DRIFT`、`MIRROR_MISSING` 或 `REPOSITORY_RUNTIME_MISSING` 时不得执行全局镜像。实际同步只允许从 clean `main` 单向写入 Global Mirror。

ChatGPT 项目读取规则见 `chatgpt/PROJECT_INSTRUCTIONS.md`。`projects/*/chatgpt-context.md` 是可重复生成的阅读快照，不是 Product Truth、Decision 或 Approval。

## 新增 Project

1. 从 `memory/project-memory/_template/` 复制一个目录。
2. 命名使用小写英文和连字符，例如 `hub-3-jp`。
3. 填写 `PROJECT.md`、`STATUS.md`、`DECISIONS.md`、`SOURCES.md` 和 `TODO.md`。
4. 在 `projects/<project-id>/project.yaml` 建立轻量 Manifest，分别记录 Manifest 更新时间、状态验证日期和维护时 Freshness，并通过 Resolver 动态计算有效 Freshness。
5. 未确认内容标记 `UNKNOWN` 或 `NEED_CONFIRMATION`，对应 Source 指针用 `null`。
6. 在 `projects/<project-id>/README.md` 保留人类可读入口。

## 更新 Skill

1. 创建 `feature/xxx` 或 `fix/xxx` 分支。
2. 修改 `skills/<skill>/`。
3. 更新 Skill 自带的测试与版本记录。
4. 运行 `python3 tests/validate_workspace.py` 和对应 Skill 测试。
5. 测试通过后提交 Pull Request。

## 提交修改

```bash
git switch -c feature/short-description
git add <明确的文件>
git commit -m "skill: update amazon PDP adapter"
git push -u origin feature/short-description
```

推荐前缀：`feat:`、`fix:`、`docs:`、`data:`、`skill:`、`test:`、`refactor:`。

## 回退版本

优先使用可追溯的反向提交：

```bash
git log --oneline
git revert <commit-id>
```

不要对共享的 `main` 使用 `git reset --hard` 或强制推送。

## 绝对不能上传

- `.env`、`.env.local` 和真实环境变量
- API Key、Access Token、Refresh Token、Cookie、密码
- `credentials.json`、`token.json`、私钥、证书私钥
- 用户个人信息、KOL 私人联系方式、未授权客户数据
- 浏览器 Profile、Keychain 导出、登录 Session
- 未获授权的大体积原始图片、视频、邮件正文和飞书导出备份

占位配置只能写入 `.env.example`，且值必须为空或使用 `YOUR_..._HERE`。

## 分支规则

- `main`：稳定版本
- `feature/xxx`：新增能力
- `fix/xxx`：问题修复
- `experiment/xxx`：实验，不应直接合并

测试失败时不得合并或覆盖 `main`。

首次 clone 后运行：

```bash
bash scripts/setup_local_git.sh
```

它会启用本地 `pre-push` 检查并阻止直接推送 `main`。当前 Private Repository 所属的 GitHub 方案不支持服务端 Branch Protection，因此 Pull Request 和通过 Actions 是必须遵守的团队规则。
