# Customer Review Intelligence

项目级 SwitchBot 日本 VOC Skill。Skill 代码位于本目录；长期数据库位于：

`/Users/lai/Documents/marketing/customer-review-intelligence`

标准入口：

```bash
/Users/lai/Documents/marketing/customer-review-intelligence/.venv/bin/python scripts/run_standard_workflow.py \
  --workspace /Users/lai/Documents/marketing/customer-review-intelligence/products/ai-art-canvas \
  --config-dir /Users/lai/Documents/marketing/customer-review-intelligence/config \
  --product-knowledge-dir /Users/lai/.codex/skills/product-knowledge \
  --mode full --initial-full \
  --build-business --build-dashboard-v2 --export-miaoda
```

后续运行将默认增量追加，不覆盖历史。网页受登录、验证码、反爬或结构变化影响时，运行结果会标记为 `Partial` 或 `Blocked`，不会把缺失解释为零条评论。

常用参数：

- `--products lock_ultra,hub_3`
- `--modules ec,sns,kol,pr,official,competitor`
- `--date-from YYYY-MM-DD --date-to YYYY-MM-DD`
- `--input <csv-or-json>`
- `--analyze-only`
- `--output-dir <path>`

长期状态写入 `state/last_success.json`；双周报告位于 `reports/biweekly/latest.md`，本地 Dashboard 位于 `outputs/latest_review_summary.html`。

## 飞书妙搭

`--export-miaoda` 会在产品工作区生成 `miaoda_bundle/`，包含审核后的评论、问题、产品 Backlog、营销洞察、数据字典、妙搭兼容数据库迁移和只读 Dashboard。该动作只生成本地交接包，不会自动创建或发布线上应用。

- 只读看板可使用妙搭 `html` 应用。
- 需要负责人、状态、截止日、提醒和多人协作时使用 `full_stack` 应用。
- 新建应用前需明确选择“本地代码开发”或“妙搭 AI 云端生成”。

## 飞书多维表格运营层

当团队需要人工审核与渠道分工时，使用一个 Base 内的 7 个渠道分表（Amazon Japan、楽天、Yahoo、官网、YouTube、X、媒体）和 1 个统一汇总表。原始日文正文、来源 ID、URL、快照和批次属于只读证据；人工状态、备注、负责人、优先级、复核时间和修正说明可维护。初次复制不等于持续同步，未建立并验证同步链路前必须标记 `initial_copy_only` 或 `not_synced`。

产品改善、营销应用、问题中心和用户原声均应展示可追溯的日文原文。每条建议关联真实 `review_id`、原始链接、分子/分母和置信度；无证据时显示“证据不足”。词云只作为二级发现工具，基于原文按 distinct review_id 计数，并可下钻至命中原声。

## 受限渠道补全

公开浏览器不能证明分页完整时，使用官方 API：

```bash
python scripts/collect_api_channels.py youtube \
  --videos-json /path/to/youtube/pages.json \
  --raw-dir /path/to/raw/youtube-comments/BATCH \
  --resume-state /path/to/state/youtube-comments.json \
  --output /path/to/imports/youtube-comments.json

python scripts/collect_api_channels.py x \
  --query '("SwitchBot AIアートキャンバス" OR "AI Art Canvas" OR "AI Art Frame") lang:ja -is:retweet' \
  --raw-dir /path/to/raw/x-api/BATCH \
  --resume-state /path/to/state/x-api.json \
  --output /path/to/imports/x-posts.json
```

YouTube 读取 `YOUTUBE_API_KEY`；X 读取 `X_BEARER_TOKEN`。密钥不会写入快照。
Amazon 没有公开的完整评论 API；使用
`customer-review-intelligence/config/amazon_review_import_template.csv` 导入授权证据，
或在用户明确授权后执行受控登录态采集。

## 浏览器截图采集

用户明确授权外部浏览器后，Amazon、X、YouTube 可使用已有浏览器页面进行采集：

- 每个分页或滚动边界保存 PNG 截图和可见 DOM 文本；
- 保存 URL、排序方式、首尾内容 ID/日期、滚动序号和加载前后数量；
- 连续三次无新增，或遇到验证码、限流、登录提示时停止并保存续跑位置；
- 使用 `scripts/validate_browser_capture.py` 校验文件哈希、ID 对账和 Complete 条件；
- X 浏览器搜索始终为 `Partial`；YouTube/Amazon 只有在固定范围全部展开并完成数量对账后才能为 `Complete`。

配置和 Manifest 模板位于：

- `customer-review-intelligence/config/browser_capture.yaml`
- `customer-review-intelligence/config/browser_capture_manifest_template.json`
