# Copy ↔ Visual Fidelity Contract

目的：保证文案、画面和证据表达同一件事。漂亮但无法支持主文案的图片不算合格电商视觉。

## 1. 核心原则

每个 Asset 必须区分：

- `message`：本资产唯一主信息；
- `copy_claim`：消费者实际看到的文字主张；
- `consumer_takeaway`：用户看完应记住什么；
- `visual_proof`：画面如何可见地支持主张；
- `render_role`：Scene / Product / Mechanism / Evidence 各自承担什么；
- `semantic_match`：文字与画面是否同义。

Render 不能只是“漂亮背景 + 产品 + 大字”。需要 Proof 的主张必须有可见 Proof。

## 2. Fidelity Packet

```yaml
message:
copy_claim:
consumer_takeaway:
visual_proof:
  proof_object:
  proof_action:
  proof_visibility:
copy_role:
  headline:
  support:
  native_text:
render_role:
  scene:
  product:
  mechanism:
  evidence:
semantic_match:
  copy_supported_by_visual:
  visual_introduces_new_claim:
  proof_visible_without_copy:
mobile:
  readable:
  proof_visible:
gate:
```

## 3. Gate

### PASS

满足：

- Copy 与 Visual 指向同一 Benefit / Mechanism；
- 需要 Proof 的信息在画面中可见；
- 画面没有引入未批准 Claim；
- 隐去文字后仍能大致理解关键 Benefit 或机制；
- Mobile 下关键 Proof 仍可见。

### WEAK

典型情况：

- 画面只是氛围或 Lifestyle，主要靠文字解释；
- Proof 存在但太小、太抽象或需要大量说明；
- Desktop 尚可，Mobile 缩小后 Proof 消失。

WEAK 可以作为品牌/情绪类资产存在，但如果资产角色本来是 Mechanism / Evidence，则必须返工。

### FAIL

任一情况：

- Copy 与 Visual 讲不同事情；
- 画面暗示新的未批准能力；
- 用装饰图冒充性能 Proof；
- 产品结构、尺度、物理关系不真实；
- 关键数字或 UI 由生成模型错误渲染；
- 比较画面与比较文案不对应。

FAIL 不得进入 Whole-set Approval。

## 4. Proof 类型

常见 Visual Proof：

### Scale Proof

例如产品小尺寸：使用门宽、椅脚、家具间距、实物比例或已验证尺寸标注。单纯把产品放在空客厅里不是 Scale Proof。

### Mechanism Proof

例如 Roller、清水/污水路径、结构机制：应能看到真实机制、剖面、接触关系或批准示意。普通拖地 Lifestyle 不能替代 Mechanism Proof。

### Performance Proof

例如吸力、续航、覆盖：需要批准的测试/数据或可验证 Evidence。尘土飞走的戏剧化画面不能单独证明具体数值。

### Automation Proof

展示真实流程、回站、维护、App/Station 行为。不可凭空生成不存在 UI 或工作步骤。

### Fit / Scenario Proof

用户、住宅和使用环境必须和 Copy 说的适配场景一致。

## 5. Copy Layer 与 Render Layer 分离

生产默认：

```text
Scene Layer
+ Official Product Layer
+ Graphic / Approved Copy Layer
```

AI Render 不负责：

- 日文消费者文案；
- 精确参数；
- 认证；
- 法律说明；
- 精确 UI；
- 品牌 Logo；
- 技术表格。

这些由程序化排版或真实批准素材完成。

## 6. Whole-set Review

必须输出：

| Asset | H1 / Claim | Consumer Takeaway | Visual Proof | Without Copy | New Claim? | Mobile Proof | Gate |
|---|---|---|---|---|---|---|---|
| | | | | Yes / Partial / No | Yes / No | Yes / Partial / No | PASS / WEAK / FAIL |

重点寻找：

- 多张图的 Copy 不同但画面其实重复；
- 画面很丰富但与主 Benefit 无关；
- 文案强调机制，但画面只展示 Lifestyle；
- H1 说尺寸，画面没有尺度参照；
- H1 说性能数字，画面只有夸张效果；
- Brand Copy 与 Product Copy 使用完全相同的画面语法。

## 7. Mobile Review

Mobile 不是只检查文字能否读到，还要检查 Proof：

- 尺度参照是否仍看得懂；
- 小型机制局部是否仍可辨识；
- 关键箭头/标签是否拥挤；
- 比较表是否转成可读堆叠/滑动策略；
- Brand Story 是否仍有品牌层级，而不是只剩产品大图。
