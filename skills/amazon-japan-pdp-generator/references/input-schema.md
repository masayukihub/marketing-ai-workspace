# PDP Input Schema

生成器读取一个 UTF-8 JSON。未知值使用空字符串或明确状态，不得伪造。

该 JSON 是 KNOW/PLAN 的 intake，不是下游页面数据源。KNOW 将其与 canonical facts 归一为 `PRODUCT_BRIEF.json`；REFERENCE 从 Brief 匹配设计决策知识；PLAN 再生成 `SELLING_POINT_MATRIX.json` 与唯一页面源 `PRODUCT_PAGE_SPEC.json`。DESIGN/PRODUCE 不得重新从本 intake 维护并行文案。

## Reference Matching Profile（可选）

`PRODUCT_BRIEF.json` 可显式包含以下非Claim字段。缺失时 Matcher 只使用 Brief 已有的 category、core value、core problem、objections、hero selling point 与 target audience；不会为了得到高分而补写事实。

```json
{
  "reference_profile": {
    "category": ["smart home"],
    "product_complexity": "high",
    "primary_usp": ["physical control"],
    "consumer_tension": ["too many remotes and apps"],
    "product_type": ["system product"],
    "story_requirement": ["Category-education", "Technology-led"],
    "technical_complexity": "high",
    "target_audience": ["Japanese household"]
  }
}
```

这些字段仅用于 Reference Matcher；不得覆盖 Product Truth、Claim 状态或来源记录。

## 顶层字段

```json
{
  "meta": {},
  "product": {},
  "journey": [],
  "facts": [],
  "claims": [],
  "strategy": {},
  "titles": {},
  "bullets": [],
  "images": [],
  "aplusModules": [],
  "comparison": {},
  "seo": [],
  "faq": [],
  "assets": [],
  "sources": [],
  "missingInformation": []
}
```

## 必填约束

- `meta.market`: `JP`；`meta.externalPublishReady`: boolean；`meta.moduleAvailability`: `Confirmed` 或 `Need Verification`。
- `product`: `brand`、`name`、`category`、`sku`、`mainImage`、`mainImageSource`、`mainImageOrigin`、`mainImageType`、`productBodyAiGenerated`。价格缺失时用占位符并标记状态；评分缺失时使用 `rating.status = unavailable`，不得填入测试数值。
- `journey`: 七个对象，`id` 按 `decision-journey.md` 固定顺序。
- `strategy.coreValue`: 单个字符串；`strategy.heroSellingPoint` 为单个对象；`coreSellingPoints` 最多 5 个。
- `titles`: `main`、`seo`、`concise`、`recommendedKey`、`keywordLogic`、`riskCheck`、`status`。
- `bullets`: 正好 5 个；每项有 `headline`、`body`、`stage`、`claimIds`、`status`。
- `images`: 正好 7 个；每项 `stage` 与所在顺序一一对应。
- `aplusModules`: 至少 1 个；默认 5–8 个实际 Module。全部 `units` 共同覆盖七阶段且首次出现顺序不倒退，但不得为了数量把每个 Unit 各自渲染为同规格 Banner。
- `comparison.rows`: 每个单元必须有 `status` 或来源可追溯。
- `seo`: 每行有 `category`、`keyword`、`priority`、`placement`、`status`。
- `faq`: 8–15 个；每项有 `question`、`answer`、`claimIds`、`status`。

## Image 对象

