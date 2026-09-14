# 日亚 A+ 参考与本次验证边界

以下第一部分记录 2026-09-09 的结构检查；2026-09-14 的像素观察补充在后。每次观察单独保留证据等级，不把历史访问成功当作当前页面已经验证。CSS 存在某类名不等于页面使用该模块。

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

## 2026-09-14：商业画面观察补充

实际重新读取 Eufy Omni C28（B0FX7M29RP）的页面 HTML，并查看此前取得的 7 张原始 A+ 图片。Soundcore（B0GK1QFGF6）证据为页面 HTML/DOM；其余 5 条实际页面仍无法读取。没有完成真实轮播交互或 Seller Central 验证，也不将 DOM-only 的内容列为视觉样本。

| 已看过的原图 | 观察到的画面原则 | 可转译的制作决定 |
|---|---|---|
| [主视觉](https://m.media-amazon.com/images/S/aplus-media-library-service-media/9e354796-bbf8-4d5e-b1c8-4d62e50d2f7e.__CR0,0,4392,1800_PT0_SX1464_V1___.png) | 产品是主角，短标题和次级信息配合主体 | 先决定产品镜头与比例，再排字 |
| [滚筒价值场景](https://m.media-amazon.com/images/S/aplus-media-library-service-media/b2d10428-b61e-4d26-b3cb-657c313dba95.__CR0,0,4392,1800_PT0_SX1464_V1___.png) | 清洁任务通过产品与地面作用关系表达 | 场景动作承担卖点证明，而非仅放一张家居背景 |
| [机理画面](https://m.media-amazon.com/images/S/aplus-media-library-service-media/c90e0140-ce77-45ac-9a50-cde943cddf80.__CR0,0,1464,600_PT0_SX1464_V1___.jpg) | 部件有统一透视，步骤靠近作用位置，过程分色 | 机理图需要可信部件/结构素材和连续阅读路径；不复制该产品内部结构 |
| [吸尘与刷头](https://m.media-amazon.com/images/S/aplus-media-library-service-media/228d5bc8-1c7b-4f42-b71f-7a108e1341df.__CR0,0,4392,1800_PT0_SX1464_V1___.png) | 大场景和局部细节共同解释作用 | A+ 用新增细节展开图库主题，不只换横版尺寸 |

这组图同时包含留白、场景和局部机理，并非统一的“强特效风格”。可学习的是按消费者问题选择画面类型，并让动作、材质与透视一致。克制的参考也不意味着每页必须相同白栏/卡片；更不能把“查看过轮播 DOM”写成“已获得其视觉语言”。

配套 [商业画面制作](commercial-visual-production.md) 将这些观察转化为 Handoff、代表图比较与能力记录。原图仅供参考，仓库不保存竞品图二进制、不迁移文案或产品主张。
