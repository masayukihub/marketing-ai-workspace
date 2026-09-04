# SwitchBot Japan AI 视觉生产手册

这份手册用于 Amazon 卖点图、EDM、社媒图、Banner、KV、Landing Page 和视频视觉。目标是兼顾生成效率、品牌一致性和产品准确性。

## 1. 最优生产模式

推荐采用：

```text
结构自动化
+ 视觉半自动
+ 最终人工收口
```

不要追求“一句话直接生成全部 Final”。系统应该追求“一次生成可进入 Review 的完整候选包”。

标准链路：

```text
Product Truth / Campaign Context
→ Selling Point / Storyline
→ Brief
→ Page Visual System
→ Anchor Candidate
→ Human Direction Review（仅在没有有效继承时）
→ One-asset Production
→ Whole-set Review
→ Hardening / Mobile QA
```

## 2. 三层视觉结构

所有正式视觉拆成三层：

```text
Scene Layer
+ Product Layer
+ Graphic / Copy Layer
```

### Scene Layer

可以使用 AI 生成：

- 日本家庭、客厅、玄关、厨房、宠物空间；
- 人物、道具、光线、天气和氛围；
- 不包含正式产品细节的抽象机制背景；
- 不承担精确事实证明的生活场景。

### Product Layer

必须使用官方或批准素材：

- 产品本体；
- Logo；
- App UI；
- 包装；
- 配件；
- 安装关系；
- 产品组合和颜色；
- 需要精确展示的按钮、接口和屏幕。

AI 不得重绘、补画、猜测或改变正式产品几何、颜色、材质、标签和接口。

### Graphic / Copy Layer

使用程序化排版、Figma、Canva、HTML/CSS 或设计工具完成：

- 日文标题；
- 参数和技术标注；
- 图标；
- 比较表；
- CTA；
- Legal；
- Logo 和品牌组件。

不要让图片模型直接生成最终日文文字或精确参数表。

## 3. 什么时候需要 Anchor

以下情况先出 1–2 张代表图：

- 没有有效 Visual Freeze；
- 没有 Accepted Project Visual Planning Decision；
- 新的产品类型或新渠道；
- Visual Router Top 1 / Top 2 过近；
- 品牌适配度不足；
- 官方素材状态不稳定；
- 用户明确要求探索新方向。

如果已有有效批准方向，默认继承，不重新询问。

推荐 Anchor：

1. Hero / Impact；
2. 核心功能 / Mechanism 或 Proof。

Anchor Review 只确认：

- 品牌气质；
- 产品比例和位置；
- 信息密度；
- 日系场景真实性；
- 图文关系；
- 是否能够扩展整套。

## 4. Visual Pattern 继承

项目优先级：

```text
Approved Visual Freeze
→ Accepted Project Visual Planning Decision
→ Valid Visual Profile
→ Visual Router
→ Limited Human Direction Review
```

视觉系统只决定 Pattern、节奏、构图族和渠道映射，不得修改 Product Truth 或 Claim。

同一个项目跨 Amazon、EDM、LP 和 Campaign Visual 时继承 Project Visual DNA，但每个渠道独立决定：

- 信息密度；
- Product Scale；
- Scene / Composition Family；
- Copy Length；
- CTA；
- Mobile Behavior。

## 5. Amazon 卖点图

统一入口：`$jp-commerce-content-flow`

### 推荐节奏

```text
Impact
→ Consumer Problem
→ Product Solution
→ Mechanism / Proof
→ Scenario / Fit
→ Detail / Compare
→ Closure
```

不是每个项目都必须使用全部角色，也不能机械地一个 Feature 对应一张图。

每张图必须回答一个问题：

```text
这是什么？
为什么需要？
为什么它更好？
为什么可信？
是否适合我？
```

### Evidence Mode

- `SOURCE_FAITHFUL`：主图、Packshot、套装、包装；
- `CREATIVE_MOCK`：生活方式、空间和氛围；
- `PROOF_VISUAL`：尺寸、安装、UI、机制、兼容性和比较。

## 6. EDM 视觉

统一入口：`$switchbot-japan-edm`

默认：

- 600px 响应式；
- Hero 在数秒内说明活动、利益、时间和动作；
- 主产品大卡，次级产品规律网格；
- 产品卡只保留一个主要利益点；
- 模块内部聚合、模块之间留白；
- 320、375、390、414 和 768px 检查；
- 历史 Formula / Template 优先，但不继承旧事实。

轻微的文案去重、换行、间距和 Mobile 修复，可以使用 `MINOR_REVISION_AUTO_APPROVE_IF_QA_PASS`。

## 7. 社媒图、Banner 和 KV

先确定母版，再做渠道改版：

```text
Master Art Direction
→ X
→ Instagram
→ LINE
→ PR TIMES
→ Website / Pop-up
```

不同尺寸不应只做机械裁切。每个 Placement 重新检查：

