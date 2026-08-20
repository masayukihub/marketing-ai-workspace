# Levoit Core P350 Pet Air Purifier — Reference Analysis

- ASIN: B08131HFSG
- Source: https://www.amazon.co.jp/dp/B08131HFSG
- Observed: 2026-08-18
- Category: ペット向け空気清浄機
- Page type: Problem-solution / Category-education / Scenario-led
- Complexity: medium

## Observation Boundary

- Desktop: Live Amazon.co.jp page inspected in Chrome at 1440 x 1000; 8 gallery items and 8 major A+ containers recorded.
- Mobile: The same live page inspected at a 390 x 844 browser viewport; Amazon retained a fixed desktop-width content region in this environment.
- The browser automation layer did not expose mobile user-agent switching; mobile findings describe a real 390px viewport, not Amazon m-site.
- Reference images and competitor copy are observation evidence only and are not packaged into the reusable Skill.

## Story Architecture

Problem-solution → Category-education → Scenario-led

Strengths:

- 受众聚焦明确，页面持续围绕宠物家庭
- 问题教育、技术证明和生活缓解交替自然
- 浅色与留白降低技术信息压力
- 最后以场景和比较分别完成情绪与理性闭环

Weaknesses:

- 临床感数字与图示需要严格Claim来源
- 部分插画容易显得儿童化
- 品牌Story卡片过长
- 390px viewport下固定宽A+仍有裁切风险

## Product Gallery

| # | Image Role | Consumer Question | Main Message | Layout | Product Scale | Text Density | Type | Why Effective |
|---:|---|---|---|---|---|---|---|---|
| 1 | Main image | どんな空気清浄機か | 本体形状を白背景で明快に提示 | Official product on white | dominant | none | Product | 優しい後続ストーリーの前に商品そのものを中立に見せる。 |
| 2 | Proof hero | ペット環境の粒子を本当に捕集できるか | フィルター性能をラボ調で提示 | Product plus filter layers and proof numeral | large | high | Technical / Proof | ペット向けという情緒的ポジションを測定可能な性能で支える。 |
| 3 | Category education | ペットのいる家で何が問題になるか | 毛・におい・空気循環を一つの生活課題として説明 | Friendly scenario diagram | medium | medium | Category Education / Problem-solution | 専門用語ではなくペット家庭の課題からカテゴリ価値を理解させる。 |
| 4 | Night scenario | 寝室で音や光が気にならないか | 静音と睡眠場面を提示 | Full lifestyle bedroom with product | medium | low | Scenario / Benefit | ラボ調の証明から静かな生活場面へ自然に切り替える。 |
| 5 | Daily confidence cluster | 子どもやペットがいる日常で扱いやすいか | タイマー・ロック等の生活機能をまとめる | Three-scene feature strip | medium | medium | Scenario / Feature | 対象家族の細かな不安を生活文脈で整理する。 |
| 6 | Mechanism detail | ペットの毛に対応するフィルター構造か | 吸気とフィルター層を説明 | Exploded filter diagram | large | high | Technical / Detail | Lifestyleだけで終わらず、対象課題を解く内部構造へ戻る。 |
| 7 | Problem education | アレルギーやほこりの原因は何か | 目に見えにくい粒子の問題を説明 | Problem diagram with household cues | small | high | Category Education / Problem-solution | 商品説明ではなく問題認識を深め、購入理由を補強する。 |
| 8 | Emotional closure | 自宅で邪魔にならずペットと暮らせるか | ペットとの安心した暮らしと設置感を見せる | Full lifestyle with size cue | medium | low | Scenario / Closure | 最後を仕様ではなく対象ユーザーの望む暮らしで閉じる。 |

## A+ Structure

| # | Module Type | Story Role | Layout | Message | Density | Product | Scene | Technical | Interaction | Rhythm Relation |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | Brand Story carousel | Brand and lineup orientation | Long horizontal card carousel | ブランド、製品群、生活価値 | high | medium | high | low | carousel | 商品説明前に生活ブランドの文脈を作る。 |
| 2 | Full-width lifestyle hero | Audience identification | Pet lifestyle full bleed | ペット家庭向けの中心価値 | low | medium | high | none | static | ブランド面から対象ユーザーの情緒へ焦点を絞る。 |
| 3 | Full-width technical visual | Purification mechanism | Filter flow full bleed | 空気を取り込み浄化する仕組み | medium | large | low | high | static | 情緒Hero直後に製品が機能する理由を示す。 |
| 4 | Full-width problem visual | Odor problem-solution | Home problem scene with simple explanation | ペット臭の課題と対処 | medium | medium | high | medium | static | 機構を生活上の具体的な困りごとへ戻す。 |
| 5 | Carousel | Allergy and particle education | Two educational cards | 粒子・アレルゲンの背景 | medium | small | medium | medium | carousel | 問題を深掘りするが、二枚に限定して読みやすい。 |
| 6 | Full-width night visual | Quiet-use benefit | Dark bedroom full bleed | 睡眠時の静かな運転 | low | medium | high | low | static | 教育情報の後に暗色の静かな休止面を作る。 |
| 7 | Carousel | Daily fit | Three lifestyle cards | 日常の置き方と操作 | medium | medium | high | low | carousel | 購入前に複数の生活場面を確認させる。 |
| 8 | Comparison table | Selection closure | Light lineup comparison | 対象面積・機能・用途の違い | high | small | none | high | static table | 情緒的な生活ページを実用的な選択支援で閉じる。 |

## Visual Grammar

| Dimension | Observation |
|---|---|
| visual hierarchy | Audience problem and benefit lead; technical proof is framed as reassurance rather than spectacle. |
| information density | Mostly medium, with concentrated high-density filter and particle units. |
| image text ratio | About 70:30 in lifestyle and 50:50 in educational units. |
| whitespace | Generous cream and mint breathing room. |
| full bleed usage | Used for pet lifestyle, odor and night scenes to create emotional chapters. |
| card usage | Limited, primarily for education and daily-fit carousels. |
| product scale | Dominant in technical proof, medium in lifestyle, small in problem education. |
| typography hierarchy | Friendly rounded headline with short explanatory copy; fine print appears around proof claims. |
| dark light rhythm | Predominantly light with one dark bedroom interval. |
| scene technical rhythm | Lifestyle identification, mechanism proof, problem education, lifestyle relief, comparison. |

## USE

- 用具体人群问题建立Category Education
- Proof之后立即给生活结果，避免只讲过滤结构
- 通过单个暗色情境改变长页面节奏
- 最后回到目标用户想要的生活状态

## ADAPT

- 按产品类别调整插画程度，SwitchBot保持Clean、Smart、Friendly
- 临床或百分比信息必须有Claim ID和条件
- 将宠物友好配色方法转译为SwitchBot薄荷色而非复制Levoit视觉

## AVOID

- 复制Levoit薄荷宠物Trade Dress或卡通资产
- 把未核验的健康、过敏或除菌表达写成事实
- 使用无法在390px阅读的脚注
- 将情绪场景当作性能证据

## Good For

- 需要先教育问题再解释产品的家居品类
- 针对特定人群或家庭情境的产品
- 技术复杂度中等但信任和生活适配重要的页面
