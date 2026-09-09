# 可移植历史适配器输入

私有输入与输出放在仓库外。模板是从实际查看的历史区域提炼的候选；候选身份和当前发送批准相互独立。

`brief.json`：

```json
{"campaign_type":"sale_launch","stage":"launch","channel":"amazon","product_count":4,"preferred_recipe":"autumn-sale-open-v1","explicit_new_design":false}
```

当前版式：`autumn-sale-open-v1`、`pd-sale-open-v1`（2–6 SKU 开售），`category-security-v1`（2–6 SKU 专题，阶段为 `mid_campaign` / `reminder`），`product-reveal-v1`（1 SKU 新品）。未知任务不能静默套用。项目已有批准的视觉方向时，先保持该决定的范围，不能用此候选库覆盖冻结结果。

`evidence.json` 为每个相关历史样本记录：

```json
{"samples":[{"reference_id":"SB-AUTUMN-2025-AMAZON-OPEN","delivery_status":"marketing_received_copy","html_read":true,"visual_reviewed":true,"visual_files":["/private/reference-hero.png","/private/reference-card.png"]}]}
```

这些 true 必须来自真实读取和查看。只查看 Hero 时，后续分析不能称已查看全封邮件；`visual_files` 只列实际看过的区域。相对路径按 evidence 文件目录解析。原始 Gmail 索引、题名、日期和查看范围留在私有证据中；plan 仅携带稳定 reference ID 和图片 hash。正式副本为 `marketing_received_copy`，确认该邮箱已发的营销邮件才为 `sent_marketing`；测试、重复、合作沟通均不得充当主要视觉来源。

`render-input.json` 的必需字段：

| 字段 | 说明 |
|---|---|
| `subject` / `preheader` | 当前日文件名与预览文字；不能保留历史占位词 |
| `campaign_name` / `hero_title` / `main_cta` | 当前活动名、Hero 文案、主行动 |
| `logo` | 本地官方 Logo；PNG/JPEG/GIF |
| `products[]` | 当前不同产品，顺序来自本次商业角色 |
| 每个产品 `id` / `asset_product_id` | 两者必须相同，不能错绑官方图 |
| `name` / `benefit` | 当前正式产品名与一个主要利益 |
| `image` / `image_source` / `product_source` | 本地官方图和当前来源 HTTPS URL |

可选：`background`（仅环境层）、`font_file`、`period_text`、`main_url`、`preferences_url`、`unsubscribe_url`；商品 `note`、`label`、`url`、`image_url`。缺少 URL 时发送 HTML 保留待配置 token。促销日期仍由当前活动材料确认；内部输入中的日期不代表正式批准。

上述本地素材和字体支持绝对路径或相对路径；CLI 的相对路径按 `render-input.json` 所在目录解析，不依赖当前命令目录。

价格只有 `offer.status: CONFIRMED`、存在 `offer.source` 且 `sale_price_jpy` 为非负整数时才展示；`reference_price_jpy` 如提供，不能低于现价。这些字段是当前来源核对后的输入，不能自动从历史图片提取；未知价格省略数字，保留查价行动。当前版本不自动计算或展示百分比、券和赠品，避免把比较价来源误当折扣批准。

`product-reveal-v1` 可带 `details[]`，每项含 `title`、`body`、`source`、`status: CONFIRMED`；无证据的细节不渲染。缺图或超出支持范围会返回具体阻塞，不能用另一产品或生成假产品填充。

输出包括 `email.html`（发送结构草稿）、`email-preview.html`、`review.html`、`copy-ja.md`、`plan.json`、`inheritance-map.json`、`asset-manifest.json`、`qa-report.json`；离线依赖就绪时输出 600/390 参考长图。`status` 保持 `INTERNAL_DRAFT`，适配器不能通过输入自报浏览器 PASS 或内容批准；不执行 ESP 发送。