```json
{
  "id": "IMAGE-01",
  "stage": "understand_product",
  "role": "Product recognition",
  "userQuestion": "これは何？",
  "keyMessage": "販売内容を正確に示す",
  "headline": "",
  "subcopy": "",
  "supportingData": "",
  "visualDirection": "白背景に実際の同梱内容",
  "productPlacement": "中央、85%以上は当次ルール確認",
  "scene": "なし",
  "iconInfographic": "なし",
  "assetRequirement": "公式正面PNG",
  "designPriority": "SKU accuracy",
  "avoid": "文字、未同梱アクセサリー",
  "claimIds": [],
  "claimSource": "SRC-...",
  "risk": "Current category rule check",
  "status": "Need Design",
  "canvas": "2000x2000",
  "layoutId": "MAIN",
  "pageRole": "Product recognition",
  "copyOptions": [
    {"id": "A", "text": "...", "approach": "Benefit"},
    {"id": "B", "text": "...", "approach": "Functional"},
    {"id": "C", "text": "...", "approach": "Lifestyle"}
  ],
  "copySelected": "A",
  "proofItems": ["..."],
  "productSize": "large",
  "background": "#FFFFFF",
  "human": "No",
  "props": "None",
  "textSafeArea": "N/A",
  "mobileSafeArea": "N/A",
  "assetSource": "official",
  "productSource": "assets/user-provided-official-product.png",
  "sceneSource": "assets/ai-or-photo-background-without-product.jpg",
  "sourceOrigin": "User Provided Official",
  "sourceAssetType": "Official PNG",
  "productBodyAiGenerated": false,
  "aiGeneratedElements": ["background", "lighting", "composition expansion"],
  "retouchRequirement": "shadow cleanup only",
  "visualSrc": "assets/product.webp"
}
```

### 商品图视觉字段

- `layoutId`: `MAIN`、`A`、`B`、`C`、`D`、`E`、`F` 之一；详见 `visual-layout-system.md`。
- `copyOptions`: 除主图外必须有 A / B / C 三案；每案记录方向与日文。生成器记录评分和最终选择。
- `informationHierarchy`: 生成后必须包含 `level1`、`level2`、`level3`；Level 3 最多 4 项。
- `layerPlan`: 分开记录 Product、Scene、Graphic 三层。Scene 层缺失时可用 AI 生成不含产品的环境；Product 层绝不允许 AI。
- `wireframePath`、`round1Path`、`editablePath`、`finalPath`: 由生成器写回统一 JSON。

## A+ Module 与 Visual Unit

```json
{
  "id": "APLUS-M01",
  "sequence": 1,
  "templateType": "SB-A01",
  "moduleType": "Premium Full Background / account availability pending",
  "moduleAvailability": "Need Verification",
  "purpose": "Understand product and spark interest",
  "desktopLayout": "Full width",
  "mobileConsideration": "Headline under 20 JP characters",
  "imageRatio": "970:300",
  "copyLength": "H1 + 40–80 JP characters",
  "cta": "No CTA",
  "units": [
    {
      "id": "APLUS-U01",
      "stage": "understand_product",
      "purpose": "Category definition",
      "userQuestion": "何ができる？",
      "headline": "...",
      "copy": "...",
      "visual": "...",
      "asset": "...",
      "claimIds": ["CLM-..."],
      "claimSource": "SRC-...",
      "risk": "...",
      "status": "Need Verification",
      "productSource": "assets/user-provided-official-product.png",
      "sceneSource": "assets/ai-or-photo-background-without-product.jpg",
      "sourceOrigin": "User Provided Official",
      "sourceAssetType": "Official PNG",
      "productBodyAiGenerated": false,
      "aiGeneratedElements": ["scene", "people", "background"],
      "visualSrc": "assets/official-lifestyle.webp"
    }
  ]
}
```

## A+ Story 与模板约束

- `templateType` 必须是 `SB-A01`—`SB-A08`。旧输入 A–J 仅作为兼容别名，生成时转为新模板 ID。
- 一个 Module 输出一张最终 JPEG；`units` 是该 Module 内部的内容块，不是独立横 Banner。
- 每个 Unit 同样需要 A / B / C Headline 三案、信息层级、Product/Scene/Graphic 三层与 Claim 来源。
- `module.finalPath` 指向 `design/aplus/aplus_xx.jpg`；Unit 写入 `moduleFinalPath`。
- A+ 数量由购买故事决定，禁止用 “至少15张” 作为结构目标。

