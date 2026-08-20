# Eufy Robot Vacuum Omni C28 — Reference Analysis

- ASIN: B0FX81HWQ3
- Source: https://www.amazon.co.jp/dp/B0FX81HWQ3
- Observed: 2026-08-18
- Category: ロボット掃除機
- Page type: Problem-solution / Performance-led / Scenario-led / Premium-brand-led
- Complexity: high

## Observation Boundary

- Desktop: Live Amazon.co.jp page inspected in Chrome at 1440 x 1000; 18 gallery items and 8 major A+ containers recorded.
- Mobile: The same live page inspected at a 390 x 844 browser viewport; Amazon retained a fixed desktop-width content region in this environment.
- The browser automation layer did not expose mobile user-agent switching; mobile findings describe a real 390px viewport, not Amazon m-site.
- Reference images and competitor copy are observation evidence only and are not packaged into the reusable Skill.

## Story Architecture

Problem-solution → Performance-led → Scenario-led → Premium-brand-led

Strengths:

- 页面一致性极高且AI设计感低
- 日本住宅适配在早期成为购买理由
- 主要机制按失败点拆分，一张一问
- Support、Privacy、Ecosystem形成购买信心闭环
- 明色体系仍能通过场景与技术切换形成节奏

Weaknesses:

- Gallery 18张不应成为默认长度
- A+多组同构轮播可能产生重复感
- 系列比较出现较早
- 最终规格模块缺少情绪性收束，390px viewport仍受Amazon固定宽影响

## Product Gallery

| # | Image Role | Consumer Question | Main Message | Layout | Product Scale | Text Density | Type | Why Effective |
|---:|---|---|---|---|---|---|---|---|
| 1 | Main image | ロボットとステーションの構成は何か | 白い本体とステーションをセットで提示 | Official system product on white | dominant | none | Product | 後続18枚の情報量に対して入口は極めて単純。 |
| 2 | Japan-fit hero | 日本の住まいに置けるサイズか | コンパクト設計を住空間と寸法で示す | Light room scene with dimension cue | large | low | Hero / Fit | 性能より先に日本市場の大きな購入障壁を解く。 |
| 3 | Lifestyle fit | インテリアに馴染むか | 白い住宅空間で静かな存在感を見せる | Full lifestyle with product | medium | low | Scenario / Brand | 設置寸法の理性判断から生活美観の情緒判断へ続く。 |
| 4 | Brand/category proof | ブランドの清掃製品を信頼できるか | カテゴリ実績と製品開発の文脈を提示 | Editorial brand proof | medium | medium | Proof / Brand | 機構説明前にブランドとしての購入安心を挟む。 |
| 5 | Mechanism overview | ローラーモップの強みは何か | 三つの理由へ圧縮して新方式を説明 | Three-reason technical composition | large | medium | Technical / Category Education | 複雑な仕組みを三つの購入理由へ整理している。 |
| 6 | Model comparison | シリーズのどのモデルが合うか | 製品差を早めに比較 | Light multi-column table | small | very_high | Comparison | 選択支援は明快だが、ストーリー途中では早く、文字も細かい。 |
| 7 | Problem-solution proof | 汚れた水を引きずらないか | 常にきれいな面で拭く仕組みを示す | Close-up mechanism with simple flow | large | medium | Technical / Problem-solution | 一枚に一つの失敗点だけを置き、因果が明快。 |
| 8 | Failure-point proof | 車輪が床を汚さないか | 走行部と清掃面の関係を説明 | Top-down path diagram | large | low | Technical / Proof | 購入者が想像しにくい二次汚れを可視化する。 |
| 9 | Surface result proof | 拭き跡は残らないか | 床面の仕上がりを見せる | Before-after floor close-up | medium | low | Performance / Proof | 内部機構から目で見える結果へ進む。 |
| 10 | Self-cleaning mechanism | 清掃中にモップが汚れ続けないか | 走行中の洗浄循環を図示 | Section diagram with fluid path | large | medium | Technical / Proof | 主要USPの信頼を異なる失敗点から積み重ねる。 |
| 11 | Carpet fit | カーペットを濡らさないか | 検知と持ち上げ動作を見せる | Split floor scenario | large | low | Scenario / Technical | 日本住宅で具体的な適合条件を一枚にする。 |
| 12 | Maintenance proof | 髪や毛が絡まないか | ブラシ構造で絡まり対策を説明 | Brush macro with hair flow | medium | medium | Technical / Benefit | 清掃性能から購入後メンテナンスへ自然に移る。 |
| 13 | Obstacle scenario | 家具や小物を避けられるか | 家の中の代表障害物を見せる | Realistic living room with detection cues | medium | low | Scenario / Technology | 技術を具体的な失敗回避場面へ翻訳する。 |
| 14 | Navigation proof | 効率よく部屋全体を回れるか | 地図と走行経路を簡潔に示す | Floor map with route overlay | small | medium | Technical / Proof | Obstacleシーンの後に経路全体の知能を説明する。 |
| 15 | Station confidence | 日々の手入れはどこまで自動か | 回収・洗浄・乾燥等の役割を整理 | Station hero with limited callouts | large | medium | Feature / Purchase Confidence | 多機能基站を少数のタスクへ整理し、ECOVACS型の過密を避けている。 |
| 16 | After-sales confidence | 故障や相談時の支援はあるか | 購入後サポートを明示 | Minimal support panel | medium | low | Trust / Closure | 性能では解消できない購入不安を独立して扱う。 |
| 17 | Privacy confidence | 地図や家庭データは安全か | データ保護方針を提示 | Security iconography with product | medium | medium | Trust / Technical | スマート家電固有の反対理由を購入前に表面化させる。 |
| 18 | Ecosystem closure | アプリやスマートホームと連携できるか | 操作エコシステムを最後に確認 | Product with verified control endpoints | medium | medium | Ecosystem / Closure | ページを使用後の操作全体像で閉じる。 |