- 首屏焦点；
- Safe Area；
- 产品比例；
- 文案长度；
- CTA；
- 移动端识别；
- 是否需要 Copy-free 版本。

## 8. AI 视频

产品外观精度是第一 Gate。

标准步骤：

```text
官方产品参考
→ 5–10 秒 Fidelity Demo
→ 产品交互检查
→ 镜头语言确认
→ 扩展完整脚本和镜头
→ 连续性 QA
```

对 Lock、Doorbell、ハブ等结构精确产品：

- 门内侧与门外侧产品不能混用；
- 位置、安装方向、钥匙孔和配件关系必须准确；
- AI 生成主要用于日系环境、人物、光线和过渡；
- 产品本体优先使用实拍、3D Render、抠图合成或受控参考编辑。

## 9. 图片生成提示词结构

Scene Layer Prompt 至少包含：

```text
Visual Objective
Japanese Consumer Context
Room / Location
Time / Lighting
Camera / Composition
Negative Space
Human / Prop Behavior
Mood
What Must Not Appear
Output Aspect Ratio
```

不要把 Product Claim、技术参数、Logo 和最终日文 Copy 塞进场景生成 Prompt。

### 负面约束

```text
no brand logo
no product recreation
no fake UI
no Japanese text
no technical labels
no extra accessories
no distorted architecture
no excessive luxury styling
no cyberpunk
no Chinese marketplace visual density
```

## 10. 产品层合成检查

每张正式候选检查：

- 产品外形和比例；
- 颜色和材质；
- 按钮、接口、屏幕和标签；
- 安装方向；
- 配件数量；
- 光影和透视是否与场景一致；
- 产品边缘和接触阴影；
- 是否产生模型自造部件；
- 是否跨 Variant / Bundle / Offer；
- 是否有素材授权。

任一关键错误标记：

```text
PRODUCT_FIDELITY_FAIL
```

不能进入 Final。

## 11. 整套图 QA

单张好看不等于整套成立。Whole-set Review 至少检查：

- 购买决策顺序；
- Primary Message 是否重复；
- Scene Family 是否连续重复；
- Composition Family 是否连续重复；
- 明暗和节奏；
- 产品大小变化；
- Proof / Lifestyle 的比例；
- Gallery 与 A+ 重复；
- 日语自然度；
- Mobile 阅读；
- 资产集合是否完整。

局部问题默认只重开最小必要 Asset ID。

## 12. 自动化边界

### 默认自动

- Visual Context 解析；
- 继承有效视觉决定；
- Pattern / Channel Adapter 选择；
- Scene Layer Prompt；
- Brief、Asset Packet 和 Contact Sheet；
- 文案去重、长度、换行和排版修复；
- Desktop / Mobile / Browser QA；
- 文件 Hash、来源和 Run Manifest。

### 必须人审

- 新 Visual DNA 或新主方向；
- 产品本体和精确 UI；
- Product / Offer / Claim；
- 最终候选和 Whole-set；
- Visual Freeze；
- 外部发布。

## 13. 输出状态

```text
WIREFRAME
CREATIVE_DIRECTION_CANDIDATE
VISUAL_DELIVERABLE_CANDIDATE
USER_SELECTED
WHOLE_SET_REVIEW_READY
HARDENED_CANDIDATE
FINAL_HUMAN_APPROVED
PUBLISH_READY
```

状态不可跳级。`VISUAL_DELIVERABLE_CANDIDATE` 和 QA PASS 都不等于 `PUBLISH_READY`。

## 14. 直接复制的产品卖点图指令

```text
使用 $jp-commerce-content-flow，读取最新 GitHub main 并解析【项目】。
基于已确认 Product Truth、Insight Pack、官方产品素材和有效视觉决定，制作【渠道/范围】的产品卖点图。

要求：
1. 一张图只回答一个消费者问题；
2. 有有效 Visual Freeze / Planning Decision 时直接继承，不重新问方向；
3. 正式产品本体、Logo、UI、配件和文字不得由图片模型重画；
4. AI 只生成 Scene Layer，Graphic/Copy Layer 程序化排版；
5. 先生成必要 Anchor，批准后逐张制作；已批准方向则直接进入逐张制作；
6. 自动完成两轮以内的安全修复和 Desktop/Mobile QA；
7. 只在 Product/Offer/Claim、主方向、精确最终资产或发布时停下；
8. 最终输出 Contact Sheet、Standalone Review HTML、QA、Blocker 和 Run Manifest。
```

## 15. Figma / Canva / HTML 收口

最终收口选择：

- **Figma**：复杂页面、严格栅格、组件复用和设计协作；
- **Canva**：快速社媒改版和非复杂模板；
- **HTML/CSS**：EDM、Review Demo、响应式检查和批量可复现；
- **实拍/3D**：产品 Fidelity 要求高、AI难以稳定保持外观时。

AI 最适合完成研究、策略、Brief、场景、候选和 QA；正式商业视觉通常仍需要精确合成与人工收口。
