# A+ / EBC 生产交接与防漏契约

适用于用户直接调用旧 `amazon-listing-creative`，但实际要求完整页面或 A+/EBC 成片的情况。它补充主入口的 output-contract；不建立第二套生产系统，不改变 Product Truth、人工审批或 Publish Gate。

## 1. 先保留完整任务范围

将下面内容一起交给 `$jp-commerce-content-flow`，不能只转交一个 Skill 名称：

- scope：full / gallery / aplus；intent：create / plan / resume / revise；
- required_outputs：full 必须同时含 gallery、aplus；aplus-only 不新增或重画 Gallery；
- 当前 Product/SKU/渠道、正式 Context Package 与冻结 Spec/Handoff 路径；
- 已批准的 Gallery 精确文件与哈希、现有 A+ 模块/内容单元/轮播页 ID；
- 当前 Brand Story / Series Comparison / FAQ 是否属于本次范围；
- 本轮缺失产物清单、可继承的批准、下一 Material Human Gate；
- 本契约及旧模板/实际运行时适配状态。

`CREATIVE_EXPLORE` 只用于用户明确要求概念发散。不要因为调用了旧名，就把“做 EBC”变成“一张 EBC 的九个点子”。原 mode-contracts/output-templates 中的九宫格继续用于创意子任务，不定义完整交付。

## 2. 模块、内容单元、轮播页、品牌、比较和文件必须分清

| 层级 | 含义 | 必须核对 |
|---|---|---|
| Gallery | 商品图库 | 每个已批准 Asset ID 的实际图片 |
| A+ Module | 页面中的模块容器 | 顺序、类型、内容单元和真实预览组件 |
| Content Unit | 模块内的一项内容 | 主信息、文案、条件、素材绑定 |
| Carousel Slide | 轮播中一页 | 每页单独素材与移动策略；不能只做第一屏 |
| Native Field | 平台原生文字/表格 | 文本字段、组件绑定和手机端实际呈现 |
| Brand Story | 品牌主张、产品哲学、生态/信任 | 与 Product Story 分层、来源、Cross-sell、品牌视觉 |
| Series Comparison | 同品牌产品/Variant 选型 | 推荐人群、适用场景、差异、来源、Publishability |
| Internal Competitor Matrix | 内部定位/竞品研究 | `INTERNAL_ONLY`，不得直接作为 Amazon 发布资产 |
| Raster Asset | 实际 JPG/PNG/WebP | 文件、可解码性、分辨率、来源、审批状态 |

一个模块不一定等于一张图片；16 个内容单元也不一定是16张横幅。数量从已批准的 Spec/Handoff 推导，禁止固定要求 7 Modules/16 Units 或把 Gallery 正方形简单拉成长横幅。

## 3. 独立完成 A+ 规划与制作

Gallery 负责快速购买判断；A+ 应进一步解释机制、使用场景、适配边界、维护/拥有体验和选择帮助。允许复用已批准 Product Layer，但不能仅复用 Gallery 成片当作 A+ 制作。

完整页面在图片生产前还必须建立：

```text
Why This Product Exists
→ Page Story Spine
→ Gallery / A+ 分工
→ Brand Story
→ Series Comparison
→ FAQ / Objection Handling
```

每个模块交接：ID、所属 SKU、消费者问题、Story Role、模块类型、内容单元、文案/条件、Product/Scene/Graphic Layer、桌面/移动呈现、所需文件、生产状态。轮播必须展开全部 Slide ID；Native 文字保持独立，不把长文案烘焙到图片里。

Brand Story 交接至少包含：Brand Promise、Product Philosophy、Why This Product Fits Brand、Ecosystem/Trust、Cross-sell、正式 Source 与禁止 Claim。

Series Comparison 交接至少包含：Comparison Mode、每个产品的 Product ID/Brand/Source/Status、Recommended For、Usage Fit、Key Differentiator 与 Publishability。竞争品牌表默认只供内部 Strategy Review；不得静默进入正式 A+。

先确认当前日本站账户可用的 Basic/Premium 模块及实际尺寸。参考页面出现某个模块，不代表本账户具有该模块。1464×600 只是本次部分参考资产中观察到的尺寸，不是所有 A+ 的统一规格。能力未核实时可以做明确标记的结构方案，但不能声称 Amazon-ready；也不能静默换掉已批准模块集合。

## 4. Copy ↔ Visual Fidelity 必须进入 Handoff

每个需要视觉证明的 Asset/Content Unit 都必须保存：

```text
Copy Claim
Consumer Takeaway
Visual Proof
Proof Object / Action / Visibility
Proof Visible Without Copy
Visual Introduces New Claim
Mobile Proof Visible
Gate = PASS / WEAK / FAIL
```

规则：

- 机制/证据型 Asset 若为 `WEAK`，不得直接按正式 Proof 交付；
- `FAIL` 必须返工；
- 画面新增未批准 Claim 必须 Block；
- H1 说尺寸时必须有尺度 Proof；
- H1 说机制时不能只用普通 Lifestyle；
- AI 生成文字、精确参数或 UI 不能成为正式 Evidence。

## 5. 使用现有运行时，不凭空造执行器

遵守主入口 runtime-contract 和 repository runtime verification。实际生产由正式 Planning/Production/Hardening 运行时负责；旧 `amazon-japan-pdp-generator` 仅在契约适配后作为兼容 Renderer。

兼容 Renderer 中可核对：

