# ECOVACS DEEBOT T80 OMNI — Reference Analysis

- ASIN: B0F66LKTV6
- Source: https://www.amazon.co.jp/dp/B0F66LKTV6
- Observed: 2026-08-18
- Category: ロボット掃除機
- Page type: Performance-led / Technology-led / Problem-solution / Feature-led
- Complexity: very_high

## Observation Boundary

- Desktop: Live Amazon.co.jp page inspected in Chrome at 1440 x 1000; 9 gallery items and 8 major A+ containers recorded.
- Mobile: The same live page inspected at a 390 x 844 browser viewport; Amazon retained a fixed desktop-width content region in this environment.
- The browser automation layer did not expose mobile user-agent switching; mobile findings describe a real 390px viewport, not Amazon m-site.
- Reference images and competitor copy are observation evidence only and are not packaged into the reusable Skill.

## Story Architecture

Performance-led → Technology-led → Problem-solution → Feature-led

Strengths:

- 机制解释紧贴用户痛点
- 从清洁核心到基站再到导航有完整技术链
- 性能数字与典型污物、墙角等场景连接
- 系列比较提供明确选择入口

Weaknesses:

- 信息密度长期处于高位
- 单张图多次出现功能清单和小字
- A+四组导航轮播的视觉变化不足
- 规格长文造成疲劳，390px viewport裁切风险明显

## Product Gallery

| # | Image Role | Consumer Question | Main Message | Layout | Product Scale | Text Density | Type | Why Effective |
|---:|---|---|---|---|---|---|---|---|
| 1 | Main image | 本体とステーションはどのような構成か | ロボットと大型ステーションをセットで提示 | Official system product on white | dominant | none | Product | 高複雑度な製品群を一つのシステムとして認識させる。 |
| 2 | Performance hero | 掃除性能の中心的な強みは何か | 清掃力の大幅向上を数値で訴求 | Large system render with performance numeral | large | medium | Hero / Performance | 複雑な機能群より先に一つの性能結論を置く。ただし倍率Claimは比較条件が必須。 |
| 3 | Problem-solution mechanism | 床をこする仕組みは何が違うか | ローラー式モップの接触と洗浄を説明 | Mechanism diagram with before-after logic | large | high | Technical / Problem-solution | ユーザーの不満である汚れ移りを機構で解く。 |
| 4 | Suction proof | ゴミをどこまで吸えるか | 吸引力とゴミ例を提示 | Performance numeral plus debris strip | medium | medium | Performance / Proof | 数値を実際のゴミ例に接続し、意味を補う。 |
| 5 | Coverage proof | 壁際や角まで掃除できるか | エッジへの接近動作を図示 | Top-down floor plan and close-up | medium | high | Technical / Scenario | 性能を部屋の境界という具体的な失敗点へ結びつける。 |
| 6 | Station inventory | ステーションは何を自動化するか | 多数の自動メンテナンス機能を一覧化 | Central station with many callouts | large | very_high | Feature / Detail | 網羅性は高いが、一枚の判断量を超えている。 |
| 7 | Smart operation | 操作を簡単にできるか | 音声・アプリ等の操作方法をまとめる | Lifestyle scene with interface callouts | medium | high | Scenario / Ecosystem | 清掃機構から日常の操作へ移り、利用の全体像を補う。 |
| 8 | Navigation proof | 障害物を避け、効率よく走れるか | 認識・経路・制御を一枚に統合 | Three-zone technical map | medium | very_high | Technical / Proof | 重要な不安を網羅する一方、認識・経路・アプリが競合している。 |
| 9 | Method comparison | 従来の回転モップより何が良いか | ローラーとパッド方式の違いを比較 | Side-by-side method comparison | medium | high | Comparison / Proof | 主要USPを競合方式との差へ戻して締める。 |

## A+ Structure

| # | Module Type | Story Role | Layout | Message | Density | Product | Scene | Technical | Interaction | Rhythm Relation |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | Brand Story carousel | Brand scale | Four large brand cards | ブランド・技術・製品群の信頼 | medium | medium | medium | low | carousel | 製品機構前にブランドの大きさを置く導入。 |
| 2 | Full-width hero | Performance reset | Dark full-bleed system hero | 清掃力と自動化の統合価値 | medium | dominant | low | medium | static | ブランド面から商品中心の暗色面へ強く転換する。 |
| 3 | Navigation carousel | Mop mechanism chapter | Blue-black tabs with mechanism cards | ローラー、洗浄、圧力、汚れ処理 | very_high | large | low | very_high | tabbed carousel | Heroの性能結論を最重要機構へ掘り下げる。 |
| 4 | Navigation carousel | Floor coverage chapter | Four technical cards | 壁際・段差・カーペット・持ち上げ | high | medium | medium | high | tabbed carousel | 機構から部屋内の失敗点へ視点を広げる。 |
| 5 | Navigation carousel | Station automation chapter | Multi-function station cards | ステーションの自動処理 | very_high | large | low | high | tabbed carousel | 床上性能から購入後の手入れ負担へ移る。 |
| 6 | Navigation carousel | Intelligence chapter | Map, recognition and app cards | 認識・経路・アプリ・連携 | very_high | medium | medium | very_high | tabbed carousel | 最後の技術章として操作と知能をまとめるが論点が多い。 |
| 7 | Comparison table | Model selection | Wide product comparison | シリーズ内の性能・機能差 | very_high | small | none | very_high | static table | 技術章を選択支援へ切り替える。 |
| 8 | Specification text | Condition closure | Long text and specifications | 仕様・条件・注意事項 | very_high | none | none | very_high | static text | 情報は網羅するが、最後の読後感は重い。 |

## Visual Grammar

| Dimension | Observation |
|---|---|
| visual hierarchy | Large numeric performance claims lead; mechanism diagrams and multi-callout panels follow. |
| information density | High to very high across most gallery and A+ units. |
| image text ratio | Roughly 50:50, often with text embedded inside diagrams. |
| whitespace | Low; panels prioritize coverage over breathing room. |
| full bleed usage | Frequent blue and dark technical fields. |
| card usage | Cards and callouts enumerate mechanisms and station functions. |
| product scale | Large for robot and station, medium inside navigation diagrams. |
| typography hierarchy | Large blue/white claim, several medium labels and many small annotations. |
| dark light rhythm | Dark hero and navigation bars alternate with pale technical panels, but density remains constant. |
| scene technical rhythm | Technical chapters dominate; lifestyle scenes are secondary proof contexts. |

## USE

- 把核心清洁问题拆成机制—性能—覆盖—维护链路
- 技术Claim后立即呈现失效场景或可见结果
- 复杂系统按核心机构、环境适配、自动维护、智能控制分章

## ADAPT

- 每个SwitchBot视觉单元只承担一个机制或一个Proof
- 将蓝黑重科技改为SwitchBot更清洁、友好的技术层
- 把10-in-1式清单拆成按消费者决策顺序的少量节点

## AVOID

- 复制ECOVACS蓝色Trade Dress或模块导航样式
- 用未经来源确认的倍数、大数字或对比结论
- 在图库或移动端塞入多列小字表
- 把所有功能放在一张中央放射图里

## Good For

- 清洁机制决定性能的复杂家电
- 需要解释机器人、基站和软件三层系统的产品
- 用户会比较清洁方式而不仅是功能数量的页面
