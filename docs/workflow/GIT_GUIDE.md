# 简单 Git 使用规范

## 日常小修改

在非 `main` 分支修改并提交：

```bash
git switch -c docs/update-readme
git add README.md
git commit -m "docs: update workspace guide"
git push -u origin docs/update-readme
```

## Commit 类型

| 前缀 | 用途 |
| --- | --- |
| `feat:` | 新增工作空间能力 |
| `fix:` | 修复错误 |
| `docs:` | 文档与 Project Memory |
| `data:` | 数据更新 |
| `skill:` | Skill 更新 |
| `test:` | 测试更新 |
| `refactor:` | 不改变功能的结构调整 |

## 回退

使用 `git revert <commit-id>` 创建反向提交。不要强制推送 `main`。