## 状态词表

内容/Claim：`Approved`、`Confirmed`、`Need Verification`、`Conflict`、`Unsupported`、`Internal Only`、`Prohibited`、`Not Available`、`Not Applicable`。

制作：`Source Ready`、`Need Cutout`、`Need Composition`、`Need Lifestyle Generation`、`Need Copy`、`Need Verification`、`Final Ready`、`Blocked`。旧输入中的 `Ready`、`Copy Ready`、`Asset Missing`、`Need Design` 继续兼容。

## Rating 与 Asset Provenance

可选评分对象：

```json
{"rating":{"value":null,"count":null,"source":null,"source_type":null,"status":"unavailable"}}
```

只有 `status` 为 `confirmed` / `approved` / `verified`、`source` 非空、`source_type` 为 `amazon_api` / `amazon_verified_snapshot` / `approved_marketplace_snapshot`、`value` 为 0–5 数字且评论数已确认时才可显示；否则消费者页面统一显示 `—`。自由文本 source、未知 source type 和 Fixture 不可显示。

每个 Resolver 记录必须输出：

```json
{
  "source_type": "official|user_supplied|generated_scene|placeholder|external_reference|unknown",
  "source_path": "",
  "verification_status": "verified|unverified|rejected",
  "product_layer_allowed": false,
  "resolved": false,
  "file_resolved": false,
  "source_verified": false,
  "usage_approved": false
}
```

`resolved`/`file_resolved` 只说明路径可访问；不得据此升级 `source_type`、`verification_status` 或 `usage_approved`。Product Layer 仅允许已验证、已批准且符合正式官方规则的 `official` 素材。`placeholder`、`external_reference`、`generated_scene`、`unknown` 永久禁止进入 Product Layer。

## 正式视觉素材硬门槛

- `sourceOrigin` 正式上线时必须是精确值 `User Provided Official`。官网下载素材只能作为研究或回归测试 Fixture，不能代替用户为正式项目提供的官方文件。
- `sourceAssetType` 只允许：`Official White Background`、`Official PNG`、`Official Render`、`Official Lifestyle`、`Official Installation`、`Official Detail`。
- `productBodyAiGenerated` 必须明确为 `false`。为 `true` 时结构校验直接失败；缺失或未知时 Publish Gate 必须 `Blocked`。
- `aiGeneratedElements` 只可包含 scene、people、background、lighting、props、composition expansion 等非产品元素。
- `productSource` 优先指向产品本体官方素材。`visualSrc` 可指向官方 Lifestyle 或已合成场景；两者都必须可追溯。
- 主图仍需重新完成白底、裁切、尺寸、居中、留白、清晰度与占比处理；不得原封不动复制源文件作为最终图。
- 产品轮廓、比例、颜色、材质、Logo、按钮、接口、屏幕、配件、安装结构、朝向与真实组合必须保持官方素材原貌，AI 不得补画或重设计。

生成器不把状态改成更乐观的值；审核人必须在源 JSON 中更新并重新生成全部产物。

## 阶段调用边界

- `--phase know`：要求 intake；只输出 Product Brief/理解审阅/状态。
- `--phase reference`：要求已完成 KNOW；输出 Top 3 Reference 与组合策略，不增加人工 Gate。
- `--phase plan`：要求已完成 KNOW、REFERENCE 与 intake；输出 Selling Matrix、Spec、Story Review。
- `--phase design`：读取落盘 Spec；要求 Story Approval。
- `--phase produce` / `--rerender`：读取落盘 Spec；要求 Layout Approval。
- `--from-spec <path>` 可显式选择 Spec；`--resume` 根据 `PROJECT_STATE.json` 选择下一个可执行阶段。
- `--force` 只添加风险覆盖，不把任何状态升级为外部批准。
