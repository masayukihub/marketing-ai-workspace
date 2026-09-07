# 交付与验收契约

## PLAN_ONLY

- Product Truth Packet；
- Creative Strategy Kernel；
- Gallery/A+故事与信息架构；
- 完整Asset Set；
- Page Visual System；
- Evidence Mode；
- Production Handoff；
- 中文Review摘要与待确认项。

## CREATIVE_EXPLORE

- 按用户指定数量输出方向；未指定时先给一个推荐方向，有实质分歧时再加一个对照；
- 仅在用户要求9宫格/广泛探索时展开9或10个方向，并按需要推荐Top 3；
- 每个方向的主信息、构图、Proof、风险；
- 用户选择后的一份可执行单张Brief。

## PRODUCE / MVP / FULL_FLOW

- 当前范围每个Asset ID的候选、选择和状态；
- 最终日文文案；
- Gallery与A+资产；
- Whole-set Contact Sheet / Content Review；
- 素材来源和授权状态；
- 未解决的Claim与证据缺口。

每张候选还需：当前 Shot Brief、实际制作方式/工具、输入素材与输出文件、成图观察、局部修改记录。字段校验通过只说明 Brief 可交接；不能写成“已出图”或“审美通过”。

## HARDEN

- 精确最终文件清单与SHA-256；
- Asset-to-Slot核对；
- 页面与交付状态；
- 单文件Content Review HTML；
- Desktop与390px Mobile验证结果；
- broken image、overflow、missing content、console error结果；
- Publish/Delivery结论和限制。

## 状态词

- `READY_FOR_REVIEW`：可供人工审阅，不代表批准。
- `USER_APPROVED`：创意被接受，不代表文件证据与发布条件已满足。
- `PARTIAL_BUT_ACTIONABLE`：可继续部分工作，正式执行仍有限制。
- `BLOCKED`：缺少关键事实、Claim、素材、权限或运行时。
- `DELIVERY_READY`：当前约定范围的事实、创意、文件和QA均完成。

## 禁止虚假完成

- 未生成真实图片，不得用占位框说“视觉稿完成”。
- 未运行浏览器，不得说“移动端QA通过”。
- 未核对官方素材与授权，不得说“可正式发布”。
- 未确认价格、促销、评价数或库存时显示 `—` / `待确认`，不得使用Fixture值。
