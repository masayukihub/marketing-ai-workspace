# 日亚 A+ 参考观察：用于交付模型，不复制成品

核对日期：2026-09-08。证据范围是本次能够读取的 Amazon.co.jp 返回 HTML/DOM，不是完整浏览器截图、实际轮播交互、Amazon App 或 Seller Central 验证。共享 CSS 中出现一个类名不能单独证明页面实际使用了模块。

## 本次七个 URL 的读取边界

| ASIN | 页面识别 / 读取情况 | 可用于本补丁的观察 |
|---|---|---|
| B0FQ5J7HFQ | Plaud Note Pro；读取到日亚页面 DOM | 存在实际结构化比较内容；比较表不能等同一张广告图 |
| B0H3TK4HKW | 未成功确认日亚 DOM | 不推断商品身份或 A+ 模块，不从第三方商品摘要补全 |
| B0FX7M29RP | Eufy Robot Vacuum Omni C28；读取到日亚页面 DOM | 存在实际比较表内容；内容应保留表格结构和型号边界 |
| B0H8P9N9W7 | SOUNDPEATS Air6 Pro；读取到日亚页面 DOM | 实际 premium-module-13-carousel 容器，5 个 Slide，独立图片 URL；观察到1464×600图像资源 |
| B0D7ZLPSJG | Soundcore Liberty 4 Pro；读取到日亚页面 DOM | 存在实际比较表字段及产品列，不能只有通用横幅 |
| B0GK1QFGF6 | Soundcore Liberty 5 Pro；读取到日亚页面 DOM | 存在实际比较内容；需独立比较组件/文案契约 |
| B0C6MK4LXR | 未成功确认日亚 DOM | 不以其他国家 Amazon 页面冒充日亚结构证据 |

Sources:

- https://www.amazon.co.jp/gp/product/B0FQ5J7HFQ
- https://www.amazon.co.jp/dp/B0H3TK4HKW
- https://www.amazon.co.jp/dp/B0FX7M29RP
- https://www.amazon.co.jp/dp/B0H8P9N9W7
- https://www.amazon.co.jp/dp/B0D7ZLPSJG
- https://www.amazon.co.jp/dp/B0GK1QFGF6
- https://www.amazon.co.jp/dp/B0C6MK4LXR

没有下载或提交这些品牌的图片、文案、用户评价、商标组合或页面源码；不将页面实时值写入 Product Truth。这里的产品名称仅用于识别参考页。

## 三条适用于生产契约的结论

1. A+ 是模块序列，不是单张创意的九宫格，也不是 Gallery 的宽屏复制。轮播模块还必须逐 Slide 生产和检查。
2. 文本/比较表/FAQ 可能是原生组件；图片、Native Copy、移动呈现、交互行为需要分别交付。
3. 参考数量和尺寸不是平台通用要求。保持已批准范围；具体 Basic/Premium 权限、模块名和图片规格必须核实本账户日本站 A+ Content Manager。

官方概念核对来源（Amazon 通用说明，不代替日本站账户实测）：

- https://sell.amazon.com/tools/a-content — 区分 Basic、Premium、Brand Story，说明图片/文字/比较表以及 Premium Carousel、Q&A 等能力。
- https://sell.amazon.com/blog/a-plus-content-design-guide — 图文分工、移动阅读与发布前预览建议。

## 不能由本次参考推导的结论

不能说七个页面均已完整视觉审计；不能说自己的账户有 Premium；不能将所有 A+ 定为1464×600、7个模块或16个单元；不能声称本补丁实现了一个新的 Premium Carousel Renderer。