- `scripts/render_v4.mjs` 的 `renderFromSpec`；
- `product_images[].outputs.jpeg`；
- `aplus_modules[].outputs.jpeg`；
- 旧版静态模块移动图：`design/aplus/mobile/aplus_XX.jpg`（XX 来自 sequence）。

这些是已读到的代码路径，不保证用户当前安装版本或上游 fork 使用同一契约。记录实际入口、commit、解释器/依赖、输入 Spec 和原始日志。没有 Runtime 时明确报 `BLOCKED_RUNTIME_MISSING`，不能以 Prompt 或空 HTML 代替成片。

不要把“生成器里有函数”当作“该函数本轮已调用”。不要用 `--force` 越过现有事实、Story、Layout 或精确资产批准。

## 6. 生产必须可恢复，不能做完套图就停

在现有 Asset Ledger/Run Manifest 中分别记录 Gallery、A+ 模块、Slide、Mobile、Brand Story、Series Comparison 和 Native Copy 的进度，按实际成功文件更新，不等整批完成后才知道 EBC 是否存在。采用该 Runtime 已支持的局部生产接口，不发明不存在的 CLI 参数。

渲染中断时保留原始错误，并在错误处理/收尾步骤运行下方只读审计。说明最后成功的 Asset ID、失败的模块/文件/函数、恢复入口。完整范围仍是原范围；Gallery 完成不意味着 FULL_FLOW 完成。

“继续 EBC”时只处理缺失/失败且允许执行的 A+ 项，不重做已锁定 Gallery。若修改了文件，不能继承旧文件的精确批准。不能把脚本返回的 resume_queue 当作审批。

## 7. 只读文件覆盖检查

在 Skill 目录运行（Python 3.9+；图像检查使用现有、已验证的 Pillow 环境）：

```bash
python3 scripts/aplus_delivery.py route --scope full --intent create
python3 scripts/aplus_delivery.py route --scope aplus --intent resume
python3 scripts/aplus_delivery.py audit --scope full \
  --spec /absolute/project/spec/PRODUCT_PAGE_SPEC.json \
  --output-dir /absolute/project
```

退出码：0 = 文件/字段覆盖完整；1 = 有缺失或无效产物；2 = 输入/运行环境错误。没有 Pillow 时图像不会被记为已验证。它不访问网络、不生成图、不写 Spec、不授予发布权限。

支持既有 `product_images` 与 `aplus_modules`。静态模块复用现有 `outputs` 与 sequence；如实际运行时已使用 `outputs.mobile_jpeg/mobile_png/mobile_webp`，优先使用显式路径。

轮播输出检查使用模块的 `slides[]`，每页含稳定 `id` 与 `outputs` 的 desktop/mobile 路径。只要声明 carousel 却没有 Slide 映射，就返回 `CAROUSEL_SLIDES_UNMAPPED`，不能把一个 module JPG 算成完整轮播。

原生文字/表格检查使用显式 `delivery_kind: native`、非空 `native_content` 和 `preview_binding`。这些只代表结构化输入存在，不证明已渲染。Brand Story / Series Comparison 如果实际 Runtime 使用独立结构，也必须有明确 preview binding；不能因为文字字段存在就声称页面已挂载。

若正式运行时字段名不同，在 Review 目录生成可追溯到原 Spec 哈希的只读审计投影；禁止修改冻结 Spec 去迁就检查器，禁止省略未映射模块。未知模块应报告适配缺口。

**ARTIFACTS_PRESENT 绝不等于 DELIVERY_READY。** 该检查不验证产品真实性、Placeholder 来源、文案批准、渠道尺寸、预览挂载、浏览器或 Seller Central。必须继续运行已有安全、内容和浏览器 QA。

## 8. 预览与实图都要交付

A+ 完成至少有五种证据：

1. 已批准范围内的实际图片/轮播页文件及独立移动产物或经验证的原生响应式策略；
2. 对应 Native Copy、条件、替代文本和组件映射；
3. Brand Story / Series Comparison 若属于范围，已装配到 Review 页面并有来源与 Publishability 状态；
4. 已装配到已有 Amazon Fidelity/Review 页面，而非孤立图片目录；
5. 实际浏览器验证桌面、390px、每个轮播页、Brand/Comparison 和必需文字；本地预览不能冒充 Seller Central 最终验证。

HTML 不存在、A+ 未挂载、只显示第一张 Slide、Brand Story 缺失、Comparison 仍是内部竞品表或手机端漏文案时，分别报告问题，不得用“图片文件存在”覆盖。

只允许通过获准的本地预览方式运行浏览器；不要绕过安全限制。工具无法访问时标记 Browser QA 未完成。

## 9. 完成与发布分开报告

输出一份简短进度：Gallery 文件 x/y；A+ 模块 x/y；Slide x/y；Mobile x/y；Native Copy；Brand Story；Series Comparison；Copy-Visual Fidelity；Preview 挂载状态；实际 Browser QA；Publish Gate。

制作状态使用现有词汇，详细注明 NOT_STARTED、RENDER_FAILED、FILES_PRESENT、PREVIEW_NOT_ASSEMBLED 或 READY_FOR_REVIEW 的原因。图片/模块部分完成仍是 PARTIAL，不能只回“套图生成完成”。

缺 Claim/素材/授权时按受影响模块保留阻塞。可执行的已批准范围继续；未批准内容不能借“内部预览”变成正式事实。Publish BLOCKED 不自动等于 EBC 没生成，EBC 文件存在也不等于可发布。
