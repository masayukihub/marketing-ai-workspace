# Soundcore Soundcore Liberty 5 Pro — Reference Analysis

- ASIN: B0GK1QFGF6
- Source: https://www.amazon.co.jp/dp/B0GK1QFGF6
- Observed: 2026-08-18
- Category: 完全ワイヤレスイヤホン
- Page type: Technology-led / Performance-led / Premium-brand-led / Feature-led
- Complexity: high

## Observation Boundary

- Desktop: Live Amazon.co.jp page inspected in Chrome at 1440 x 1000; 11 gallery items and 8 major A+ containers recorded.
- Mobile: The same live page inspected at a 390 x 844 browser viewport; Amazon retained a fixed desktop-width content region in this environment.
- The browser automation layer did not expose mobile user-agent switching; mobile findings describe a real 390px viewport, not Amazon m-site.
- Reference images and competitor copy are observation evidence only and are not packaged into the reusable Skill.

## Story Architecture

Technology-led → Performance-led → Premium-brand-led → Feature-led

Strengths:

- 核心性能有明确技术解释
- 产品比例稳定且上位感清晰
- Comparison与FAQ形成购买闭环
- 技术章节的A+导航逻辑一致

Weaknesses:

- 整体暗色占比过高
- 后半图库文字密度过大
- 受赏与规格标签存在堆叠感
- 390px viewport下固定宽内容产生裁切风险

## Product Gallery

| # | Image Role | Consumer Question | Main Message | Layout | Product Scale | Text Density | Type | Why Effective |
|---:|---|---|---|---|---|---|---|---|
| 1 | Main image | 何の商品で、形状と同梱ケースはどう見えるか | イヤホン本体と充電ケースを明快に提示 | Official product on white | dominant | none | Product | 最初に商品認識だけへ集中し、後続の高密度な技術説明との入口を分離している。 |
| 2 | Value hero | この上位モデルは何が特別か | 静寂・音質・通話をProとして束ねる | Dark hero with large product and three proof labels | large | medium | Hero / Feature | 製品を大きく見せつつ三つの価値軸へ圧縮し、価格帯の理由を早期に作る。 |
| 3 | Technology explanation | ノイズ低減は何で実現するか | 専用チップを中心に処理構造を説明 | Centered product with chip callout | large | medium | Technical / Proof | 抽象的なANCをチップという具体物へ置き換え、信頼の足場を作る。 |
| 4 | Performance proof | 実環境でどこまでノイズを抑えられるか | 環境別の低減性能を図で示す | Performance chart plus product | medium | high | Technical / Proof | 性能を視覚化し、上位モデルの差を感覚ではなく比較可能な情報にする。 |
| 5 | Mechanism proof | 通話品質はなぜ安定するか | マイク構造とノイズ処理の仕組みを分解 | Cutaway diagram with callouts | large | high | Technical / Proof | 内部構造を見せ、目に見えない通話性能へ理由を与える。 |
| 6 | Audio proof | 音質の違いは何で生まれるか | ドライバー構成と対応規格を提示 | Exploded product and specification labels | large | high | Technical / Detail | オーディオ購入者が比較に使う技術語を一枚に集約している。 |
| 7 | Lifestyle proof | 音の広がりは日常でどう感じるか | 没入感を人物シーンへ翻訳 | Lifestyle full bleed with restrained overlay | small | low | Scenario / Benefit | 連続する技術説明の後に人物を入れ、感情的な呼吸を作る。 |
| 8 | Convenience cluster | 毎日の使いやすさはどうか | 外音・ケース・電池の補助価値を整理 | Three-zone feature composition | medium | high | Feature / Detail | 主性能の説明後に日常性を補完し、比較検討の抜けを減らす。 |
| 9 | Comparison | シリーズ内でどれを選ぶべきか | モデル差を表で提示 | Multi-column comparison table | small | very_high | Comparison | 購入直前の選択を支援する一方、ギャラリーでは文字が小さくなりやすい。 |
| 10 | Narrative detail | 自分向けの音へ調整できるか | パーソナライズ機能を長文で説明 | Editorial long-form panel | medium | very_high | Technology / Detail | 検討深度の高い購入者には有効だが、一覧性は弱い。 |
| 11 | Purchase confidence | 第三者評価と購入後の安心はあるか | 受賞・保証情報で締める | Badge row plus product/support copy | medium | high | Proof / Closure | 技術説明の最後を信頼要素で閉じるが、バッジ量は過剰になりやすい。 |

