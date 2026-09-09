# 日亚 A+ 参考与本次验证边界

核对日期：2026-09-09。本文件仅记录本轮真实读取结果，不继承上一轮的抓取成功状态。证据为返回 HTML/DOM，不是截图、轮播交互、Amazon App 或 Seller Central 验证。CSS 存在某类名不等于页面使用该模块。

## 七个用户参考页

| ASIN | 本轮结果 | 用途 |
|---|---|---|
| B0FQ5J7HFQ | 访问失败 / DisabledError | 不推断本轮页面结构 |
| B0H3TK4HKW | 访问失败 / DisabledError | 不推断产品身份或模块 |
| B0FX7M29RP | 成功读取 HTML/DOM | 实际 premium-module-13-carousel 容器、premium-module-5-comparison-table-scroller 和 premium-module-15-text 容器；可确认轮播、比较表及原生文字需分别交付 |
| B0H8P9N9W7 | 访问失败 | 不声称本轮验证全部轮播页 |
| B0D7ZLPSJG | 访问失败 | 不推断本轮页面结构 |
| B0GK1QFGF6 | 成功读取 HTML/DOM | 已读取 A+ 区域及布局声明；未完成逐模块、逐 Slide 或移动 UA 视觉审计 |
| B0C6MK4LXR | 访问失败 / DisabledError | 不以其他站点冒充日亚证据 |

来源：

- https://www.amazon.co.jp/gp/product/B0FQ5J7HFQ
- https://www.amazon.co.jp/dp/B0H3TK4HKW
- https://www.amazon.co.jp/dp/B0FX7M29RP
- https://www.amazon.co.jp/dp/B0H8P9N9W7
- https://www.amazon.co.jp/dp/B0D7ZLPSJG
- https://www.amazon.co.jp/dp/B0GK1QFGF6
- https://www.amazon.co.jp/dp/B0C6MK4LXR
- https://sell.amazon.com/tools/a-content

## 对修复的影响

1. EBC 不是单张概念的九宫格。完整请求必须交接到主流程，并保留 A+ 的 required_outputs。
2. 一个 A+ Module 可以包含多个 Slide；每页图、移动呈现、文案和组件绑定分别核验。模块封面不能代替全部 Slide。
3. 比较表、FAQ、正文可能是原生字段；不能把它们全部强制转为一张横幅，也不能仅凭字段存在就声称已挂载。
4. 7 Modules / 16 Units 仅作为历史项目形状的回归样本，不是统一平台要求。具体模块和尺寸由已批准 Spec 与账户能力决定。
5. 本补丁复用现有 renderer，不创建新的 Premium Carousel 产品功能；新增的是路由、完整交付契约和文件检查。

## 本轮测试不是产品发布验证

`aplus_runtime_smoke.mjs` 使用无真实产品的合成数据，调用现有 reference renderer 实际写入桌面/移动 JPG，并验证 Gallery 字节未变、缺失 A+ 被发现、Publish 保持 BLOCKED。它不调用完整生产编排器，不测试真实 S30 素材、品牌效果、浏览器或 Seller Central。

产品事实、图片使用批准和 Story/Handoff 缺失必须如实报告；不能将技术样本的成功写为真实产品成片通过。不将竞品图片、原文、实时价格、账号数据或未发布产品资料提交到本补丁。