## A+ Structure

| # | Module Type | Story Role | Layout | Message | Density | Product | Scene | Technical | Interaction | Rhythm Relation |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | Brand Story carousel | Anker ecosystem trust | Eight restrained brand cards | ブランドと製品群の信頼 | medium | medium | medium | low | carousel | 商品固有説明の前に企業・ブランド安心を作る。 |
| 2 | Premium carousel chapter | Category value and fit | Large light module with two cards | 日本住宅への適合と中心価値 | low | large | high | medium | carousel | ブランド導入から生活適合へ焦点を絞る。 |
| 3 | Premium carousel chapter | Mop mechanism | Four consistent light cards | ローラーモップの原理と結果 | medium | large | medium | high | carousel | Fitの後に主要USPを分解し、一枚一論点を守る。 |
| 4 | Premium carousel chapter | Suction and brush | Four consistent light cards | 吸引・ブラシ・床面対応 | medium | medium | medium | high | carousel | 拭き掃除から吸引性能へ機能章を移す。 |
| 5 | Premium carousel chapter | Maintenance and home fit | Six cards with product and home scenes | 基站手入れ・設置・日常運用 | medium | medium | high | medium | carousel | 性能理解の後に所有コストと生活適合へ進む。 |
| 6 | Premium carousel chapter | Confidence and operation | Five cards | 支援・プライバシー・操作 | medium | medium | medium | medium | carousel | 購入不安をまとめる終盤章。 |
| 7 | Comparison table | Model selection | Light multi-column comparison | シリーズ内の選択基準 | high | small | none | high | static table | 同じ明色基調のまま判断モードへ移る。 |
| 8 | Specification text | Condition closure | Restrained specifications | 仕様・条件・注意事項 | high | none | none | high | static text | 最後に必要条件を残すが、情緒的な締めは弱い。 |

## Visual Grammar

| Dimension | Observation |
|---|---|
| visual hierarchy | One large headline and one visual question per unit, supported by limited callouts. |
| information density | Low to medium despite a very long gallery. |
| image text ratio | Usually 70:30; technical units remain visually led. |
| whitespace | Consistently generous light gray and warm-white space. |
| full bleed usage | Selective; interiors and floor surfaces carry depth without heavy overlays. |
| card usage | A+ uses repeated premium carousel cards with strict internal consistency. |
| product scale | Large for fit and mechanism, medium for trust and scenario, small in maps/comparison. |
| typography hierarchy | Large concise headline, one supporting sentence, minimal labels. |
| dark light rhythm | Almost entirely light; rhythm comes from scene/diagram changes rather than color inversion. |
| scene technical rhythm | Fit scene, category proof, mechanism chain, scenario checks, confidence and ecosystem. |

## USE

- 先解决日本住宅适配，再进入性能
- 将一个大USP拆为多个具体失效问题逐一证明
- 在后半段独立处理Support、Privacy、同梱与Ecosystem
- 以稳定网格、留白和产品比例降低AI感

## ADAPT

- 将Anker/Eufy明灰Trade Dress转译为SwitchBot白、浅灰与薄荷品牌系统
- 保留一问一图的逻辑，但压缩到产品所需的7张Gallery
- A+不必复制轮播形式，只吸收章节顺序和密度控制

## AVOID

- 复制Anker/Eufy卡片造型、字体、色彩或完整布局
- 把18张Gallery当作数量目标
- 重复相同视觉结构导致长页面机械
- 在没有现行来源时复制隐私、支援或性能表述

## Good For

- 需要日本住宅适配和购买信心的智能家电
- 高复杂度但希望视觉保持清爽的产品
- 主要USP可以拆成多个问题—证据单元的页面
