# 成图质量诊断与改进

本次审查针对 marketing-ai-workspace 的内容入口和两个 Amazon 兼容模块。基础版本为 `cf7c9996c86f44057a88006830422d30e7038c78`。尚未取得用户不满意的成图、对应 Prompt 和实际运行记录，所以以下是可复核的流程/代码缺陷，不能认定某次 ChatGPT 生成一定走了这些分支。

## 发现的问题与本次修复

| 问题 | 原代码/规则中的证据 | 本次改动 |
|---|---|---|
| 没看图片就给出好评 | `visual_quality_system.mjs` 的 Brand Fit 和 Template Feeling 只根据 ON/OFF 返回固定分数/风险；`art_direction_system.mjs` 给出固定的品牌、真实感和基线分 | 未评估值用 null / NOT_ASSESSED；只保留真实语义与计划元数据检查 |
| 技术检查被当成设计通过 | 旧 `visual_pipeline.mjs::finalAudit` 检查文字长度、模板 ID 等，并把标题复制为“5 秒信息”；满足来源/Claim 后可进入 Final Ready | 元数据检查和实际成图观察分开；未观察、记录不完整或文件已改变时保持待审 |
| 参考方向没有完整落到渲染 | V4 的 `visualQualitySvg \|\| referenceRender.svg` 优先使用质量预设，即使已存在注册参考 Renderer；手机端也优先预设 | 注册参考 Renderer 在桌面与手机均优先；其他模板仍可使用质量预设。没有新增/重排模板或资产 |
| 从策略到镜头缺少执行交接 | 主入口有分层政策与 Asset Packet，但未规定具体镜头、接触面、光向、证明对象和工具调用记录 | 加入单张 Shot Brief、制作模式、窄场景 Prompt 编译器及实际工具交接规则 |
| 默认过度发散，已有图组容易被固定九图结构牵引 | Creative 模块默认 10 方向、Top 3、9 图；内容入口探索契约也固定 9/10 | 默认先完成一个候选；有实质分歧才增加对照；明确的九宫格请求保留，已批准集合不变 |
| 节奏检测误报高密度 | `longestRun` 把连续非 high 的 reset 也当作高密度长串 | 只统计连续 high，低密度会真正重置计数 |

这些变化能减少模板覆盖、提示词失焦和“假通过”。它们不会自动把普通素材变成高质量摄影；官方产品机位、场景制作能力和对真实图片的观察仍决定结果。

## 参考了什么

参考 [heymio/amazon-japan-creative-workflow](https://github.com/heymio/amazon-japan-creative-workflow/tree/271401d040a172ad140f02cbde193220269db098) 的 creative-production 和 creative-quality 方法；本次固定版本为 `271401d040a172ad140f02cbde193220269db098`。没有复制其实现或引入另一套项目状态。

| 参考方法 | 对应到本仓库 |
|---|---|
| 当前资产、购买任务、主信息和证明对象先明确 | 内容入口的 Shot Brief |
| 制作方式独立于模型供应商，缩小 Prompt 上下文 | 分层制作包；场景请求不携带产品素材、正文、全量研究和 Gate |
| 一个候选，观察后有限次定向修复 | 单张生产与局部修改，默认最多两轮针对同一问题修复 |
| 单图与整组分开看，定位具体缺陷 | 当前文件观察、Contact Sheet、受影响/保留资产记录 |
| 精确输出变更后审核需要重做 | 兼容层绑定 Asset ID、输出路径和 SHA-256；模型观察不自动升级成人工批准 |

## 日常怎么用

继续使用 `$jp-commerce-content-flow`，不需要切换多个 Skill。修图时给出：

```text
项目/Asset ID：
当前不满意的成图：
我认可的参考图：
具体哪里不满意：
已批准且必须保留的内容：
可用官方产品素材：

请先查看两张实际图片，定位最影响效果的问题。
按现有 Flow 为当前资产做一版局部修复，实际出图后再评审。
```

没有旧图时先做可执行 Brief，不假定用户不满意的是某种风格。认可的参考图用来讨论构图、焦点、材质和氛围，不复制其产品、文案或完整设计。

脚本示例：

```bash
python skills/jp-commerce-content-flow/scripts/prepare_creative_brief.py brief.json
node --test skills/amazon-japan-pdp-generator/tests/creative_quality_regression.mjs
python -m unittest discover -s skills/jp-commerce-content-flow/tests -p 'test_*.py' -v
```

Brief 编译器不调用图像模型。生产时由当前运行时/Agent 调用可用工具，再合成官方产品、真实 UI 和日文文字。实际审核记录格式见 [creative-review-record.md](../../skills/amazon-japan-pdp-generator/references/creative-review-record.md)。

## 验证与生效边界

回归覆盖固定美学分消除、密度误报、参考构图优先级、来源/Proof/UI 缺口、Prompt 上下文隔离，以及真实合成文件的“待审→记录审核→源图改变后失效”。合成测试没有用户产品事实，观察记录仅为测试夹具，不构成美学效果验证。

真实效果验收还需要同一产品、同一信息点的旧成图、目标参考与新成图，逐项比较信息焦点、产品真实性、构图、品牌气质和手机阅读。不能仅凭新规则或测试通过宣称“图片更好看”。

提交 PR 不会立即改变 ChatGPT 中已安装的 Skill，也不会更新另一个仓库的运行时。合并稳定 main 后，按仓库现有同步流程更新 Codex 镜像/个人 Skill，再重新开始该内容任务。不要用未合并分支覆盖正式安装。
