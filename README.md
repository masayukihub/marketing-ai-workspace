# Marketing AI Workspace

这是 SWITCHBOT 日本市场营销工作的长期 GitHub 工作空间，用来管理可复用的 AI Skills、Project Memory、自动化脚本、数据结构和可视化应用。

它不是飞书或正式产品资料的替代品。飞书与官方资料仍是 Source of Record；本仓库保存经过筛选、可版本管理的执行能力和项目上下文。

## 目录说明

| 目录 | 用途 |
| --- | --- |
| `skills/` | 可复用的营销 AI Skills、脚本、测试和规范 |
| `projects/` | 各营销项目的工作入口，不复制全部原始素材 |
| `memory/` | 项目记忆、产品记忆接口和决策日志 |
| `data/` | 可公开给团队版本管理的结构化数据；默认不放个人信息和原始密钥 |
| `automations/` | 监测与同步任务 |
| `apps/` | Dashboard、报告和内部工具 |
| `docs/` | 工作流、标准与架构说明 |
| `tests/` | 工作空间级验证脚本 |
| `.github/` | Actions、Issue 和 PR 模板 |

## 如何让 Codex 工作

直接说明项目、目标、来源、期望输出和允许的修改范围。例如：

```text
读取 memory/project-memory/s30-mini 后，检查对应 Skill，
在 feature/s30-pdp 分支更新 Amazon PDP 流程；不要修改产品事实，完成后运行测试。
```

Codex 必须先读取根目录 `AGENTS.md`，再读取项目的 Project Memory。

## 新增 Project

1. 从 `memory/project-memory/_template/` 复制一个目录。
2. 命名使用小写英文和连字符，例如 `hub-3-jp`。
3. 填写 `PROJECT.md`、`STATUS.md`、`DECISIONS.md`、`SOURCES.md` 和 `TODO.md`。
4. 未确认内容标记 `UNKNOWN` 或 `NEED_CONFIRMATION`。
5. 在 `projects/<project>/README.md` 建立工作入口。

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
