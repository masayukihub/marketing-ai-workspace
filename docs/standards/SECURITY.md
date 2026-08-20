# Security Standard

- 仓库保持 Private 不能代替 Secret 管理。
- Secret 只存本机 Keychain、GitHub Actions Secrets 或获批准的 Secret Manager。
- `.env.example` 只放变量名称和占位符。
- KOL 联系方式、用户评论原始身份信息、邮件正文和浏览器 Session 默认不进入仓库。
- 提交前运行 `python3 tests/validate_workspace.py`。
- 若 Secret 曾被提交，删除文件不等于安全；必须立即轮换凭证并清理 Git 历史。
