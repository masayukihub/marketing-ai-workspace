# GTM策略决策接入审阅记录

日期：2026-09-08。基线：`cf7c9996c86f44057a88006830422d30e7038c78`。本次是仓库实现候选，不是正式Skill发布或项目策略批准。

## 改动与使用

保留四个入口；新品GTM/实质策略变更通过 `$switchbot-japan-campaign` 的 PLAN 调用内部策略模块。先完整度地图，后候选比较、证据、反证和验证动作，停在现有 `STRATEGY_SCOPE_GATE`。完整协议见 [GTM策略契约](../../skills/switchbot-japan-campaign/references/gtm-strategy.md)。

- 新增三种思想标签及F11/F12/F13方法引用；不把方法当项目证据。
- 关键依赖缺失、不匹配、来源冲突或过期均不能靠自填High放行。
- Campaign Context增量引用唯一决策包；四类Brief继承准确版本，不能静默重新定位。
- 产品事实、Claim、预算、商业、素材、制作和发布审批保持独立。
- 历史活动/局部改稿保持原流程，不强制迁移或补齐十四问。

可用自然语言请求：

> 解析当前项目。使用日本营销活动策划与复盘的PLAN模式，先输出GTM答案完整度地图，比较受众/场景/价值候选，列明证据、放弃项和反证。已有策略只做增量检查，停在Strategy Review Gate，不生成渠道执行计划。

## 行为验证

Campaign 53项测试通过（含既有契约测试）；另有独立只读forward-test。新增回归覆盖：

- 无来源自填High、核心问题未知、未知保留完整十四问；
- 日本/中国市场、不同产品变体、过期/未来来源、单一或重复来源、未解决反证；
- 产品事实与市场FACT分域，缺少产品批准不能当作RTB；
- 完整度通过不自动批准；只读main接受记录而非本地修改；
- 次日人工接受可正确渲染；实际输出/Brief依赖的非核心证据过期也阻断；
- 四渠道同策略、错误版本/范围/hash/事实漂移阻断；
- assertions不得绕过声明依赖，Brief ID不能缺失；
- 选择理由及反证变化必须换版本并列出受影响决策；
- baseline不覆盖，局部修改/旧项目不重跑全部问卷。

独立验证发现的跨日接受、非核心证据到期、市场FACT误分类、理由变化漏追踪、未声明assertion依赖及Brief ID缺失，均已修正并加入回归。

工作空间验证、原有Skill回归（含视觉、Product Knowledge、Resolver、Project Memory、Campaign Review、VOC、EDM、Amazon Node和Ruby语法）、Runtime Lock、Skill Inventory与ChatGPT Context一致性均须在合入前通过。脚本结构校验不等于来源语义、样本代表性、商业效果、审批身份或浏览器渲染已验证。

## S30内部试跑

在最新main上重跑Resolver并读取可用正式来源及freshness依据：state_as_of为2026-08-20，当前stale；Product Truth/Approved Claim指针为空，受众、定位、USP未确认；已有Accepted Decision仅限视觉规划。

因此实跑输出14个Unknown、0个One Pager可进入项、策略Red；One Pager Deferred，Channel Plan不生成。空间/维护两条研究方向明确标为New Hypothesis，均暂不选。补证任务按P0/P1/P2列出，未指定Owner保留Unassigned。

该结果只说明当前正式仓库缺少可用于本次验证的来源链，不证明现实中没有资料或审批。试跑原始输入与产物保存在仓库外，未写正式Project Memory、Decision、Manifest或飞书，也未使用历史聊天填充事实。

## 合入与回退

- 保持PR供人工审核，不自动合并。此候选没有安装/同步全局Skill镜像。
- 合入后由clean main执行原有Runtime校验与单向镜像同步流程；这属于后续正式启用，不在本次自动执行范围。
- 回退使用审核后的反向提交；不存在数据库迁移、批量旧项目重写或生产资源变更。