## A+ Structure

| # | Module Type | Story Role | Layout | Message | Density | Product | Scene | Technical | Interaction | Rhythm Relation |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | Brand Story carousel | Brand credibility | Horizontal card carousel | ブランド背景・受賞・シリーズ文脈 | high | medium | medium | low | carousel | 商品固有の説明前にブランド権威を置く導入。 |
| 2 | Full-width hero | Value reset | Full-bleed dark image | Proモデルの中心価値を再提示 | medium | dominant | none | low | static | ブランド導入を商品中心の強い暗色面へ切り替える。 |
| 3 | Bento proof block | Core technology proof | Large lead tile with smaller supporting tiles | 主要技術と性能の全体像 | high | large | low | high | static | Heroの抽象価値を複数の具体的根拠へ展開する。 |
| 4 | Navigation carousel | Noise control chapter | Dark chapter header plus selectable cards | ANC・外音・接続・ケース操作 | high | medium | low | high | tabbed carousel | 機能群を一つの操作テーマにまとめ、縦長化を抑える。 |
| 5 | Navigation carousel | Audio chapter | Dark chapter header plus selectable cards | 音質・規格・個人最適化・電池 | high | medium | low | high | tabbed carousel | 同じ器を反復し、読む規則は保つが視覚変化は小さい。 |
| 6 | Navigation carousel | Everyday use chapter | Dark chapter header plus selectable cards | 通話・防水・同梱物 | high | medium | medium | medium | tabbed carousel | 技術中心から利用・購入条件へ移行する橋渡し。 |
| 7 | Comparison table | Selection aid | Light multi-column table | シリーズ内の選択基準 | very_high | small | none | high | static table | 暗色の技術面から白背景へ切り替え、判断モードへ移る。 |
| 8 | FAQ | Objection closure | Light stacked question rows | 互換・使用・購入前の疑問 | medium | none | none | medium | accordion-like static rows | 比較後に残る不安を短いQ&Aで閉じる。 |

## Visual Grammar

| Dimension | Observation |
|---|---|
| visual hierarchy | Large product render first, oversized short headline second, then proof labels and conditions. |
| information density | High to very high after the second gallery image. |
| image text ratio | About 55:45 in technical units; lifestyle unit shifts toward image. |
| whitespace | Limited inside proof panels; greater in the main image and lifestyle break. |
| full bleed usage | Frequent dark full-bleed fields in both gallery and A+. |
| card usage | Proof cards and A+ navigation cards organize dense specifications. |
| product scale | Usually large or dominant; small only in comparison. |
| typography hierarchy | Large white headline, medium proof title, small conditions; hierarchy is clear but lower tiers can become tiny. |
| dark light rhythm | Predominantly dark; comparison and FAQ create the late light break. |
| scene technical rhythm | Several technical units, one lifestyle pause, then utility and confidence. |

## USE

- 用一张Hero把多个功能压缩成一个上位价值
- 核心Claim之后立即给机制或性能证据
- 用Comparison与FAQ完成选择和疑虑消除

## ADAPT

- 把黑色硬核科技感改为SwitchBot清洁、友好、带温度的技术表达
- 所有日文与图表文字改为程序化Graphic Layer
- 每个技术单元只保留一个主机制和必要条件

## AVOID

- 复制Soundcore黑色Trade Dress
- 把受赏Logo做成壁纸
- 在单张图库中塞入长段落或完整比较表
- 直接使用竞品文案、图片或页面布局

## Good For

- 需要解释不可见技术的高复杂度电子产品
- 性能差异是溢价核心的产品
- 需要强技术信任与系列比较的页面
